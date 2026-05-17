-- =============================================
-- NIRVANTA TRAVELS — SUPABASE DATABASE SCHEMA
-- Run this in Supabase SQL Editor
-- =============================================

-- TRIPS TABLE
create table trips (
  id              bigserial primary key,
  name            text not null,
  destination     text not null,
  days            int not null,
  nights          int not null,
  price_per_person int not null,
  vehicle         text not null,
  inclusions      text not null,
  itinerary_short text,
  itinerary_full  text,
  available_dates text[],
  max_seats       int default 20,
  is_active       boolean default true,
  created_at      timestamptz default now()
);

-- TRIP PHOTOS TABLE
create table trip_photos (
  id        bigserial primary key,
  trip_id   bigint references trips(id) on delete cascade,
  photo_url text not null,
  caption   text,
  created_at timestamptz default now()
);

-- BOOKINGS TABLE
create table bookings (
  id                   bigserial primary key,
  trip_id              bigint references trips(id),
  customer_name        text not null,
  customer_phone       text not null,
  travel_date          text not null,
  adults               int not null default 1,
  kids                 int default 0,
  total_amount         int not null,
  status               text default 'pending_payment',
  razorpay_payment_id  text,
  notes                text,
  created_at           timestamptz default now()
);

-- SESSIONS TABLE (conversation memory)
create table sessions (
  id         bigserial primary key,
  phone      text unique not null,
  data       jsonb default '{}',
  updated_at timestamptz default now()
);

-- =============================================
-- SAMPLE DATA — Nirvanta Travels Trips
-- =============================================

insert into trips (name, destination, days, nights, price_per_person, vehicle, inclusions, itinerary_short, available_dates, max_seats) values

('Bir Billing Paragliding Trip', 'Bir, Himachal Pradesh', 2, 1, 3499,
 'Tempo Traveller',
 '• Paragliding flight (tandem)\n• 1 night homestay\n• Breakfast + Dinner\n• Sightseeing\n• All transfers',
 'Day 1: Delhi se Bir pick-up → Arrive Bir → Monastery visit → Paragliding briefing → Dinner + Rest\nDay 2: Early morning paragliding → Landing at Billing → Return journey',
 ARRAY['2025-06-15', '2025-06-22', '2025-07-06', '2025-07-13'], 15),

('Rishikesh 2 Day Adventure Tour', 'Rishikesh, Uttarakhand', 2, 1, 2999,
 'Tempo Traveller',
 '• White water rafting (16km)\n• Bungee jumping optional\n• 1 night camp stay\n• All meals\n• Bonfire evening\n• All transfers',
 'Day 1: Delhi se Rishikesh → Check-in river camp → Rafting → Evening aarti at Ganga → Bonfire\nDay 2: Yoga session → Optional bungee/zip-line → Laxman Jhula → Return',
 ARRAY['2025-06-20', '2025-06-27', '2025-07-04', '2025-07-11'], 20),

('Rajasthan Royal 10 Days Tour', 'Jaipur, Jodhpur, Jaisalmer, Udaipur', 10, 9, 18999,
 'AC Volvo Bus + Local Cab',
 '• 9 nights hotel (3-star)\n• Daily breakfast + dinner\n• All sightseeing entry fees\n• Camel safari in Jaisalmer\n• Boat ride in Udaipur\n• Professional guide\n• All transfers',
 'Day 1-2: Jaipur — Amber Fort, Hawa Mahal, City Palace\nDay 3-4: Jodhpur — Mehrangarh Fort, Blue City walk\nDay 5-7: Jaisalmer — Desert safari, Sam Sand Dunes, camel ride\nDay 8-10: Udaipur — Lake Pichola, City Palace, Fateh Sagar',
 ARRAY['2025-10-15', '2025-11-01', '2025-11-15', '2025-12-01'], 25),

('Manali Spiti Valley 7 Days', 'Manali, Kaza, Pin Valley, Chandratal', 7, 6, 12499,
 'Tempo Traveller (4x4)',
 '• 6 nights accommodation (mix of hotels + camps)\n• All meals\n• Spiti valley sightseeing\n• Chandratal lake visit\n• Monastery tours\n• All transfers\n• Experienced mountain driver',
 'Day 1: Manali → Kaza via Rohtang\nDay 2: Kaza local — Key Monastery, Kibber\nDay 3: Tabo, Dhankar monastery\nDay 4: Pin Valley National Park\nDay 5: Chandratal Lake camp\nDay 6: Atal Tunnel route back\nDay 7: Manali drop',
 ARRAY['2025-07-10', '2025-07-25', '2025-08-05', '2025-08-20'], 12),

('Kedarnath Badrinath Char Dham Yatra', 'Haridwar, Kedarnath, Badrinath, Yamunotri, Gangotri', 12, 11, 22999,
 'AC Tempo Traveller',
 '• 11 nights accommodation\n• All meals (veg)\n• Kedarnath pony/helicopter optional\n• All temple darshan arrangements\n• Puja samagri\n• Experienced yatra guide\n• Medical kit',
 'Day 1-2: Haridwar → Yamunotri\nDay 3-4: Gangotri\nDay 5-7: Kedarnath (pony/palanquin available extra)\nDay 8-10: Badrinath + Mana village\nDay 11-12: Return to Haridwar',
 ARRAY['2025-05-20', '2025-06-01', '2025-06-15', '2025-09-10'], 20);
