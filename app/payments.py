import os
import httpx
import base64
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
BASE_URL = os.getenv("BASE_URL", "https://your-app.onrender.com")


async def create_razorpay_link(amount: int, booking_id: int, name: str, phone: str) -> str:
    """
    Creates a Razorpay Payment Link and returns the short URL.
    Amount is in INR (not paise).
    """
    credentials = base64.b64encode(f"{RAZORPAY_KEY_ID}:{RAZORPAY_KEY_SECRET}".encode()).decode()

    payload = {
        "amount": amount * 100,  # Razorpay needs paise
        "currency": "INR",
        "accept_partial": False,
        "description": f"Nirvanta Travels — Booking #{booking_id}",
        "customer": {
            "name": name,
            "contact": f"+{phone}"
        },
        "notify": {
            "sms": True,
            "email": False
        },
        "reminder_enable": True,
        "notes": {
            "booking_id": str(booking_id)
        },
        "callback_url": f"{BASE_URL}/payment/callback",
        "callback_method": "get"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.razorpay.com/v1/payment_links",
            json=payload,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/json"
            }
        )
        data = response.json()
        return data.get("short_url", "Payment link generation failed")


async def verify_payment(razorpay_payment_id: str, razorpay_payment_link_id: str, razorpay_signature: str) -> bool:
    """Verify payment signature from Razorpay callback."""
    import hmac
    import hashlib

    message = f"{razorpay_payment_link_id}|{razorpay_payment_id}"
    expected = hmac.new(
        RAZORPAY_KEY_SECRET.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)
