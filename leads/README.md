# Leads App — CRM Core: Leads & Appointments

The heart of the CRM. Tracks potential customers (leads) and their appointments (test drives, call backs, showroom visits).

---

## Models

### Lead

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto |
| `customer` | FK -> CustomUser, nullable | Linked once they OTP-verify |
| `phone` | VARCHAR(15) | Primary contact |
| `full_name` | VARCHAR(150), nullable | Customer name |
| `source` | ENUM('website','chatbot','campaign','walk_in') | How the lead was acquired |
| `interested_car` | FK -> Car, nullable | Which car they're interested in |
| `status` | ENUM('new','contacted','qualified','won','lost') | Sales pipeline stage |
| `assigned_to` | FK -> CustomUser (staff), nullable | Sales rep assigned |
| `created_at` | DATETIME, auto | Created |
| `updated_at` | DATETIME, auto-update | Last modified |

### Appointment

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto |
| `lead` | FK -> Lead (CASCADE) | Parent lead |
| `car` | FK -> Car, nullable | Car for test drive |
| `type` | ENUM('test_drive','call_back','showroom_visit') | Appointment type |
| `scheduled_at` | DATETIME | When it's happening |
| `status` | ENUM('pending','confirmed','completed','cancelled') | State |
| `notes` | TEXT, nullable | Staff notes |
| `created_at` | DATETIME, auto | Created |

---

## Booking Flow

The public booking flow goes through these steps:

```
1. Visitor lands on / or car detail page
2. Clicks "Book Test Drive" / "Book" in nav
3. /leads/book/ —> optionally preselects a car via ?car=<id>
4. Fills form: phone number, appointment type, preferred date/time
5. Submits POST -> Lead created (or found if existing phone)
6. Appointment created with status='confirmed'
7. Confirmation SMS sent via SendAfrica
8. Redirects to landing page with success message
```

If the customer already exists (same phone number), the existing Lead is reused.

### Lead Source Mapping

| Entry Point | Source |
|-------------|--------|
| Booking form on website | `website` |
| Chatbot (captures phone + booking intent) | `chatbot` |
| Campaign (marketing blast) | `campaign` |
| Admin-created | `walk_in` |

---

## Admin

`LeadAdmin` with `AppointmentInline`:

- List display: full_name, phone, source, status, interested_car, assigned_to, created_at
- Filters: source, status, car make
- Search: full_name, phone
- Inline appointments on lead edit page

`AppointmentAdmin`:

- List display: lead, car, type, scheduled_at, status, created_at
- Filters: type, status, scheduled_at
- Search: lead name/phone

---

## URL Endpoints

| URL | View | Methods | Auth |
|-----|------|---------|------|
| `/leads/book/` | `book_appointment` | GET, POST | None (public) |

---

## SMS Integration

After a successful booking, a confirmation SMS is sent automatically:

> "Your Test Drive for Toyota Hilux is booked for Friday, 14 June at 10:00."

The SMS is sent via `notifications.services.send_sms()` — no direct SendAfrica calls here.

---

## Relations

```
Lead 1---* Appointment
Lead *---1 CustomUser (customer, nullable)
Lead *---1 Car (interested_car, nullable)
Lead *---1 CustomUser (assigned_to, nullable)
Appointment *---1 Car (nullable)
```
