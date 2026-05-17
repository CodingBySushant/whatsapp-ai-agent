import streamlit as st
import pandas as pd
from datetime import datetime
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.database import Database
from supabase import create_client

st.set_page_config(
    page_title="Nirvanta Travels — Admin",
    page_icon="🏔️",
    layout="wide"
)

# ── AUTH ───────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🏔️ Nirvanta Travels Admin")
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        pwd = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True):
            if pwd == os.getenv("DASHBOARD_PASSWORD", "nirvanta2025"):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Wrong password!")
    st.stop()

# ── DB ─────────────────────────────────────────────────────
@st.cache_resource
def get_db():
    return Database()

db = get_db()

# ── SIDEBAR ────────────────────────────────────────────────
st.sidebar.image("https://via.placeholder.com/200x80/1a5276/white?text=NIRVANTA+TRAVELS", width=200)
st.sidebar.title("Navigation")
page = st.sidebar.radio("", ["📊 Dashboard", "📦 Trips", "📅 Bookings", "➕ Add Trip"])

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.rerun()

# ─────────────────────────────────────────────────────────────
# PAGE 1: DASHBOARD
# ─────────────────────────────────────────────────────────────
if page == "📊 Dashboard":
    st.title("📊 Nirvanta Travels — Dashboard")

    bookings = db.get_all_bookings()
    trips = db.get_all_trips()

    df = pd.DataFrame(bookings) if bookings else pd.DataFrame()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Bookings", len(bookings))
    with col2:
        confirmed = len([b for b in bookings if b["status"] == "confirmed"])
        st.metric("Confirmed", confirmed)
    with col3:
        pending = len([b for b in bookings if b["status"] == "pending_payment"])
        st.metric("Pending Payment", pending)
    with col4:
        total_rev = sum(b["total_amount"] for b in bookings if b["status"] == "confirmed")
        st.metric("Revenue", f"₹{total_rev:,}")

    st.markdown("---")
    st.subheader("🔔 Recent Bookings")

    if not df.empty:
        display_cols = ["id", "customer_name", "customer_phone", "travel_date", "adults", "kids", "total_amount", "status", "created_at"]
        available = [c for c in display_cols if c in df.columns]
        st.dataframe(
            df[available].rename(columns={
                "id": "Booking ID", "customer_name": "Name",
                "customer_phone": "Phone", "travel_date": "Travel Date",
                "adults": "Adults", "kids": "Kids",
                "total_amount": "Amount (₹)", "status": "Status",
                "created_at": "Booked At"
            }),
            use_container_width=True
        )
    else:
        st.info("Abhi tak koi booking nahi aayi.")

    st.markdown("---")
    st.subheader("✅ Confirm Payment Manually")
    booking_id = st.number_input("Booking ID", min_value=1, step=1)
    payment_ref = st.text_input("Payment Reference / UTR")
    if st.button("Mark as Confirmed"):
        db.update_booking_status(int(booking_id), "confirmed", payment_ref)
        st.success(f"Booking #{booking_id} confirmed!")
        st.rerun()


# ─────────────────────────────────────────────────────────────
# PAGE 2: TRIPS
# ─────────────────────────────────────────────────────────────
elif page == "📦 Trips":
    st.title("📦 Manage Trips")
    trips = db.get_all_trips()

    if not trips:
        st.info("Koi trip nahi hai abhi.")
    else:
        for trip in trips:
            with st.expander(f"🏔️ {trip['name']} — ₹{trip['price_per_person']:,}/person ({trip['days']}D/{trip['nights']}N)"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Destination:** {trip['destination']}")
                    st.markdown(f"**Vehicle:** {trip['vehicle']}")
                    st.markdown(f"**Max Seats:** {trip.get('max_seats', 20)}")
                    st.markdown(f"**Inclusions:**\n{trip['inclusions']}")
                    st.markdown(f"**Itinerary:**\n{trip.get('itinerary_short', '')}")
                    dates = trip.get("available_dates", [])
                    if dates:
                        st.markdown(f"**Available Dates:** {', '.join(dates)}")

                with col2:
                    photos = db.get_trip_photos(trip["id"])
                    if photos:
                        st.image(photos[0], use_column_width=True)
                        st.caption(f"{len(photos)} photo(s)")

                    st.markdown("---")
                    new_price = st.number_input("Update Price", value=trip["price_per_person"], key=f"price_{trip['id']}")
                    if st.button("Update Price", key=f"upd_{trip['id']}"):
                        db.update_trip(trip["id"], {"price_per_person": new_price})
                        st.success("Price updated!")
                        st.rerun()

                    if st.button("🗑️ Delete Trip", key=f"del_{trip['id']}", type="secondary"):
                        db.delete_trip(trip["id"])
                        st.success("Trip deleted!")
                        st.rerun()


# ─────────────────────────────────────────────────────────────
# PAGE 3: BOOKINGS
# ─────────────────────────────────────────────────────────────
elif page == "📅 Bookings":
    st.title("📅 All Bookings")
    bookings = db.get_all_bookings()

    status_filter = st.selectbox("Filter by Status", ["All", "confirmed", "pending_payment", "cancelled"])

    if bookings:
        df = pd.DataFrame(bookings)
        if status_filter != "All":
            df = df[df["status"] == status_filter]

        for _, row in df.iterrows():
            status_icon = "✅" if row["status"] == "confirmed" else "⏳" if row["status"] == "pending_payment" else "❌"
            with st.expander(f"{status_icon} #{row['id']} — {row['customer_name']} — {row.get('travel_date', '')}"):
                col1, col2 = st.columns(2)
                with col1:
                    trip_name = row["trips"]["name"] if isinstance(row.get("trips"), dict) else "—"
                    st.markdown(f"**Trip:** {trip_name}")
                    st.markdown(f"**Customer:** {row['customer_name']}")
                    st.markdown(f"**Phone:** {row['customer_phone']}")
                    st.markdown(f"**Travel Date:** {row.get('travel_date', '—')}")
                with col2:
                    st.markdown(f"**Adults:** {row.get('adults', 1)} | **Kids:** {row.get('kids', 0)}")
                    st.markdown(f"**Total Amount:** ₹{row['total_amount']:,}")
                    st.markdown(f"**Status:** {row['status']}")
                    st.markdown(f"**Payment ID:** {row.get('razorpay_payment_id', '—')}")
                    st.markdown(f"**Booked At:** {row.get('created_at', '—')[:16]}")

                if row["status"] == "pending_payment":
                    ref = st.text_input("Payment Ref", key=f"ref_{row['id']}")
                    if st.button("✅ Confirm Payment", key=f"conf_{row['id']}"):
                        db.update_booking_status(int(row["id"]), "confirmed", ref)
                        st.success("Confirmed!")
                        st.rerun()
    else:
        st.info("Koi booking nahi mili.")


# ─────────────────────────────────────────────────────────────
# PAGE 4: ADD TRIP
# ─────────────────────────────────────────────────────────────
elif page == "➕ Add Trip":
    st.title("➕ New Trip Add Karo")

    with st.form("add_trip_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Trip Name *", placeholder="Bir Billing Paragliding Trip")
            destination = st.text_input("Destination *", placeholder="Bir, Himachal Pradesh")
            days = st.number_input("Days *", min_value=1, value=3)
            nights = st.number_input("Nights *", min_value=0, value=2)
        with col2:
            price = st.number_input("Price per Person (₹) *", min_value=100, value=3999)
            vehicle = st.text_input("Vehicle *", placeholder="Tempo Traveller / AC Bus / 4x4 Jeep")
            max_seats = st.number_input("Max Seats", min_value=1, value=15)

        inclusions = st.text_area("Inclusions *", placeholder="• Hotel stay\n• Breakfast + Dinner\n• Sightseeing\n• All transfers", height=150)
        itinerary_short = st.text_area("Itinerary (Short) *", placeholder="Day 1: Delhi pickup...\nDay 2: ...", height=200)
        itinerary_full = st.text_area("Itinerary (Full/Detailed)", height=300)
        available_dates = st.text_input("Available Dates (comma separated)", placeholder="2025-06-15, 2025-06-22, 2025-07-06")

        st.markdown("**Trip Photos (Supabase Storage URLs)**")
        photo1 = st.text_input("Photo 1 URL")
        photo2 = st.text_input("Photo 2 URL")
        photo3 = st.text_input("Photo 3 URL")
        photo4 = st.text_input("Photo 4 URL")

        submitted = st.form_submit_button("🚀 Trip Add Karo!", use_container_width=True)

        if submitted:
            if not all([name, destination, inclusions, itinerary_short]):
                st.error("Starred fields required hain!")
            else:
                dates_list = [d.strip() for d in available_dates.split(",") if d.strip()] if available_dates else []
                trip = db.add_trip({
                    "name": name,
                    "destination": destination,
                    "days": int(days),
                    "nights": int(nights),
                    "price_per_person": int(price),
                    "vehicle": vehicle,
                    "inclusions": inclusions,
                    "itinerary_short": itinerary_short,
                    "itinerary_full": itinerary_full,
                    "available_dates": dates_list,
                    "max_seats": int(max_seats),
                })

                for url in [photo1, photo2, photo3, photo4]:
                    if url and url.strip():
                        db.add_trip_photo(trip["id"], url.strip())

                st.success(f"✅ '{name}' successfully add ho gayi! Trip ID: #{trip['id']}")
                st.balloons()
