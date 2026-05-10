import midtransclient
import os

MIDTRANS_SERVER_KEY = os.getenv("MIDTRANS_SERVER_KEY", "")
MIDTRANS_IS_PRODUCTION = os.getenv("MIDTRANS_IS_PRODUCTION", "false").lower() == "true"

snap = midtransclient.Snap(
    is_production=MIDTRANS_IS_PRODUCTION,
    server_key=MIDTRANS_SERVER_KEY
)

def create_snap_transaction(order_id: str, amount: int, customer: dict, items: list):
    param = {
        "transaction_details": {
            "order_id": order_id,
            "gross_amount": amount
        },
        "customer_details": {
            "first_name": customer["name"],
            "email": customer.get("email", ""),
            "phone": customer.get("phone", "")
        },
        "item_details": items,
        "expiry": {
            "unit": "hours",
            "duration": 24
        }
    }
    transaction = snap.create_transaction(param)
    return transaction["token"], transaction["redirect_url"]
