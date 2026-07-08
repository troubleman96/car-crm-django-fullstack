# CarDealTZ — Car Dealership CRM (Tanzania)

A Django-based Customer Relationship Management system built for car dealerships in Tanzania. Handles inventory, leads, appointments, SMS notifications (via SendAfrica), chatbot, and marketing campaigns.

**Stack:** Django 6.0 · MySQL 8.0 · Tailwind CSS · SendAfrica SMS API · Alpine.js

---

## Project Structure

```
car_crm/                    # Django project settings
├── settings.py             # Database, apps, middleware, templates
├── urls.py                 # Root URL routing
├── wsgi.py / asgi.py       # WSGI/ASGI entry points

accounts/                   # CustomUser, OTP, authentication
├── models.py               # CustomUser (phone-based), OTP model
├── views.py                # Staff login, customer OTP login
├── forms.py                # StaffLoginForm, PhoneForm, OTPVerifyForm
├── admin.py                # CustomUserAdmin, OTPAdmin
├── urls.py                 # login, logout, otp/send, otp/verify
└── management/commands/seed_data.py  # DB seeder

vehicles/                   # Car inventory
├── models.py               # Car, CarImage
├── views.py                # Landing page, car detail
├── admin.py                # CarAdmin with CarImageInline
└── urls.py                 # / and /car/<id>/

leads/                      # Leads and appointments
├── models.py               # Lead, Appointment
├── views.py                # Booking flow (car -> type -> phone -> confirm)
├── admin.py                # LeadAdmin with AppointmentInline
└── urls.py                 # /book/

chatbot/                    # Live chat widget (mock AI)
├── models.py               # ChatSession, ChatMessage
├── views.py                # Chat API (POST JSON, returns bot reply)
├── bot.py                  # Mock keyword-matching bot
├── admin.py                # ChatSessionAdmin, ChatMessageAdmin
└── urls.py                 # /message/, /history/<id>/

notifications/              # SMS gateway (SendAfrica)
├── models.py               # SmsLog
├── services.py             # send_sms() — the ONLY place calling SendAfrica
├── admin.py                # SmsLogAdmin
└── urls.py                 # (no public URLs)

campaigns/                  # Marketing SMS blasts
├── models.py               # Campaign, CampaignRecipient
├── admin.py                # CampaignAdmin with "Send Campaign" action
└── urls.py                 # (no public URLs)

templates/                  # All HTML templates
├── base.html               # Base layout with Tailwind CSS
├── accounts/               # Staff login, OTP send, OTP verify
├── vehicles/               # Landing page, car detail
├── leads/                  # Booking form
└── chatbot/widget.html     # Chat widget (included in landing + detail)
```

---

## Quick Start

### 1. Prerequisites

```bash
python3 --version    # Python 3.10+
mysql --version      # MySQL 8.0+
```

### 2. Clone & Setup

```bash
git clone <repo-url> cardealtz
cd cardealtz

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Database

**Option A — MySQL (production):**

```bash
# Create the database
mysql -u root -p -e "CREATE DATABASE car_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Copy and edit env file
cp .env.example .env
# Edit .env with your MySQL credentials
```

**Option B — SQLite (development):**

```bash
export USE_MYSQL=False
```

### 4. Migrate & Seed

```bash
python manage.py migrate
python manage.py seed_data
```

### 5. Run

```bash
python manage.py runserver
```

Visit **http://localhost:8000** for the public site and **http://localhost:8000/admin/** for the admin panel.

---

## Seed Data

The `seed_data` command creates realistic sample data:

| Type | Credentials |
|------|-------------|
| Admin | `+255711000001` / `admin123` |
| Marketing | `+255711000002` / `marketing123` |
| Sales | `+255711000003` / `sales123` |
| Support | `+255711000004` / `support123` |
| Customer 1 | `+255712000001` (OTP login only) |
| Customer 2 | `+255712000002` (OTP login only) |

Also creates: 8 cars with images, 3 leads, 2 appointments, 2 SMS logs, 1 chat session, 1 campaign.

---

## 8 Build Phases

This project was built in 8 ordered phases:

### Phase 1 — Project Skeleton
Django project with MySQL config (env-driven), all 6 apps created, static/media directories.

### Phase 2 — Accounts App
- `CustomUser` (phone as USERNAME_FIELD, no username)
- `OTP` model with 5-minute expiry
- Staff login (phone + password)
- Customer OTP login (phone -> SMS code -> verify)
- 4 Django Groups (Admin, Marketing, Sales, Support) via data migration

### Phase 3 — Vehicles App
- `Car` (make, model, year, price, status, description)
- `CarImage` (car FK, image_url, is_primary)
- Landing page listing available cars
- Car detail page
- Admin with CarImage inline

### Phase 4 — Notifications App
- `send_sms()` service — THE single gateway to SendAfrica
- Phone normalization (07xx -> +2557xx)
- `SmsLog` — every SMS attempt logged
- Never raises exceptions (returns True/False)
- Reads `SENDAFRICA_API_KEY` from env

### Phase 5 — Leads App
- `Lead` (customer link, phone, source, interested_car, status, assigned_to)
- `Appointment` (lead, car, type, scheduled_at, status)
- Booking flow: pick car -> type test_drive/call_back/showroom_visit -> phone -> confirm -> SMS
- Admin with Appointment inline

### Phase 6 — Chatbot App
- `ChatSession`, `ChatMessage` models
- Mock AI bot (`bot.py` — keyword matching, swap for LLM later)
- Chat widget (Alpine.js, POST to `/chatbot/message/`)
- Auto-creates Lead from chat when phone is captured

### Phase 7 — Campaigns App
- `Campaign` (name, message_template, status, created_by)
- `CampaignRecipient` (campaign, lead, phone, status, sms_log)
- Admin action "Send Campaign" — sends SMS to all pending recipients
- 150ms delay between sends (rate-limit safe)
- `{full_name}` / `{phone}` personalization

### Phase 8 — Admin Wiring
All models registered in admin. Group-based permissions:
- **Admin**: everything
- **Marketing**: Leads, Campaigns, CampaignRecipients
- **Sales**: Leads, Appointments
- **Support**: ChatSessions, ChatMessages (read-only), Leads (read-only)

---

## SMS Integration (SendAfrica)

All SMS goes through `notifications/services.py:send_sms()`.

### Set up

```bash
export SENDAFRICA_API_KEY="your-api-key-from-sendafrica-dashboard"
```

### SMS Events

| Event | Trigger | Message |
|-------|---------|---------|
| OTP Login | Customer enters phone | "Your verification code is 482910. Valid for 5 minutes." |
| Booking | Customer confirms appointment | "Your Test Drive for Toyota Hilux is booked for ..." |
| Campaign | Admin clicks "Send Campaign" | Personalized template per campaign |

### Phone Format

Tanzania only (07xx, 06xx, +2557xx). See `normalize_phone()` in `services.py`.

---

## Chatbot

The chatbot widget appears on every public page (bottom-right).

**Mock mode:** `chatbot/bot.py` uses keyword matching. To upgrade:

```python
# Replace get_bot_reply() in chatbot/bot.py
# Same signature: (message: str) -> str
# Call any LLM API, keep input/output unchanged
```

The widget uses Alpine.js and sends POST requests to `/chatbot/message/`. If the user shares a phone number and shows booking intent, a Lead is auto-created with `source='chatbot'`.

---

## Key Design Decisions

| Decision | Why |
|----------|-----|
| MySQL with SQLite fallback | MySQL in production, SQLite for dev without MySQL installed |
| `USE_MYSQL=False` env var | Toggle between MySQL and SQLite at runtime |
| pymysql as MySQL driver | Pure Python, no C extensions needed |
| No Celery/Redis | Student project — 50-200 SMS sync is fine |
| One `send_sms()` function | Single gateway, no other app calls SendAfrica directly |
| Django Groups (not custom roles) | Built-in, works with /admin permissions natively |
| Tailwind via CDN | Zero build step, fast prototyping |
| Alpine.js for chat widget | Lightweight, no npm/build needed |
| `seed_data` command | One command to get a working demo |

---

## API Endpoints

### Public

| Method | URL | Description |
|--------|-----|-------------|
| GET | `/` | Landing page with car listing |
| GET | `/car/<id>/` | Car detail page |
| GET | `/leads/book/` | Booking form |
| POST | `/leads/book/` | Submit booking |
| GET | `/accounts/otp/send/` | OTP request form |
| POST | `/accounts/otp/send/` | Send OTP SMS |
| GET | `/accounts/otp/verify/` | OTP verify form |
| POST | `/accounts/otp/verify/` | Verify OTP code |
| POST | `/chatbot/message/` | Send chat message |

### Admin (Django Admin)

| URL | Description |
|-----|-------------|
| `/admin/` | Admin dashboard |
| `/admin/accounts/customuser/` | Manage users |
| `/admin/vehicles/car/` | Manage cars |
| `/admin/leads/lead/` | Manage leads |
| `/admin/leads/appointment/` | Manage appointments |
| `/admin/chatbot/chatsession/` | View chat sessions |
| `/admin/notifications/smslog/` | View SMS logs |
| `/admin/campaigns/campaign/` | Manage campaigns |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | dev-only | Django secret key |
| `DJANGO_DEBUG` | True | Debug mode |
| `DJANGO_ALLOWED_HOSTS` | localhost,127.0.0.1 | Allowed hosts |
| `DB_NAME` | car_crm | MySQL database name |
| `DB_USER` | root | MySQL user |
| `DB_PASSWORD` | (empty) | MySQL password |
| `DB_HOST` | localhost | MySQL host |
| `DB_PORT` | 3306 | MySQL port |
| `USE_MYSQL` | True | Set to False for SQLite |
| `SENDAFRICA_API_KEY` | (empty) | SendAfrica SMS API key |

---

## For Developers

### Run tests

```bash
python manage.py test
```

### Add new models

1. Create/update model in the appropriate app
2. `python manage.py makemigrations <app_name>`
3. `python manage.py migrate`
4. Register in `admin.py`

### Add SMS notifications

```python
from notifications.services import send_sms
send_sms('+255712345678', 'Your message here')
```

---

## License

Student project — Tanzania car dealership CRM.
