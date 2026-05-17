# 🏔️ Nirvanta Travels — WhatsApp AI Agent

Complete WhatsApp AI travel agent using **Twilio Sandbox** (no new number needed),
Supabase database, Razorpay payments, and Streamlit admin dashboard.

---

## 📁 Project Structure

```
nirvanta_travels/
├── app/
│   ├── main.py              ← FastAPI server (Twilio webhook)
│   ├── agent.py             ← Claude AI travel agent (Hinglish)
│   ├── database.py          ← Supabase database layer
│   ├── payments.py          ← Razorpay payment link generator
│   └── payment_routes.py   ← Payment confirmed callback
├── streamlit_dashboard/
│   └── dashboard.py         ← Admin panel
├── database/
│   ├── schema.sql           ← Step 1: Run this in Supabase
│   └── security_fixes.sql  ← Step 2: Run this in Supabase
├── .env.example             ← Copy to .env and fill values
├── requirements.txt
└── README.md
```

---

## ⚙️ Step-by-Step Setup

### STEP 1 — Supabase (Free Database)

1. Go to https://supabase.com → Create account → New project
2. Go to **SQL Editor** → paste `database/schema.sql` → Run
3. Then paste `database/security_fixes.sql` → Run
4. Go to **Settings → API**:
   - Copy **Project URL** → `SUPABASE_URL` in .env
   - Copy **service_role** key (not anon!) → `SUPABASE_KEY` in .env
5. Go to **Storage** → New bucket → Name: `trip-photos` → Public: ON
6. Upload trip photos → copy public URLs → use when adding trips in dashboard

---

### STEP 2 — Twilio WhatsApp Sandbox (Free, no new number needed)

1. Go to https://twilio.com → Create free account
2. Dashboard → **Messaging → Try it out → Send a WhatsApp message**
3. You'll see the sandbox number: `+1 415 523 8886`
4. On YOUR WhatsApp, send: `join <sandbox-keyword>` to `+14155238886`
   (Twilio will show you the exact keyword, like "join yellow-tiger")
5. Your number is now connected to the sandbox ✅
6. Go to **Account → API Keys** → copy **Account SID** and **Auth Token**
7. In Twilio Console → Messaging → Settings → WhatsApp Sandbox Settings:
   - Set **"When a message comes in"** webhook URL to:
     `https://your-app.onrender.com/webhook`
   - Method: `HTTP POST`

> ⚠️ Anyone who wants to test the bot must send the join message first.
> For production, upgrade to a real Twilio number (~$1/month).

---

### STEP 3 — Razorpay (Free signup, only 2% per transaction)

1. Go to https://razorpay.com → Sign up
2. Complete KYC (PAN + bank account)
3. **Settings → API Keys → Generate Test Key** (use test first!)
4. Copy **Key ID** and **Key Secret** → add to .env
5. Test mode mein real money nahi kataega

---

### STEP 4 — Anthropic API Key

1. Go to https://console.anthropic.com
2. Create API key → add to .env as `ANTHROPIC_API_KEY`

---

### STEP 5 — Local Setup & Testing

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and fill environment file
cp .env.example .env
# Edit .env with your actual keys

# 3. Run the bot server
uvicorn app.main:app --reload --port 8000

# 4. Expose locally using ngrok (free)
# Download ngrok from https://ngrok.com
ngrok http 8000
# Copy the https URL (e.g. https://abc123.ngrok.io)
# Paste into Twilio sandbox webhook URL

# 5. Run Streamlit dashboard (separate terminal)
streamlit run streamlit_dashboard/dashboard.py
```

**Test the bot:**
- Open WhatsApp on your phone
- Message `+14155238886` (Twilio sandbox)
- Say "Hi" → bot should reply in Hinglish!

---

### STEP 6 — Deploy on Render (Free hosting)

1. Push project to GitHub
2. Go to https://render.com → New Web Service → Connect repo
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add all `.env` variables under **Environment** tab
6. Deploy → copy the URL (e.g. `https://nirvanta-travels.onrender.com`)
7. Update Twilio sandbox webhook URL with this Render URL + `/webhook`

**Streamlit Dashboard on Streamlit Cloud (Free):**
1. Go to https://streamlit.io/cloud → New app
2. Repo: your GitHub repo | File: `streamlit_dashboard/dashboard.py`
3. Add secrets (same as .env) under **Advanced Settings → Secrets**

---

## 🤖 How the Bot Works

```
You (customer) WhatsApp karte ho
        ↓
Twilio receives message → sends to your FastAPI /webhook
        ↓
FastAPI → Claude AI reads live trips from Supabase
        ↓
Claude replies in Hinglish with trip suggestions
        ↓
Customer books → bot collects name, date, travellers
        ↓
Razorpay payment link generated + sent via WhatsApp
        ↓
Customer pays → payment confirmed
        ↓
Bot sends receipt to customer
Owner gets WhatsApp notification
Booking updated in Streamlit dashboard
```

---

## 📊 Streamlit Dashboard Features

| Page | What you can do |
|---|---|
| Dashboard | Total bookings, revenue, pending payments, confirm manually |
| Trips | View all trips, edit prices, delete trips |
| Bookings | View all bookings filtered by status, confirm payments |
| Add Trip | Add new trips with full itinerary, photos, dates, pricing |

Default password: `nirvanta2025` (change in .env → `DASHBOARD_PASSWORD`)

---

## 💰 Monthly Cost

| Service | Cost |
|---|---|
| Supabase | ₹0 (500MB free) |
| Twilio Sandbox | ₹0 (testing) / ~₹80/month (real number) |
| Render hosting | ₹0 (free tier) |
| Streamlit Cloud | ₹0 |
| Claude API | ~₹0.10–0.50 per conversation |
| Razorpay | 2% only on successful bookings |

**Fixed monthly cost = ₹0**
