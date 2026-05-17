import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class Database:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.client: Client = create_client(url, key)

    # ── TRIPS ──────────────────────────────────────────────
    def get_all_trips(self) -> list[dict]:
        res = self.client.table("trips").select("*").eq("is_active", True).order("created_at", desc=True).execute()
        return res.data or []

    def get_trip_by_id(self, trip_id: int) -> dict | None:
        res = self.client.table("trips").select("*").eq("id", trip_id).single().execute()
        return res.data

    def get_trip_photos(self, trip_id: int) -> list[str]:
        res = self.client.table("trip_photos").select("photo_url").eq("trip_id", trip_id).execute()
        return [r["photo_url"] for r in (res.data or [])]

    def search_trips(self, query: str) -> list[dict]:
        res = self.client.table("trips").select("*").eq("is_active", True).ilike("name", f"%{query}%").execute()
        return res.data or []

    def get_trips_by_budget(self, max_price: int) -> list[dict]:
        res = self.client.table("trips").select("*").eq("is_active", True).lte("price_per_person", max_price).execute()
        return res.data or []

    # ── BOOKINGS ───────────────────────────────────────────
    def create_booking(self, data: dict) -> dict:
        data["created_at"] = datetime.utcnow().isoformat()
        data["status"] = "pending_payment"
        res = self.client.table("bookings").insert(data).execute()
        return res.data[0] if res.data else {}

    def update_booking_status(self, booking_id: int, status: str, razorpay_id: str = None):
        update = {"status": status}
        if razorpay_id:
            update["razorpay_payment_id"] = razorpay_id
        self.client.table("bookings").update(update).eq("id", booking_id).execute()

    def get_booking(self, booking_id: int) -> dict | None:
        res = self.client.table("bookings").select("*, trips(name, price_per_person)").eq("id", booking_id).single().execute()
        return res.data

    def get_bookings_by_phone(self, phone: str) -> list[dict]:
        res = self.client.table("bookings").select("*, trips(name, price_per_person, days)").eq("customer_phone", phone).order("created_at", desc=True).execute()
        return res.data or []

    def get_all_bookings(self) -> list[dict]:
        res = self.client.table("bookings").select("*, trips(name)").order("created_at", desc=True).execute()
        return res.data or []

    # ── SESSIONS ───────────────────────────────────────────
    def get_session(self, phone: str) -> dict:
        res = self.client.table("sessions").select("*").eq("phone", phone).execute()
        if res.data:
            return res.data[0].get("data", {})
        return {}

    def set_session(self, phone: str, data: dict):
        existing = self.client.table("sessions").select("id").eq("phone", phone).execute()
        if existing.data:
            self.client.table("sessions").update({"data": data, "updated_at": datetime.utcnow().isoformat()}).eq("phone", phone).execute()
        else:
            self.client.table("sessions").insert({"phone": phone, "data": data, "updated_at": datetime.utcnow().isoformat()}).execute()

    def clear_session(self, phone: str):
        self.set_session(phone, {})

    # ── TRIPS CRUD for dashboard ────────────────────────────
    def add_trip(self, trip: dict) -> dict:
        trip["created_at"] = datetime.utcnow().isoformat()
        trip["is_active"] = True
        res = self.client.table("trips").insert(trip).execute()
        return res.data[0] if res.data else {}

    def update_trip(self, trip_id: int, data: dict) -> dict:
        res = self.client.table("trips").update(data).eq("id", trip_id).execute()
        return res.data[0] if res.data else {}

    def delete_trip(self, trip_id: int):
        self.client.table("trips").update({"is_active": False}).eq("id", trip_id).execute()

    def add_trip_photo(self, trip_id: int, photo_url: str):
        self.client.table("trip_photos").insert({"trip_id": trip_id, "photo_url": photo_url}).execute()

    def delete_trip_photos(self, trip_id: int):
        self.client.table("trip_photos").delete().eq("trip_id", trip_id).execute()
