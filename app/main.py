import os
from fastapi import FastAPI, Form
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv
from twilio.rest import Client as TwilioClient
from app.agent import TravelAgent
from app.database import Database

load_dotenv()

app = FastAPI(title="Nirvanta Travels WhatsApp Bot")
db = Database()
agent = TravelAgent(db)

TWILIO_ACCOUNT_SID   = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN    = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
OWNER_PHONE          = os.getenv("OWNER_PHONE_NUMBER")

twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


@app.get("/")
async def root():
    return {"status": "Nirvanta Travels bot is running 🏔️"}


@app.post("/webhook")
async def receive_message(
    From: str = Form(...),
    Body: str = Form(...),
    NumMedia: str = Form("0")
):
    """Twilio sends WhatsApp messages as form-encoded POST."""
    user_phone = From.replace("whatsapp:", "")
    user_text  = Body.strip()

    if not user_text:
        return PlainTextResponse("<?xml version='1.0'?><Response/>", media_type="application/xml")

    messages = await agent.process(user_phone, user_text)
    for msg in messages:
        await send_whatsapp_message(From, msg)

    return PlainTextResponse("<?xml version='1.0'?><Response/>", media_type="application/xml")


async def send_whatsapp_message(to: str, payload: dict):
    try:
        if not to.startswith("whatsapp:"):
            to = f"whatsapp:{to}"

        msg_type = payload.get("type", "text")

        if msg_type == "text":
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_FROM,
                to=to,
                body=payload["text"]["body"]
            )
        elif msg_type == "image":
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_FROM,
                to=to,
                body=payload["image"].get("caption", ""),
                media_url=[payload["image"]["link"]]
            )
    except Exception as e:
        print(f"Twilio send error: {e}")


async def notify_owner(message: str):
    if OWNER_PHONE:
        owner = OWNER_PHONE if OWNER_PHONE.startswith("whatsapp:") else f"whatsapp:{OWNER_PHONE}"
        try:
            twilio_client.messages.create(
                from_=TWILIO_WHATSAPP_FROM,
                to=owner,
                body=f"🔔 *Nirvanta Travels Alert*\n\n{message}"
            )
        except Exception as e:
            print(f"Owner notify error: {e}")
