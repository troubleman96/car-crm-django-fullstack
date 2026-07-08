# CarDealTZ — Car Dealership CRM for Tanzania

**Version:** 1.0.0 | **Stack:** Django 6.0 · MySQL 8.0 / SQLite · Tailwind CSS · SendAfrica SMS · Alpine.js · Jazzmin

A Django-based Customer Relationship Management (CRM) system built for car dealerships in Tanzania. Manages **vehicle inventory**, **customer leads**, **appointments**, **SMS notifications**, **live chat**, **marketing campaigns**, and **advertising promotions**.

---

## Documentation Map

This README is the **entry point**. Each Django app has its own detailed README:

| App | README | What It Covers |
|-----|--------|----------------|
| `car_crm/` | [car_crm/README.md](car_crm/README.md) | Project settings, database config, URL routing, env vars |
| `accounts/` | [accounts/README.md](accounts/README.md) | User model, OTP login, staff password login, phone normalization |
| `vehicles/` | [vehicles/README.md](vehicles/README.md) | Car inventory, landing page, car detail page, image management |
| `leads/` | [leads/README.md](leads/README.md) | Lead pipeline, appointment booking, SMS confirmations |
| `notifications/` | [notifications/README.md](notifications/README.md) | SMS gateway (SendAfrica), phone normalization, SmsLog audit |
| `chatbot/` | [chatbot/README.md](chatbot/README.md) | Chat widget (Alpine.js), API, keyword bot engine, lead creation |
| `campaigns/` | [campaigns/README.md](campaigns/README.md) | Bulk SMS marketing, campaign admin action, personalization |
| `advertising/` | [advertising/README.md](advertising/README.md) | Banners, promotions, landing page integration |
| `templates/` | [templates/README.md](templates/README.md) | Template hierarchy, context variables, design system |
| `docs/` | [docs/mysql-guide.md](docs/mysql-guide.md) | MySQL commands, troubleshooting, backup/restore |

**How to use this documentation:** Start here for the big picture, then dive into any app README above for implementation details. Each app README includes a "Dependencies" section that links to related apps.

```
╔══════════════════════════════════════════════════════════════╗
║               🚗  CarDealTZ  —  Overview                    ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║   Customers ──►  Landing Page (vehicles)                     ║
║      │               ├── Banners (advertising)               ║
║      │               ├── Promotions (advertising)            ║
║      │               ├── Car Listings (vehicles)             ║
║      │               └── Chat Widget (chatbot)               ║
║      │                                                       ║
║      ├── OTP Login (accounts)  ──►  Book Appointment (leads) ║
║      │                                   │                   ║
║      │                                   └── SMS (notif.)    ║
║      │                                                       ║
║      └── Chat (chatbot)  ──►  Lead Created (leads)           ║
║                                                              ║
║   Staff ──► Staff Login (accounts) ──► Admin Panel           ║
║      ├── Manage Cars (vehicles)                              ║
║      ├── Manage Leads/Appointments (leads)                   ║
║      ├── Send Campaigns (campaigns)                          ║
║      ├── Create Ads (advertising)                            ║
║      └── View SMS Logs (notifications)                       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

**Stack:** Django 6.0 · MySQL 8.0 (or SQLite) · Tailwind CSS (CDN) · SendAfrica SMS API · Alpine.js · Jazzmin Admin Theme

---

## 📚 Table of Contents

- [Project Architecture](#-project-architecture)
- [How the Apps Connect](#-how-the-apps-connect)
- [Installation (Windows & Linux)](#-installation-windows--linux)
- [Quick Start (Linux/macOS)](#-quick-start-linuxmacos)
- [Quick Start (Windows)](#-quick-start-windows)
- [Seed Data](#-seed-data)
- [Understanding the Code](#-understanding-the-code)
- [8 Build Phases](#-8-build-phases)
- [SMS Integration (SendAfrica)](#-sms-integration-sendafrica)
- [Chatbot](#-chatbot)
- [Advertising Module](#-advertising-module)
- [API Endpoints](#-api-endpoints)
- [Environment Variables](#-environment-variables)
- [Key Design Decisions](#-key-design-decisions)
- [For Developers](#-for-developers)

---

## 🏗 Project Architecture

```
car-crm-django-fullstack/
│
├── car_crm/                  # Django PROJECT settings (the "control panel")
│   ├── settings.py           #   - All config: databases, apps, middleware
│   ├── urls.py               #   - Root URL routing (connects all apps)
│   ├── wsgi.py               #   - For production deployment
│   └── asgi.py               #   - For async/WebSocket deployment
│
├── accounts/                 # 🔐 USER AUTHENTICATION
│   ├── models.py             #   - CustomUser (phone-based, no username)
│   │                         #   - OTP (one-time password codes)
│   ├── views.py              #   - Staff login (phone + password)
│   │                         #   - Customer OTP login (send + verify)
│   ├── forms.py              #   - Login form, OTP forms with validation
│   ├── admin.py              #   - User & OTP management in /admin/
│   └── urls.py               #   - /login/, /otp/send/, /otp/verify/
│
├── vehicles/                 # 🚘 CAR INVENTORY
│   ├── models.py             #   - Car (make, model, year, price, status)
│   │                         #   - CarImage (multiple images per car)
│   ├── views.py              #   - Landing page (banners → promotions → cars)
│   │                         #   - Car detail page
│   ├── admin.py              #   - Car management with inline images
│   └── urls.py               #   - / (homepage), /car/<id>/
│
├── leads/                    # 📋 CUSTOMER LEADS & BOOKINGS
│   ├── models.py             #   - Lead (source tracking, status pipeline)
│   │                         #   - Appointment (test drive, call back, visit)
│   ├── views.py              #   - Booking flow (form → SMS → confirmation)
│   ├── admin.py              #   - Lead & appointment management
│   └── urls.py               #   - /book/
│
├── chatbot/                  # 💬 LIVE CHAT WIDGET
│   ├── models.py             #   - ChatSession, ChatMessage
│   ├── views.py              #   - JSON API (POST message → bot reply)
│   ├── bot.py                #   - Keyword-matching engine (Swahili + English)
│   ├── admin.py              #   - Chat history viewer
│   └── urls.py               #   - /message/, /history/<id>/
│
├── notifications/            # 📱 SMS GATEWAY (SendAfrica)
│   ├── models.py             #   - SmsLog (audit trail of all SMS)
│   ├── services.py           #   - send_sms() — THE ONLY SMS entry point
│   └── admin.py              #   - SMS log viewer
│
├── campaigns/                # 📣 BULK SMS MARKETING
│   ├── models.py             #   - Campaign, CampaignRecipient
│   ├── admin.py              #   - Create campaign, "Send Campaign" action
│   └── urls.py               #   - (admin-only, no public URLs)
│
├── advertising/              # 🎯 BANNERS & PROMOTIONS
│   ├── models.py             #   - Banner (hero slider images)
│   │                         #   - Promotion (featured/sale cars)
│   └── admin.py              #   - Create/manage banners and promotions
│
├── templates/                # 🎨 ALL HTML TEMPLATES
│   ├── base.html             #   - Master layout (nav, messages, footer)
│   ├── accounts/             #   - Login, OTP send, OTP verify
│   ├── vehicles/             #   - Landing page, car detail
│   ├── leads/                #   - Booking form
│   └── chatbot/widget.html   #   - Chat widget (included everywhere)
│
├── static/                   # 📦 Static files (CSS, JS, images)
├── media/                    # 🖼 User-uploaded images (gitignored)
│
├── .env                      # 🔒 Secret keys (NEVER commit this!)
├── .env.example              # 📝 Template for .env (safe to commit)
├── manage.py                 # 🎮 Django's command runner
├── requirements.txt          # 📦 Python dependencies
└── start.sh                  # 🚀 Quick start script (Linux/macOS)
```

---

## 🔗 How the Apps Connect

This is the most important section for understanding the project. Every app connects to others through **models** (Foreign Keys), **URLs** (links between pages), and **services** (function calls).

### Connection Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        CAR_CRM (settings.py)                    │
│  Configures all apps, database, middleware, templates, auth      │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐   ┌───────────────────┐   ┌───────────────┐
│   accounts    │◄──│     vehicles      │   │  advertising  │
│  (users/auth) │   │  (car inventory)  │   │(banners/promos)│
└───────┬───────┘   └────────┬──────────┘   └───────┬───────┘
        │                    │                      │
        │             ┌──────┴──────┐               │
        │             │             │               │
        ▼             ▼             ▼               │
┌─────────────────────────────────────────┐         │
│               leads                     │◄────────┘
│     (leads & appointments)              │
│   - Lead.customer -> CustomUser         │
│   - Lead.interested_car -> Car          │
│   - Appointment.lead -> Lead            │
│   - Appointment.car -> Car              │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│           notifications                 │
│         (SMS sending service)           │
│   - send_sms() called by:              │
│     • accounts.views (OTP code)         │
│     • leads.views (booking confirm)     │
│     • campaigns.admin (bulk SMS)        │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                  ▼
┌───────────────┐   ┌───────────────┐
│   chatbot     │   │   campaigns   │
│ (live chat)   │   │(SMS marketing)│
│ - Creates     │   │ - Uses send_  │
│   Lead from   │   │   sms() for   │
│   chat        │   │   bulk sends  │
└───────────────┘   └───────────────┘
```

### How Data Flows Through the System

#### Flow 1: A customer visits the website

```
Browser → GET / → vehicles.views.landing_page()
                  ├── Queries: Car.objects.filter(status='available')
                  ├── Queries: Banner.objects.filter(is_active=True)
                  ├── Queries: Promotion.objects.filter(is_active=True, ...)
                  └── Renders: templates/vehicles/landing.html
                      ├── Banner carousel (top)
                      ├── Hot Deals section (if promotions active)
                      ├── All Vehicles grid
                      └── Chat widget (bottom-right)
```

#### Flow 2: A customer logs in with OTP

```
Browser → GET /accounts/otp/send/ → accounts.views.customer_otp_send()
          │  Renders: otp_send.html (phone input form)
          │
User enters phone → POST → customer_otp_send()
          │  1. normalize_phone(phone) -> +2557xxxxxxxx
          │  2. Generate random 6-digit code
          │  3. OTP.objects.create(phone, code, expires_at=now+5min)
          │  4. send_sms(phone, "Your code is XXXXXX")
          │     └─► notifications.services.send_sms()
          │           └─► POST to SendAfrica API
          │           └─► SmsLog.objects.create(status='sent'/'failed')
          │  5. request.session['otp_phone'] = phone
          │  6. Redirect to /accounts/otp/verify/
          │
Redirect → GET /accounts/otp/verify/ → accounts.views.customer_otp_verify()
          │  Renders: otp_verify.html (6-digit code input)
          │
User enters code → POST → customer_otp_verify()
          │  1. Look up OTP where phone+code+not_used+not_expired
          │  2. If valid:
          │     a. otp.is_used = True (prevents replay)
          │     b. CustomUser.objects.get_or_create(phone=phone)
          │     c. login(request, user) — creates Django session
          │     d. Redirect to / (or back to booking if redirected)
          │  3. If invalid: show error message
```

#### Flow 3: A customer books a test drive

```
Browser → GET /leads/book/?car=3 → leads.views.book_appointment()
          │  Renders: book.html (pre-filled with car info)
          │
User fills form → POST → leads.views.book_appointment()
          │  1. Find or create Lead (get_or_create by phone)
          │  2. Create Appointment (lead, car, type, scheduled_at)
          │  3. send_sms(phone, "Your Test Drive for Toyota Hilux...")
          │     └─► notifications.services.send_sms()
          │  4. Redirect to / with success message
```

#### Flow 4: A staff member sends a marketing campaign

```
Admin clicks "Send Campaign" in /admin/campaigns/campaign/
          │  campaigns.admin.send_campaign_now()
          │  For each pending recipient:
          │    1. Personalize template: {full_name} → "Juma"
          │    2. send_sms(phone, personalized_message)
          │    3. Update recipient status (sent/failed)
          │    4. Sleep 150ms (rate limiting)
          │  Then: campaign.status = 'sent'
```

#### Flow 5: A customer chats with the bot

```
Browser → Chat widget opens → POST /chatbot/message/ (JSON)
          │  Body: {"message": "How much is the Prado?", "phone": "..."}
          │
chatbot.views.chat_message_view()
          │  1. Find or create ChatSession
          │  2. Store user message: ChatMessage.objects.create(...)
          │  3. Get bot reply: chatbot.bot.get_bot_reply(message)
          │     ├── "price" keyword → return price info
          │     ├── "test drive" → return booking link
          │     └── default → "I'll connect you with a sales rep"
          │  4. Store bot reply
          │  5. Return JSON: {"reply": "...", "session_id": ...}
          │
          │  If phone provided + booking intent:
          │    └─► Create Lead (source='chatbot')
```

---

## 💻 Installation (Windows & Linux)

### Prerequisites (Both Platforms)

| Requirement | Version | Check Command |
|-------------|---------|---------------|
| Python | 3.10+ | `python --version` or `python3 --version` |
| pip | (comes with Python) | `pip --version` |
| MySQL (optional) | 8.0+ | `mysql --version` |

### 📦 Windows Installation

#### Step 1: Install Python

1. Go to [python.org/downloads](https://python.org/downloads)
2. Download Python 3.12 or later
3. **IMPORTANT**: Check ✅ **"Add Python to PATH"** during installation
4. Open **Command Prompt** (cmd) or **PowerShell** and verify:
   ```cmd
   python --version
   pip --version
   ```

#### Step 2: Install MySQL (Optional — skip for SQLite)

1. Download MySQL Installer from [dev.mysql.com/downloads/installer](https://dev.mysql.com/downloads/installer/)
2. Choose **"MySQL Server 8.0"** during installation
3. Set root password (remember it!)
4. Or use **XAMPP** (easier): [apachefriends.org](https://www.apachefriends.org/)
   - Download XAMPP, install, start MySQL from the control panel
   - Default: root user, no password, port 3306

#### Step 3: Download the Project

```cmd
REM Option A: If you have Git installed
git clone git@github.com:troubleman96/car-crm-django-fullstack.git
cd car-crm-django-fullstack

REM Option B: Download ZIP from GitHub
REM Extract the ZIP file and open that folder in cmd
```

#### Step 4: Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` appear at the start of your command prompt line.

#### Step 5: Install Dependencies

```cmd
pip install -r requirements.txt
```

If you get a `mysqlclient` error on Windows, install the precompiled wheel:
```cmd
pip install mysqlclient‑1.4.6‑cp312‑cp312‑win_amd64.whl
```
Or find the right wheel at [pypi.org/project/mysqlclient](https://pypi.org/project/mysqlclient/#files)

If you're NOT using MySQL, just install the rest:
```cmd
pip install django pymysql django-jazzmin
```

#### Step 6: Configure Environment

```cmd
REM Copy the example env file
copy .env.example .env

REM Edit .env with Notepad or any text editor
notepad .env
```

Set these values in `.env`:
```ini
DJANGO_SECRET_KEY=your-random-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=car_crm
DB_USER=root
DB_PASSWORD=your-mysql-password    # Leave empty if no password
DB_HOST=localhost
DB_PORT=3306
SENDAFRICA_API_KEY=               # Leave empty to test without SMS
```

#### Step 7: Choose Database

**Option A — SQLite (easier, no MySQL needed):**
```cmd
set USE_MYSQL=False
```

**Option B — MySQL (if you installed MySQL or XAMPP):**
```cmd
REM First create the database
mysql -u root -p -e "CREATE DATABASE car_crm CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
```

#### Step 8: Migrate & Seed

```cmd
python manage.py migrate
python manage.py seed_data
```

If you get a MySQL connection error, switch to SQLite:
```cmd
set USE_MYSQL=False
python manage.py migrate
python manage.py seed_data
```

#### Step 9: Run the Server

```cmd
python manage.py runserver
```

Open your browser to **http://localhost:8000**

---

### 🐧 Quick Start (Linux/macOS)

```bash
# 1. Clone the repo
git clone git@github.com:troubleman96/car-crm-django-fullstack.git
cd car-crm-django-fullstack

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env   # Edit with your settings

# 5. Set up database (SQLite)
export USE_MYSQL=False

# 6. Migrate and seed
python manage.py migrate
python manage.py seed_data

# 7. Run
python manage.py runserver
```

---

## 🌱 Seed Data

The `seed_data` command (`python manage.py seed_data`) creates realistic sample data so you don't start with an empty database:

### Staff Users (can log in at /accounts/login/)

| Full Name | Phone | Password | Role |
|-----------|-------|----------|------|
| Admin User | +255711000001 | admin123 | Full admin access |
| Marketing User | +255711000002 | marketing123 | Marketing campaigns |
| Sales User | +255711000003 | sales123 | Lead management |
| Support User | +255711000004 | support123 | Chat support |

### Customer Users (log in via OTP at /accounts/otp/send/)

| Full Name | Phone | Notes |
|-----------|-------|-------|
| Juma Mwangi | +255712000001 | Has a lead and appointment |
| Aisha Mohamed | +255712000002 | Has a lead and appointment |

### Sample Cars

| # | Make | Model | Year | Price (TZS) |
|---|------|-------|------|-------------|
| 1 | Toyota | Hilux | 2023 | 95,000,000 |
| 2 | Toyota | Land Cruiser Prado | 2022 | 180,000,000 |
| 3 | Nissan | X-Trail | 2023 | 65,000,000 |
| 4 | Suzuki | Swift | 2024 | 28,000,000 |
| 5 | BMW | X5 | 2021 | 150,000,000 |
| 6 | Mercedes-Benz | C-Class | 2023 | 85,000,000 |
| 7 | Honda | CR-V | 2022 | 72,000,000 |
| 8 | Mitsubishi | Outlander | 2023 | 58,000,000 |

Also creates: 3 leads, 2 appointments, 2 SMS logs, 1 chat session, 1 campaign.

---

## 📖 Understanding the Code

Every Python file in this project has **detailed educational comments** explaining:

- **WHAT** the code does
- **WHY** it's written that way
- **HOW** it connects to other parts of the project

Read the comments in order:

1. **`car_crm/settings.py`** — Start here. Understand all the project configuration.
2. **`car_crm/urls.py`** — See how all the apps are connected via URLs.
3. **Each app's `models.py`** — Understand the database structure.
4. **Each app's `views.py`** — See the logic that handles requests.
5. **Each app's `forms.py`** — Understand form validation.
6. **Each app's `admin.py`** — See how data is managed in the admin panel.
7. **Templates (.html)** — See how the UI is rendered.

### Key Files to Read (in order of importance)

| File | Why It's Important |
|------|-------------------|
| `car_crm/settings.py` | All project configuration in one place |
| `accounts/models.py` | The custom user model — core of the auth system |
| `accounts/views.py` | Two authentication flows (OTP + password) |
| `notifications/services.py` | The SMS gateway — how messages are sent |
| `vehicles/views.py` | The landing page — entry point for all visitors |
| `leads/views.py` | The booking flow — creates leads + appointments |
| `chatbot/bot.py` | The bot engine — keyword matching logic |
| `chatbot/views.py` | The chat API — how the widget communicates |
| `campaigns/admin.py` | The bulk SMS action — how campaigns are sent |
| `templates/base.html` | The master layout — every page extends this |

---

## 🏗 8 Build Phases

This project was built incrementally in 8 ordered phases. Each phase adds a complete feature:

### Phase 1 — Project Skeleton
- Django project with MySQL/SQLite config (env-driven)
- All 8 apps created, static/media directories, Jazzmin admin theme
- Base template with Tailwind CSS

### Phase 2 — Accounts App
- `CustomUser` — phone as USERNAME_FIELD (no username, no email)
- `OTP` model with 5-minute expiry, single-use codes
- **Staff login**: phone + password → authenticate → session
- **Customer OTP login**: phone → SMS code → verify → auto-create user
- 4 Django Groups (Admin, Marketing, Sales, Support) via data migration
- Phone normalization (0628587749 → +255628587749)

### Phase 3 — Vehicles App
- `Car` model: make, model, year, price, status, description
- `CarImage` model: car FK, image_url, is_primary
- Landing page: lists available cars with images
- Car detail page: full info + thumbnail gallery
- Admin with CarImageInline

### Phase 4 — Notifications App
- `send_sms()` service — THE single gateway to SendAfrica API
- Phone normalization (07xx → +2557xx for Tanzania)
- `SmsLog` — every SMS attempt logged for audit
- Never raises exceptions (returns True/False)
- Error handling: URLError, HTTPError, OSError, JSONDecodeError

### Phase 5 — Leads App
- `Lead` model: customer link, phone, source tracking, status pipeline
- `Appointment` model: type (test_drive/call_back/showroom_visit), datetime
- Booking flow: pick car → select type → enter phone → confirm → SMS
- Uses `get_or_create` to find existing leads by phone
- Admin with AppointmentInline

### Phase 6 — Chatbot App
- `ChatSession`, `ChatMessage` models for chat history
- Mock AI bot (`bot.py`) — keyword matching with Swahili support
- Chat widget (Alpine.js) — floating button, slide-up box, real-time fetch
- JSON API: POST `/chatbot/message/` → returns bot reply
- Auto-creates Lead from chat when phone + booking intent detected

### Phase 7 — Campaigns App
- `Campaign` model: name, message_template, status pipeline
- `CampaignRecipient` model: links campaign to leads
- Admin action "Send Campaign" — iterates recipients, personalizes, sends SMS
- 150ms delay between sends (respects SendAfrica rate limit)
- `{full_name}` / `{phone}` personalization placeholders

### Phase 8 — Advertising App
- `Banner` model: hero slider images for the landing page
- `Promotion` model: featured/sale/new/hot badges with discount %
- Landing page section order: banners → hot deals → all vehicles
- Admin with toggle-able active state and ordering

---

## 📱 SMS Integration (SendAfrica)

All SMS in the system goes through ONE function: `notifications/services.py:send_sms()`.

### How It Works

```
Your Code → send_sms(phone, message)
                │
                ├── normalize_phone("0628587749")
                │       └── Returns "+255628587749"
                │
                ├── POST https://api.sendafrica.online/v1/sms/
                │   Headers: X-API-Key = your-key
                │   Body: {"to": "+255628587749", "message": "..."}
                │
                ├── If success (HTTP 200 + {"success": true}):
                │   └── SmsLog.objects.create(status='sent')
                │   └── Return True
                │
                └── If failure:
                    └── SmsLog.objects.create(status='failed')
                    └── Return False (never crashes!)
```

### Set up

```bash
# Get an API key from https://sendafrica.online
# Then set it in your .env file:
SENDAFRICA_API_KEY=
```

### Where SMS Is Sent

| Event | Trigger | Message |
|-------|---------|---------|
| **OTP Login** | Customer enters phone on /accounts/otp/send/ | "Your verification code is 482910. Valid for 5 minutes." |
| **Booking Confirmation** | Customer submits booking on /leads/book/ | "Your Test Drive for Toyota Hilux is booked for Friday, 14 June at 10:00." |
| **Campaign Blast** | Admin clicks "Send Campaign" in admin | Personalized template: "Hello {full_name}! Visit our showroom..." |

### Phone Format

This CRM is for Tanzania, so only these formats work:

| Input | Normalized | Valid? |
|-------|-----------|--------|
| 0712345678 | +255712345678 | ✅ |
| 0628587749 | +255628587749 | ✅ |
| +255712345678 | +255712345678 | ✅ |
| 255712345678 | +255712345678 | ✅ |
| 071234567 | +25571234567 | ❌ (too short) |

---

## 💬 Chatbot

The chatbot widget appears on every public page (bottom-right corner).

### Technology

- **Frontend**: Alpine.js (lightweight JavaScript framework, no build step)
- **Backend**: Django JSON API at `/chatbot/message/`
- **Bot Engine**: Keyword matching with regex in `chatbot/bot.py`

### How the Widget Works

```
1. User clicks the blue chat button → chat box slides up
2. User types a message → Alpine.js sends POST to /chatbot/message/
   Body: {"message": "Hello", "session_id": null, "phone": ""}
3. Server:
   a. Finds or creates ChatSession
   b. Saves user message
   c. Calls get_bot_reply("Hello")
   d. Returns JSON: {"reply": "Hi! Welcome...", "session_id": 5}
4. Widget displays the bot's reply
5. If user shares phone + shows booking intent:
   → Server auto-creates a Lead (source='chatbot')
```

### Bot Keywords (English & Swahili)

| Keyword | Response |
|---------|----------|
| hi, hello, habari | Greeting + offers help |
| price, cost, bei | "Our cars range from TZS 28M to TZS 180M..." |
| toyota, nissan, bmw, etc. | Info about that specific make |
| test drive | Redirects to booking page |
| book, appointment | "Visit /leads/book/ to schedule" |
| phone, call, simu | Asks for phone number |
| thanks, asante | You're welcome |
| help, saida | Lists available commands |

### Swahili Support

The bot understands common Swahili words:
- **habari** = hello/how are you
- **bei** = price
- **asante** = thank you
- **sawa** = okay
- **saida** = help
- **simu** = phone

---

## 🎯 Advertising Module

Create promotional content that displays on the landing page.

### Banners (Hero Slider)

Auto-rotating full-width banners at the top of the homepage.

**Add in admin**: `/admin/advertising/banner/add/`

| Field | Example | Purpose |
|-------|---------|---------|
| Title | "End of Year Sale" | Headline text |
| Subtitle | "Up to 20% off SUVs" | Supporting text |
| Image URL | `https://.../car-banner.jpg` | Background image |
| Link URL | `/leads/book/` | Where "Learn More" goes |
| Active | ✅ | Toggle visibility |
| Order | 0 | Display sequence |

### Promotions (Hot Deals)

Cars with special badges and optional discounts.

**Add in admin**: `/admin/advertising/promotion/add/`

| Label | Badge Color | Use Case |
|-------|------------|----------|
| Featured | Blue | General promotion |
| Sale | Red | Discount event |
| New | Green | New arrivals |
| Hot Deal | Orange | Urgent promotion |

Promotions appear in a **"Hot Deals"** section above the regular car listing. If a discount is set, both the original price (strikethrough) and the discounted price show.

---

## 🌐 API Endpoints

### Public Pages

| Method | URL | Description | View Function |
|--------|-----|-------------|---------------|
| GET | `/` | Landing page with banners, promotions, cars | `vehicles.views.landing_page` |
| GET | `/car/<id>/` | Car detail page | `vehicles.views.car_detail` |
| GET | `/accounts/login/` | Staff login form (phone + password) | `accounts.views.staff_login_view` |
| POST | `/accounts/login/` | Staff login submit | `accounts.views.staff_login_view` |
| GET | `/accounts/logout/` | Logout | `accounts.views.staff_logout_view` |
| GET | `/accounts/otp/send/` | Customer OTP form (enter phone) | `accounts.views.customer_otp_send` |
| POST | `/accounts/otp/send/` | Request OTP code (sends SMS) | `accounts.views.customer_otp_send` |
| GET | `/accounts/otp/verify/` | OTP verify form (enter code) | `accounts.views.customer_otp_verify` |
| POST | `/accounts/otp/verify/` | Verify OTP code (logs in) | `accounts.views.customer_otp_verify` |
| GET | `/leads/book/` | Booking form | `leads.views.book_appointment` |
| POST | `/leads/book/` | Submit booking (sends SMS) | `leads.views.book_appointment` |
| POST | `/chatbot/message/` | Chat API (JSON) | `chatbot.views.chat_message_view` |
| GET | `/chatbot/history/<id>/` | Chat history (JSON) | `chatbot.views.chat_session_history` |

### Admin Pages (Django Admin)

| URL | What You Can Do |
|-----|-----------------|
| `/admin/` | Dashboard with all models |
| `/admin/accounts/customuser/` | Manage users (staff + customers) |
| `/admin/accounts/otp/` | View OTP codes (read-only) |
| `/admin/vehicles/car/` | Add/edit cars with images |
| `/admin/leads/lead/` | Manage leads and assign to staff |
| `/admin/leads/appointment/` | View/manage appointments |
| `/admin/chatbot/chatsession/` | View chat history |
| `/admin/notifications/smslog/` | View SMS delivery logs |
| `/admin/campaigns/campaign/` | Create and send campaigns |
| `/admin/advertising/banner/` | Create homepage banners |
| `/admin/advertising/promotion/` | Create car promotions |
| `/admin/auth/group/` | Manage roles & permissions |

---

## 🔐 Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DJANGO_SECRET_KEY` | (dev key) | ✅ Production | Used for cryptographic signing. Generate with: `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DJANGO_DEBUG` | `True` | ⚠️ Turn off in production | When True, shows detailed error pages |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | ✅ Production | Comma-separated domain names |
| `DB_NAME` | `car_crm` | Only for MySQL | MySQL database name |
| `DB_USER` | `root` | Only for MySQL | MySQL username |
| `DB_PASSWORD` | (empty) | Only for MySQL | MySQL password |
| `DB_HOST` | `localhost` | Only for MySQL | MySQL host address |
| `DB_PORT` | `3306` | Only for MySQL | MySQL port |
| `USE_MYSQL` | `True` | ❌ | Set to `False` to use SQLite instead |
| `SENDAFRICA_API_KEY` | (empty) | Only for SMS | SendAfrica SMS API key |

---

## 🎯 Key Design Decisions

| Decision | Why We Did It |
|----------|---------------|
| **Phone as username** | Tanzanian car buyers use phones, not emails |
| **Custom User model** | Django's default User has username/email — we don't need those |
| **OTP for customers** | No password to remember; SMS is universal in Tanzania |
| **Staff login with password** | Employees need stronger auth, shared phones |
| **MySQL + SQLite fallback** | MySQL in production, SQLite for classmates without MySQL |
| **One `send_sms()` function** | Single gateway means easy to swap providers, add logging |
| **No Celery/Redis** | For 50-200 SMS, synchronous sending is fine for a class project |
| **Django Groups** | Built-in, works with admin permissions — no custom code needed |
| **Tailwind via CDN** | Zero build tools — just write HTML classes |
| **Alpine.js for chat** | Lightweight, no npm/webpack — just add a `<script>` tag |
| **SendAfrica API** | Supports Tanzania numbers, affordable, simple REST API |
| **`seed_data` command** | One command to get a fully working demo with realistic data |
| **Jazzmin admin theme** | Makes Django admin look like a modern SaaS product |
| **Phone normalization** | Users enter 07xx, app converts to +2557xx for the API |

---

## 👨‍💻 For Developers

### Run Tests

```bash
python manage.py test
```

### Add a New Model

```python
# 1. In your app's models.py:
class MyModel(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

# 2. Create and run migration:
# python manage.py makemigrations yourapp
# python manage.py migrate

# 3. Register in admin.py:
from django.contrib import admin
from .models import MyModel

@admin.register(MyModel)
class MyModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
```

### Send an SMS from Anywhere

```python
from notifications.services import send_sms

# Returns True if sent, False if failed
success = send_sms('+255712345678', 'Hello from CarDealTZ!')
if not success:
    print('SMS failed — check the SmsLog for details')
```

### Query the Most Recent Leads

```python
from leads.models import Lead

# Last 10 leads
recent_leads = Lead.objects.order_by('-created_at')[:10]

# Filter by status
new_leads = Lead.objects.filter(status='new')

# Filter by assigned staff
my_leads = Lead.objects.filter(assigned_to__phone='+255711000001')
```

---

## 📝 License

Student project — Tanzania car dealership CRM system. Built for educational purposes.

---

*Generated with ❤️ for the CarDealTZ project. See individual app README.md files for detailed documentation of each component.*
