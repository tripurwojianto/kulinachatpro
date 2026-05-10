import os
import httpx
from typing import Optional

FONNTE_TOKEN = os.getenv("FONNTE_TOKEN", "")
FONNTE_URL = "https://api.fonnte.com/send"


async def send_whatsapp(nomor_wa: str, pesan: str) -> dict:
    """Kirim pesan WhatsApp via Fonnte."""
    headers = {"Authorization": FONNTE_TOKEN}
    payload = {
        "target": nomor_wa,
        "message": pesan,
        "countryCode": "62"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(FONNTE_URL, headers=headers, data=payload)
        return response.json()


# =============================================
# TEMPLATE PESAN
# =============================================

async def kirim_invoice(
    nomor_wa: str,
    nama_pelanggan: str,
    paket: str,
    tanggal_acara: str,
    jumlah_kambing: int,
    total_harga: int,
    dp_amount: int,
    payment_url: str,
    order_id: str
) -> dict:
    """Kirim invoice + link pembayaran DP ke klien."""
    pesan = f"""Assalamu'alaikum {nama_pelanggan} 🌙

Terima kasih telah menghubungi *Kulina Aqiqah*.

Berikut detail pesanan Anda:

📋 *INVOICE PESANAN*
━━━━━━━━━━━━━━━━━━━━
Paket       : {paket}
Tgl Acara   : {tanggal_acara}
Jml Kambing : {jumlah_kambing} ekor
No. Order   : {order_id}
━━━━━━━━━━━━━━━━━━━━
Total Harga : Rp {total_harga:,}
DP (50%)    : Rp {dp_amount:,}
Sisa Lunas  : Rp {total_harga - dp_amount:,}
━━━━━━━━━━━━━━━━━━━━

Silakan lakukan pembayaran DP melalui link berikut:
{payment_url}

⏳ Link pembayaran berlaku 24 jam.

Setelah DP terkonfirmasi, pesanan Anda akan segera kami proses.

Jazakallah khairan 🙏
*Tim Kulina Aqiqah*"""

    return await send_whatsapp(nomor_wa, pesan)


async def kirim_konfirmasi_dp(
    nomor_wa: str,
    nama_pelanggan: str,
    paket: str,
    tanggal_acara: str,
    dp_amount: int,
    sisa_amount: int,
    order_id: str
) -> dict:
    """Kirim konfirmasi setelah DP lunas."""
    pesan = f"""Assalamu'alaikum {nama_pelanggan} 🌙

*Pembayaran DP Anda telah kami terima!* ✅

Detail konfirmasi:
━━━━━━━━━━━━━━━━━━━━
Paket       : {paket}
Tgl Acara   : {tanggal_acara}
No. Order   : {order_id}
DP Diterima : Rp {dp_amount:,}
Sisa Lunas  : Rp {sisa_amount:,}
━━━━━━━━━━━━━━━━━━━━

Pesanan Anda sudah kami konfirmasi dan akan segera diproses.

Pelunasan sebesar Rp {sisa_amount:,} akan ditagihkan saat pesanan diantarkan.

Terima kasih kepercayaannya 🙏
*Tim Kulina Aqiqah*"""

    return await send_whatsapp(nomor_wa, pesan)


async def kirim_tagihan_pelunasan(
    nomor_wa: str,
    nama_pelanggan: str,
    paket: str,
    sisa_amount: int,
    payment_url: str,
    order_id: str
) -> dict:
    """Kirim tagihan pelunasan saat pesanan diantar."""
    pesan = f"""Assalamu'alaikum {nama_pelanggan} 🌙

Pesanan Aqiqah Anda sedang dalam perjalanan! 🚗

Mohon siapkan pelunasan:
━━━━━━━━━━━━━━━━━━━━
Paket       : {paket}
No. Order   : {order_id}
Sisa Lunas  : Rp {sisa_amount:,}
━━━━━━━━━━━━━━━━━━━━

Bisa dibayar tunai saat pengiriman atau via link:
{payment_url}

Terima kasih 🙏
*Tim Kulina Aqiqah*"""

    return await send_whatsapp(nomor_wa, pesan)


async def kirim_konfirmasi_lunas(
    nomor_wa: str,
    nama_pelanggan: str,
    paket: str,
    total_harga: int,
    order_id: str
) -> dict:
    """Kirim konfirmasi pesanan selesai & lunas."""
    pesan = f"""Assalamu'alaikum {nama_pelanggan} 🌙

*Pesanan Anda telah selesai!* ✅

━━━━━━━━━━━━━━━━━━━━
Paket       : {paket}
No. Order   : {order_id}
Total Lunas : Rp {total_harga:,}
━━━━━━━━━━━━━━━━━━━━

Semoga Aqiqah putra-putri Anda penuh berkah 🤲

Mohon berikan ulasan Anda untuk membantu kami berkembang.

Jazakallah khairan 🙏
*Tim Kulina Aqiqah*"""

    return await send_whatsapp(nomor_wa, pesan)


async def kirim_notif_pembayaran_gagal(
    nomor_wa: str,
    nama_pelanggan: str,
    payment_url: str
) -> dict:
    """Kirim notif ke klien jika pembayaran gagal/expired."""
    pesan = f"""Assalamu'alaikum {nama_pelanggan} 🌙

Kami ingin menginformasikan bahwa pembayaran DP Anda *belum berhasil* atau telah kadaluarsa.

Silakan lakukan pembayaran kembali melalui link berikut:
{payment_url}

Jika ada kendala, hubungi kami langsung.

*Tim Kulina Aqiqah*"""

    return await send_whatsapp(nomor_wa, pesan)
