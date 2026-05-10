import hashlib

def verify_signature(
    order_id: str,
    status_code: str,
    gross_amount: str,
    server_key: str,
    signature_key: str
) -> bool:
    raw = f"{order_id}{status_code}{gross_amount}{server_key}"
    expected = hashlib.sha512(raw.encode()).hexdigest()
    return expected == signature_key
