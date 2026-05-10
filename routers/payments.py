from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
import os

from services.midtrans_service import create_snap_transaction
from services.midtrans_signature import verify_signature
from services.supabase_service import (
    insert_order,
    update_order_status,
    update_order_payment_url,
    get_order_by_midtrans_id,
    insert_payment,
    update_payment_status,
    update_prospek_status
)
from services.fonnte_service import (
    kirim_invoice,
    kirim_konfirmasi_dp,
    kirim_notif_pembayaran_gagal
)

router = APIRouter(prefix="/payments", tags=["payments"])

MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY", "")


# =============================================
# SCHEMAS
# =============================================

class CustomerSchema(BaseModel):
    nama: str
    nomor_wa: str
    email: Optional[str] = ""

class ItemSchema(BaseModel):
    id: str
    price: int
    quantity: int
    name: str

class InvoiceRequest(BaseModel):
    prospek_id: int
    order_id: str           # uuid dari tabel orders
    paket: str
    tanggal_acara: str
    jumlah_kambing: int
    total_harga: int
    alamat: Optional[str] = ""
    catatan: Optional[str] = ""
    customer: CustomerSchema
    items: List[ItemSchema]


# =============================================
# ENDPOINTS
# =============================================

@router.post("/create-invoice")
async def create_invoice(data: InvoiceRequest):
    """
    Buat invoice + payment link Midtrans, kirim ke WA klien.
    Dipanggil oleh Delisa setelah klien setuju dengan pesanan.
    """
    dp_amount = int(data.total_harga * 0.5)

    items_payload = [
        {
            "id": item.id,
            "price": int(item.price * 0.5),
            "quantity": item.quantity,
            "name": f"[DP] {item.name}"
        }
        for item in data.items
    ]

    # 1. Buat transaksi Midtrans
    try:
        token, payment_url = create_snap_transaction(
            order_id=data.order_id,
            amount=dp_amount,
            customer={
                "name": data.customer.nama,
                "email": data.customer.email,
                "phone": data.customer.nomor_wa
            },
            items=items_payload
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Midtrans error: {str(e)}")

    # 2. Simpan payment_url ke Supabase, update status -> invoiced
    update_order_payment_url(
        order_id=data.order_id,
        payment_url=payment_url,
        midtrans_order_id=data.order_id
    )

    # 3. Kirim invoice + payment link via WhatsApp
    try:
        await kirim_invoice(
            nomor_wa=data.customer.nomor_wa,
            nama_pelanggan=data.customer.nama,
            paket=data.paket,
            tanggal_acara=data.tanggal_acara,
            jumlah_kambing=data.jumlah_kambing,
            total_harga=data.total_harga,
            dp_amount=dp_amount,
            payment_url=payment_url,
            order_id=data.order_id
        )
    except Exception as e:
        print(f"[WARNING] Gagal kirim WA invoice: {str(e)}")

    return {
        "order_id": data.order_id,
        "dp_amount": dp_amount,
        "payment_url": payment_url,
        "token": token,
        "status": "invoiced"
    }


@router.post("/webhook")
async def midtrans_webhook(request: Request):
    """
    Terima callback dari Midtrans.
    Otomatis update Supabase + kirim notif WA ke klien.
    """
    body = await request.json()

    order_id           = body.get("order_id")
    status_code        = body.get("status_code")
    gross_amount       = body.get("gross_amount")
    signature_key      = body.get("signature_key")
    transaction_status = body.get("transaction_status")
    fraud_status       = body.get("fraud_status", "")
    payment_type       = body.get("payment_type", "")
    transaction_id     = body.get("transaction_id", "")

    # 1. Validasi signature Midtrans
    is_valid = verify_signature(
        order_id, status_code, gross_amount,
        MIDTRANS_SERVER_KEY, signature_key
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 2. Ambil data order dari Supabase
    order = get_order_by_midtrans_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order tidak ditemukan: {order_id}")

    # 3. DP LUNAS
    if transaction_status == "settlement" or (
        transaction_status == "capture" and fraud_status == "accept"
    ):
        update_order_status(order["id"], "dp_paid")

        if order.get("prospek_id"):
            update_prospek_status(order["prospek_id"], "order")

        insert_payment(
            order_id=order["id"],
            tipe="dp",
            jumlah=int(float(gross_amount)),
            metode=payment_type,
            midtrans_transaction_id=transaction_id,
            midtrans_status=transaction_status,
            payload=body
        )

        try:
            await kirim_konfirmasi_dp(
                nomor_wa=order["nomor_wa"],
                nama_pelanggan=order["nama_pelanggan"],
                paket=order["paket"],
                tanggal_acara=str(order["tanggal_acara"]),
                dp_amount=order["dp_amount"],
                sisa_amount=order["sisa_amount"],
                order_id=order["id"]
            )
        except Exception as e:
            print(f"[WARNING] Gagal kirim WA konfirmasi DP: {str(e)}")

        print(f"[WEBHOOK] DP lunas: {order_id}")

    # 4. PEMBAYARAN GAGAL / EXPIRED / DIBATALKAN
    elif transaction_status in ["cancel", "deny", "expire"]:
        update_order_status(order["id"], "payment_failed")
        update_payment_status(order["id"], "failed", payload=body)

        try:
            await kirim_notif_pembayaran_gagal(
                nomor_wa=order["nomor_wa"],
                nama_pelanggan=order["nama_pelanggan"],
                payment_url=order.get("payment_url", "")
            )
        except Exception as e:
            print(f"[WARNING] Gagal kirim WA notif gagal: {str(e)}")

        print(f"[WEBHOOK] Pembayaran gagal: {order_id} - {transaction_status}")

    return {"status": "ok"}
