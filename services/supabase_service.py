import os
from supabase import create_client, Client
from datetime import datetime
from typing import Optional

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# =============================================
# ORDERS
# =============================================

def insert_order(
    prospek_id: int,
    nama_pelanggan: str,
    nomor_wa: str,
    paket: str,
    tanggal_acara: str,
    total_harga: int,
    alamat: str = "",
    jumlah_kambing: int = 1,
    catatan: str = "",
    midtrans_order_id: str = "",
    payment_url: str = ""
) -> dict:
    """Insert pesanan baru setelah DP lunas."""
    dp_amount = int(total_harga * 0.5)
    sisa_amount = total_harga - dp_amount

    data = {
        "prospek_id": prospek_id,
        "nama_pelanggan": nama_pelanggan,
        "nomor_wa": nomor_wa,
        "alamat": alamat,
        "paket": paket,
        "tanggal_acara": tanggal_acara,
        "jumlah_kambing": jumlah_kambing,
        "catatan": catatan,
        "total_harga": total_harga,
        "dp_amount": dp_amount,
        "sisa_amount": sisa_amount,
        "status": "dp_paid",
        "midtrans_order_id": midtrans_order_id,
        "payment_url": payment_url
    }

    response = supabase.table("orders").insert(data).execute()
    return response.data[0] if response.data else {}


def update_order_status(order_id: str, status: str) -> dict:
    """Update status pesanan.
    
    Status: invoiced | dp_paid | in_progress | delivered | completed | cancelled | payment_failed
    """
    response = (
        supabase.table("orders")
        .update({"status": status, "updated_at": datetime.utcnow().isoformat()})
        .eq("id", order_id)
        .execute()
    )
    return response.data[0] if response.data else {}


def update_order_payment_url(order_id: str, payment_url: str, midtrans_order_id: str) -> dict:
    """Simpan payment_url dan midtrans_order_id setelah invoice dibuat."""
    response = (
        supabase.table("orders")
        .update({
            "payment_url": payment_url,
            "midtrans_order_id": midtrans_order_id,
            "status": "invoiced",
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("id", order_id)
        .execute()
    )
    return response.data[0] if response.data else {}


def get_order_by_midtrans_id(midtrans_order_id: str) -> Optional[dict]:
    """Ambil pesanan berdasarkan midtrans_order_id (untuk webhook)."""
    response = (
        supabase.table("orders")
        .select("*")
        .eq("midtrans_order_id", midtrans_order_id)
        .single()
        .execute()
    )
    return response.data if response.data else None


def get_order_by_id(order_id: str) -> Optional[dict]:
    """Ambil pesanan berdasarkan id."""
    response = (
        supabase.table("orders")
        .select("*")
        .eq("id", order_id)
        .single()
        .execute()
    )
    return response.data if response.data else None


# =============================================
# PAYMENTS
# =============================================

def insert_payment(
    order_id: str,
    tipe: str,  # 'dp' atau 'pelunasan'
    jumlah: int,
    metode: str = "",
    midtrans_transaction_id: str = "",
    midtrans_status: str = "",
    payload: dict = {}
) -> dict:
    """Catat pembayaran DP atau pelunasan."""
    data = {
        "order_id": order_id,
        "tipe": tipe,
        "jumlah": jumlah,
        "metode": metode,
        "status": "success",
        "midtrans_transaction_id": midtrans_transaction_id,
        "midtrans_status": midtrans_status,
        "payload": payload
    }

    response = supabase.table("payments").insert(data).execute()
    return response.data[0] if response.data else {}


def update_payment_status(order_id: str, status: str, payload: dict = {}) -> dict:
    """Update status payment berdasarkan order_id (untuk webhook gagal/expired)."""
    response = (
        supabase.table("payments")
        .update({"status": status, "payload": payload})
        .eq("order_id", order_id)
        .execute()
    )
    return response.data[0] if response.data else {}


# =============================================
# PROSPEK
# =============================================

def update_prospek_status(prospek_id: int, status: str) -> dict:
    """Update status prospek setelah jadi order."""
    response = (
        supabase.table("prospek")
        .update({"status": status})
        .eq("id", prospek_id)
        .execute()
    )
    return response.data[0] if response.data else {}


# =============================================
# HISTORY CHAT
# =============================================

def save_chat_message(
    session_id: str,
    nama_pelanggan: str,
    role: str,  # 'user' atau 'assistant'
    message: str,
    nomor_wa: str = "",
    order_id: Optional[str] = None
) -> dict:
    """Simpan pesan chat ke history_chat."""
    data = {
        "session_id": session_id,
        "nama_pelanggan": nama_pelanggan,
        "role": role,
        "message": message,
        "nomor_wa": nomor_wa,
        "order_id": order_id
    }

    response = supabase.table("history_chat").insert(data).execute()
    return response.data[0] if response.data else {}


def get_chat_history(session_id: str, limit: int = 20) -> list:
    """Ambil history chat berdasarkan session_id untuk konteks Delisa."""
    response = (
        supabase.table("history_chat")
        .select("role, message, created_at")
        .eq("session_id", session_id)
        .order("created_at", desc=False)
        .limit(limit)
        .execute()
    )
    return response.data if response.data else []
