-- =============================================
-- NIRVANTA TRAVELS — SECURITY FIXES
-- Run this in Supabase SQL Editor AFTER schema.sql
-- Fixes: RLS policies + unindexed foreign keys
-- =============================================


-- ── 1. ENABLE RLS ON ALL TABLES ──────────────

alter table trips        enable row level security;
alter table trip_photos  enable row level security;
alter table bookings     enable row level security;
alter table sessions     enable row level security;


-- ── 2. RLS POLICIES FOR TRIPS ────────────────

-- Anyone can read active trips (for the bot)
create policy "Public can read active trips"
  on trips for select
  using (is_active = true);

-- Only service role (your backend) can insert/update/delete
create policy "Service role can manage trips"
  on trips for all
  using (auth.role() = 'service_role');


-- ── 3. RLS POLICIES FOR TRIP_PHOTOS ──────────

-- Anyone can read photos (for the bot)
create policy "Public can read trip photos"
  on trip_photos for select
  using (true);

-- Only service role can manage photos
create policy "Service role can manage trip photos"
  on trip_photos for all
  using (auth.role() = 'service_role');


-- ── 4. RLS POLICIES FOR BOOKINGS ─────────────

-- Service role only (bookings are private)
create policy "Service role can manage bookings"
  on bookings for all
  using (auth.role() = 'service_role');


-- ── 5. RLS POLICIES FOR SESSIONS ─────────────

-- Service role only (session data is private)
create policy "Service role can manage sessions"
  on sessions for all
  using (auth.role() = 'service_role');


-- ── 6. FIX UNINDEXED FOREIGN KEYS ────────────

-- Index on bookings.trip_id
create index if not exists idx_bookings_trip_id
  on bookings(trip_id);

-- Index on trip_photos.trip_id
create index if not exists idx_trip_photos_trip_id
  on trip_photos(trip_id);


-- ── 7. EXTRA USEFUL INDEXES ──────────────────

-- For fast session lookup by phone
create index if not exists idx_sessions_phone
  on sessions(phone);

-- For fast booking lookup by phone
create index if not exists idx_bookings_phone
  on bookings(customer_phone);

-- For filtering active trips
create index if not exists idx_trips_is_active
  on trips(is_active);
