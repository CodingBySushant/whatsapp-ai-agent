import os
import json
import re
from groq import AsyncGroq
from app.database import Database
from app.payments import create_razorpay_link
from dotenv import load_dotenv

load_dotenv()

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
OWNER_PHONE = os.getenv("OWNER_PHONE_NUMBER")


# NOTE: Use %s placeholders — filled manually to avoid .format() clash with JSON braces
SYSTEM_PROMPT_TEMPLATE = """Tu Nirvanta Travels ka WhatsApp AI assistant hai — naam hai "Nirva".
Tum ek friendly, helpful travel expert ho jo Hinglish mein baat karta hai (Hindi + English mix).

Tumhara kaam hai:
1. Customers ko trips ke baare mein batana
2. Unki budget aur preferences ke hisaab se trips suggest karna
3. Booking lena (naam, phone, travel date, kitne log)
4. Razorpay payment link bhejna
5. Booking confirm karna aur receipt dena

TONE: Warm, enthusiastic, helpful. Use emojis naturally
LANGUAGE: Hinglish — mostly Hindi but technical words in English
RESPONSE LENGTH: Short 3-5 lines max. WhatsApp pe long text mat likho.

BOOKING FLOW:
Step 1: Customer koi trip mein interest dikhata hai
Step 2: Ek ek karke puchho — pehle naam, phir travel date, phir kitne log
Step 3: Total amount calculate karo (price_per_person x adults) aur confirm karo
Step 4: Jab sab details mil jaaye toh EXACTLY ye likho (kuch aur mat likho baad mein):
         <<CREATE_BOOKING>>
         <BOOKING_DATA>{"trip_id": X, "customer_name": "NAME", "travel_date": "YYYY-MM-DD", "adults": N, "kids": N, "total_amount": NNNN}</BOOKING_DATA>

TRIP DISPLAY: Jab koi specific trip dekhna chahe toh likho:
<<SHOW_TRIP>>
<TRIP_ID>X</TRIP_ID>

RULES:
- Sirf database wali trips batao, kuch invent mat karo
- Ek baar mein ek hi sawaal puchho
- 3-5 lines max per reply

Current trips database:
%s

Current conversation state:
%s
"""


class TravelAgent:
    def __init__(self, db: Database):
        self.db = db

    async def process(self, phone: str, user_text: str) -> list[dict]:
        session = self.db.get_session(phone)
        trips   = self.db.get_all_trips()

        trips_summary = [
            {
                "id": t["id"],
                "name": t["name"],
                "price_per_person": t["price_per_person"],
                "days": t["days"],
                "nights": t["nights"],
                "destination": t["destination"],
                "vehicle": t["vehicle"],
                "inclusions": t["inclusions"],
                "itinerary_short": t.get("itinerary_short", ""),
                "available_dates": t.get("available_dates", []),
                "max_seats": t.get("max_seats", 20),
            }
            for t in trips
        ]

        # Use % formatting — safe with JSON curly braces
        system = SYSTEM_PROMPT_TEMPLATE % (
            json.dumps(trips_summary, ensure_ascii=False, indent=2),
            json.dumps(session, ensure_ascii=False, indent=2)
        )

        history = session.get("history", [])
        history.append({"role": "user", "content": user_text})
        history = history[-20:]

        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=600,
            messages=[{"role": "system", "content": system}] + history
        )

        ai_text = response.choices[0].message.content
        history.append({"role": "assistant", "content": ai_text})

        updated_session = {**session, "history": history}
        messages_to_send = []

        # ── Handle <<CREATE_BOOKING>> ──────────────────────
        if "<<CREATE_BOOKING>>" in ai_text:
            try:
                booking_data = self._extract_tag(ai_text, "BOOKING_DATA", parse_json=True)
                booking = self.db.create_booking({
                    "trip_id":        booking_data["trip_id"],
                    "customer_name":  booking_data["customer_name"],
                    "customer_phone": phone,
                    "travel_date":    booking_data["travel_date"],
                    "adults":         booking_data["adults"],
                    "kids":           booking_data.get("kids", 0),
                    "total_amount":   booking_data["total_amount"],
                })
                pay_link = await create_razorpay_link(
                    amount=booking["total_amount"],
                    booking_id=booking["id"],
                    name=booking["customer_name"],
                    phone=phone
                )
                clean = ai_text.split("<<CREATE_BOOKING>>")[0].strip()
                if clean:
                    messages_to_send.append(self._text(clean))
                messages_to_send.append(self._text(
                    f"Booking create ho gayi!\n\n"
                    f"Payment link:\n{pay_link}\n\n"
                    f"Booking ID: #{booking['id']}\n"
                    f"Is link se payment karein"
                ))
                updated_session["pending_booking_id"] = booking["id"]
                await self._notify_owner(booking, booking_data)

            except Exception as e:
                print(f"Booking error: {e}")
                clean = re.sub(r"<<CREATE_BOOKING>>.*", "", ai_text, flags=re.DOTALL).strip()
                clean = re.sub(r"<BOOKING_DATA>.*?</BOOKING_DATA>", "", clean, flags=re.DOTALL).strip()
                messages_to_send.append(self._text(clean or "Booking mein thodi problem aayi, dobara try karein!"))

        # ── Handle <<SHOW_TRIP>> ───────────────────────────
        elif "<<SHOW_TRIP>>" in ai_text:
            try:
                trip_id = int(self._extract_tag(ai_text, "TRIP_ID"))
                trip    = self.db.get_trip_by_id(trip_id)
                photos  = self.db.get_trip_photos(trip_id)
                clean   = ai_text.split("<<SHOW_TRIP>>")[0].strip()
                if clean:
                    messages_to_send.append(self._text(clean))
                if photos:
                    messages_to_send.append(self._image(photos[0], trip["name"]))
                messages_to_send.append(self._trip_card(trip))
            except Exception as e:
                print(f"Show trip error: {e}")
                clean = re.sub(r"<<SHOW_TRIP>>.*", "", ai_text, flags=re.DOTALL).strip()
                messages_to_send.append(self._text(clean))

        # ── Normal reply ───────────────────────────────────
        else:
            messages_to_send.append(self._text(ai_text))

        self.db.set_session(phone, updated_session)
        return messages_to_send

    # ── Helpers ───────────────────────────────────────────

    def _extract_tag(self, text: str, tag: str, parse_json=False):
        match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
        if not match:
            return None
        content = match.group(1).strip()
        if parse_json:
            return json.loads(content)
        return content

    def _text(self, body: str) -> dict:
        clean = re.sub(r"<<[^>]+>>.*", "", body, flags=re.DOTALL).strip()
        clean = re.sub(r"<[A-Z_]+>.*?</[A-Z_]+>", "", clean, flags=re.DOTALL).strip()
        return {"type": "text", "text": {"body": clean}}

    def _image(self, url: str, caption: str) -> dict:
        return {"type": "image", "image": {"link": url, "caption": f"{caption}"}}

    def _trip_card(self, t: dict) -> dict:
        body = (
            f"*{t['name']}*\n"
            f"Destination: {t['destination']}\n"
            f"Duration: {t['days']} Days / {t['nights']} Nights\n"
            f"Price: Rs.{t['price_per_person']:,} per person\n"
            f"Vehicle: {t['vehicle']}\n\n"
            f"Inclusions:\n{t['inclusions']}\n\n"
            f"Itinerary:\n{t.get('itinerary_short', 'Details ke liye call karein')}"
        )
        return {"type": "text", "text": {"body": body}}

    async def _notify_owner(self, booking: dict, data: dict):
        if not OWNER_PHONE:
            return
        msg = (
            f"New Booking!\n"
            f"ID: #{booking['id']}\n"
            f"Customer: {data['customer_name']}\n"
            f"Phone: {booking['customer_phone']}\n"
            f"Date: {data['travel_date']}\n"
            f"Adults: {data['adults']} | Kids: {data.get('kids', 0)}\n"
            f"Total: Rs.{data['total_amount']:,}\n"
            f"Status: Pending Payment"
        )
        from app.main import notify_owner
        await notify_owner(msg)
