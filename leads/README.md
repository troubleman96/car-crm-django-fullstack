# Leads App — Customer Leads & Appointment Booking

> **Quick links:** [`vehicles` app](../vehicles/README.md) · [`notifications` app](../notifications/README.md) · [`chatbot` app](../chatbot/README.md) · [`campaigns` app](../campaigns/README.md) · [leads templates](../templates/leads/README.md) · [root README](../README.md)

## Overview

The `leads` app manages the **sales pipeline** — tracking potential customers (leads) and their scheduled appointments (test drives, call-backs, showroom visits). It provides a public **booking form** where website visitors can book appointments, which automatically creates or links to a lead record, schedules the appointment, and sends a confirmation SMS. This app connects the `vehicles` inventory to real customer interactions.

---

## Models

### Lead

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `customer` | `ForeignKey(settings.AUTH_USER_MODEL)` | `on_delete=SET_NULL, null=True, blank=True` | Links to a registered `CustomUser` (optional — leads can be anonymous) |
| `phone` | `CharField(max_length=15)` | Required | The lead's phone number (primary contact method) |
| `full_name` | `CharField(max_length=150)` | `null=True, blank=True` | Optional display name |
| `source` | `CharField(max_length=10)` | `choices=SOURCE_CHOICES, default='website'` | How the lead entered the system |
| `interested_car` | `ForeignKey('vehicles.Car')` | `on_delete=SET_NULL, null=True, blank=True` | The car the lead is interested in (optional) |
| `status` | `CharField(max_length=10)` | `choices=STATUS_CHOICES, default='new'` | Current stage in the sales pipeline |
| `assigned_to` | `ForeignKey(settings.AUTH_USER_MODEL)` | `on_delete=SET_NULL, null=True, blank=True, related_name='assigned_leads'` | The salesperson handling this lead |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Created timestamp |
| `updated_at` | `DateTimeField` | `auto_now=True` | Last updated timestamp |

**SOURCE_CHOICES:** `website`, `chatbot`, `campaign`, `walk_in`

**STATUS_CHOICES:** `new` → `contacted` → `qualified` → `won` / `lost`

**Meta:** `ordering = ['-created_at']` — newest leads first.

### Appointment

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `lead` | `ForeignKey(Lead)` | `on_delete=CASCADE, related_name='appointments'` | The lead this appointment belongs to |
| `car` | `ForeignKey('vehicles.Car')` | `on_delete=SET_NULL, null=True, blank=True` | The specific car for this appointment (optional for call-backs) |
| `type` | `CharField(max_length=20)` | `choices=TYPE_CHOICES` | Appointment type |
| `scheduled_at` | `DateTimeField` | Required | When the appointment is scheduled |
| `status` | `CharField(max_length=10)` | `choices=STATUS_CHOICES, default='pending'` | Appointment status |
| `notes` | `TextField` | `null=True, blank=True` | Staff notes about the appointment |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Created timestamp |

**TYPE_CHOICES:** `test_drive`, `call_back`, `showroom_visit`

**STATUS_CHOICES:** `pending` → `confirmed` → `completed` / `cancelled`

**Meta:** `ordering = ['-scheduled_at']` — soonest appointments first.

---

## How It Works — Booking Flow

### Full Booking Flow (Step by Step)

```
User clicks "Book Test Drive" on a car card
  (URL: /leads/book/?car=5)
         │
         ▼
  GET /leads/book/   ← view pre-selects car_id=5
         │
         ▼
  Booking form renders with:
    - Pre-selected car (from ?car= query param)
    - All available cars in dropdown
    - Phone, appointment type, date/time fields
         │
         ▼
  User fills form and submits (POST)
         │
         ▼
  book_appointment(request) view processes:
         │
    ├─ 1. Extract & clean form data
    │      phone, appointment_type, car_id, scheduled_at
    │
    ├─ 2. Validate phone (required)
    │      └─ If missing → re-render form with error
    │
    ├─ 3. Look up car (optional)
    │      interested_car = Car.objects.filter(id=car_id).first()
    │      └─ If invalid ID, silently treats as "no car selected"
    │
    ├─ 4. Find or create Lead
    │      Lead.objects.get_or_create(
    │          phone=phone,
    │          defaults={'source': 'website', 'interested_car': ...}
    │      )
    │      └─ Uses phone as unique identifier
    │      └─ If returning customer, uses existing lead
    │
    ├─ 5. Parse scheduled datetime
    │      scheduled_at = timezone.datetime.fromisoformat(scheduled_at_str)
    │      └─ Falls back to "tomorrow" if parsing fails
    │
    ├─ 6. Create Appointment
    │      Appointment.objects.create(
    │          lead=lead,
    │          car=interested_car,
    │          type=appointment_type,
    │          scheduled_at=scheduled_at,
    │          status='confirmed'  ← auto-confirmed
    │      )
    │
    ├─ 7. Send SMS confirmation
    │      send_sms(phone, f"Your {type} for {car} is booked for {datetime}...")
    │      └─ Uses notifications/services.py
    │
    ├─ 8. Flash success message
    │      messages.success(request, 'Appointment booked!')
    │
    └─ 9. Redirect to landing page
           return redirect('vehicles:landing')
```

### Key Design Decisions

- **`get_or_create` for leads** — A returning customer with the same phone number does NOT create a duplicate Lead. All appointment history stays under one Lead record.
- **Phone as primary identifier** — Customers don't need an account to book. Their phone number is the key that ties all their interactions together.
- **`interested_car` on Lead** — Even if no specific car is selected during booking, the Lead records which car the customer was looking at (from the `?car=` parameter).
- **Status auto-set to `confirmed`** — Booked appointments start as `confirmed` (not `pending`), since the customer initiated the booking themselves.
- **SMS sent synchronously** — The confirmation SMS is sent during the request. For large volumes, this should be moved to a task queue.

---

## URLs

| URL Pattern | View Function | Name | Description |
|-------------|---------------|------|-------------|
| `/leads/book/` | `book_appointment` | `leads:book` | Booking form (GET) and processing (POST). Optional `?car=ID` query param pre-selects a car. |

---

## Admin

Registered in `leads/admin.py`:

### LeadAdmin
- **List columns:** `full_name`, `phone`, `source`, `status`, `interested_car`, `assigned_to`, `created_at`
- **Filters:** `source`, `status`, `interested_car__make`
- **Search:** `full_name`, `phone`
- **Inline:** `AppointmentInline` — shows all appointments on the Lead edit page

### AppointmentAdmin
- **List columns:** `lead`, `car`, `type`, `scheduled_at`, `status`, `created_at`
- **Filters:** `type`, `status`, `scheduled_at`
- **Search:** `lead__full_name`, `lead__phone`

### AppointmentInline (TabularInline)
- Shown on the Lead admin page
- `extra = 0` — no extra blank rows
- `readonly_fields = ['created_at']`

---

## Dependencies

- **`vehicles/models.py`** — `Lead.interested_car` and `Appointment.car` are ForeignKeys to `Car`. The booking view queries `Car.objects.filter(status='available')`.
- **`accounts/models.py`** — `Lead.customer` and `Lead.assigned_to` are ForeignKeys to `CustomUser` (via `settings.AUTH_USER_MODEL`).
- **`notifications/services.py`** — The booking view imports `send_sms()` to send confirmation messages.
- **`chatbot/views.py`** — The chatbot creates `Lead` records from chat conversations, using the same `Lead.objects.get_or_create()` pattern.
