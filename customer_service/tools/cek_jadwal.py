# Tambahkan di tools/tools.py

JADWAL_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vQEP0hnB2dzF6qd1YMCZTXPYlDTWsPuMdJkcNjFP3iab68h3HzTTkBkYrtXcvMK8WjaIx46o4HvJxpK"
    "/pub?gid=106223976&single=true&output=csv"
)

def cek_jadwal(tanggal: str = None) -> str:
    """
    Mengambil ketersediaan jadwal aqiqah dari database Lazizah.

    Args:
        tanggal: Filter tanggal spesifik format YYYY-MM-DD.
                 Kosongkan untuk tampilkan semua jadwal tersedia.

    Returns:
        Informasi jadwal dan slot yang masih tersedia.
    """
    try:
        rows = _fetch_csv(JADWAL_URL)
        tersedia = []

        for row in rows:
            # skip baris kosong
            if not row.get("tanggal", "").strip():
                continue

            status = row.get("status", "").lower()
            tgl = row.get("tanggal", "")

            # filter tanggal jika diberikan
            if tanggal and tanggal not in tgl:
                continue

            slot = row.get("slot_tersedia", "0")
            alamat = row.get("alamat", "-")

            if status == "tersedia":
                tersedia.append(
                    f"• {tgl} — {slot} slot tersedia\n"
                    f"  Area: {alamat}"
                )

        if not tersedia:
            return (
                "Belum ada jadwal tersedia yang tercatat. "
                "Silakan hubungi kami langsung untuk penjadwalan."
            )

        hasil = "📅 Jadwal Aqiqah Lazizah Tersedia\n"
        hasil += "=" * 35 + "\n\n"
        hasil += "\n\n".join(tersedia)
        hasil += "\n\n_Jadwal real-time. Segera konfirmasi untuk booking._"
        return hasil

    except Exception as e:
        return f"Maaf, data jadwal sedang tidak bisa diakses. (Error: {str(e)})"
