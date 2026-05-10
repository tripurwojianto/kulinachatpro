#!/usr/bin/env python3
"""Webhook server - terima pesan WA dari Fonnte, kirim ke Delisa ADK."""
import json
import os
from dotenv import load_dotenv

# Cukup panggil load_dotenv() tanpa path, Railway akan ambil dari tab Variables
load_dotenv() 

# Jika Delisa ADK berjalan di proyek yang sama, gunakan 0.0.0.0
# Jika berbeda, masukkan URL publik ADK Anda
ADK_URL = os.getenv("ADK_URL", "http://0.0.0.0:8080") 
FONNTE_TOKEN = os.getenv("FONNTE_TOKEN", "")
APP_NAME = "customer_service"

def get_or_create_session(user_id: str) -> str:
    """Buat atau ambil session ADK berdasarkan nomor WA."""
    try:
        url = f"{ADK_URL}/apps/{APP_NAME}/users/{user_id}/sessions"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            sessions = json.loads(resp.read())
            if sessions:
                return sessions[-1]["id"]
    except Exception:
        pass

    try:
        url = f"{ADK_URL}/apps/{APP_NAME}/users/{user_id}/sessions"
        req = urllib.request.Request(
            url,
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            session = json.loads(resp.read())
            return session["id"]
    except Exception as e:
        return "default-session"


def send_to_delisa(user_id: str, session_id: str, message: str) -> str:
    """Kirim pesan ke Delisa ADK dan ambil respons."""
    try:
        payload = json.dumps({
            "app_name": APP_NAME,
            "user_id": user_id,
            "session_id": session_id,
            "new_message": {
                "role": "user",
                "parts": [{"text": message}]
            }
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{ADK_URL}/run",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())

        # Ambil teks respons terakhir dari Delisa
        for event in reversed(result):
            if event.get("author") == "Delisa":
                content = event.get("content", {})
                parts = content.get("parts", [])
                for part in parts:
                    if "text" in part:
                        return part["text"]
        return "Maaf, Delisa sedang tidak bisa merespons."

    except Exception as e:
        return f"Maaf, sistem sedang gangguan. ({str(e)[:50]})"


def kirim_wa(nomor: str, pesan: str):
    """Kirim balasan WA via Fonnte."""
    try:
        payload = urllib.parse.urlencode({
            "target": nomor,
            "message": pesan,
            "countryCode": "62",
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.fonnte.com/send",
            data=payload,
            headers={"Authorization": FONNTE_TOKEN},
            method="POST"
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"[WA Error] {e}")


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
        except Exception:
            try:
                data = dict(urllib.parse.parse_qsl(body.decode("utf-8")))
            except Exception:
                data = {}

        print(f"[Webhook] Data masuk: {json.dumps(data, ensure_ascii=False)[:200]}")

        sender = data.get("sender", data.get("from", ""))
        message = data.get("message", data.get("text", "")).strip()

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok"}')

        if sender and message:
            user_id = sender.replace("+", "").replace(" ", "")
            print(f"[Webhook] Dari {user_id}: {message}")

            session_id = get_or_create_session(user_id)
            respons = send_to_delisa(user_id, session_id, message)

            print(f"[Delisa] Respons: {respons[:100]}")
            kirim_wa(sender, respons)

    def log_message(self, format, *args):
        print(f"[HTTP] {format % args}")


if __name__ == "__main__":
    # Railway mengirimkan variabel "PORT", bukan "WEBHOOK_PORT"
    port = int(os.environ.get("PORT", 8000)) 
    
    # Pastikan mengikat ke 0.0.0.0 agar bisa diakses dari luar Railway
    server = HTTPServer(("0.0.0.0", port), WebhookHandler)
    print(f"Webhook server berjalan di port {port}")
    server.serve_forever()
