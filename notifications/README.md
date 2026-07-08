# Notifications App — Central SMS Service

## Overview

The `notifications` app is the **central SMS sending service** for the entire CRM. It provides two key utilities used by every other app: `normalize_phone()` for converting Tanzanian phone numbers to a standard international format, and `send_sms()` for sending text messages via the **SendAfrica API**. Every SMS send attempt is recorded in the `SmsLog` model for audit purposes. This app **never raises exceptions** to its callers — it always returns `True`/`False` and logs failures gracefully.

---

## Models

### SmsLog

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `phone` | `CharField(max_length=15)` | Required | The normalized recipient phone number (e.g. `+255712345678`) |
| `message` | `TextField` | Required | The full SMS body text |
| `status` | `CharField(max_length=10)` | `choices=STATUS_CHOICES, default='sent'` | Delivery status: `sent`, `delivered`, `failed` |
| `provider_message_id` | `CharField(max_length=64)` | `null=True, blank=True` | The message ID returned by SendAfrica (for looking up delivery reports) |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Timestamp of the send attempt |

**Meta:** `ordering = ['-created_at']` — newest entries first.

---

## Core Services — `services.py`

### `normalize_phone(phone: str) -> str`

Converts any common Tanzanian phone number format to the standard international format `+2557XXXXXXXX`.

**Input/Output Examples:**

| Input | Output |
|-------|--------|
| `0712345678` | `+255712345678` |
| `255712345678` | `+255712345678` |
| `+255712345678` | `+255712345678` |
| `0712 345 678` | `+255712345678` |
| `255-712-345-678` | `+255712345678` |
| `+255 712 345 678` | `+255712345678` |
| `712345678` (bare, no prefix) | `+255712345678` |

**Algorithm (step by step):**
1. Strip whitespace, dashes, and parentheses using `re.sub(r'[\s\-\(\)]', '', phone)`.
2. If starts with `0`, replace the leading `0` with `+255` (e.g. `0712...` → `+255712...`).
3. Else if starts with `255` (without `+`), prepend `+`.
4. If still doesn't start with `+`, prepend `+255` as fallback.

**Note:** This performs format normalisation, NOT full validation. It doesn't check that the number has exactly 9 digits after the country code or that it starts with a valid Tanzanian prefix (7XX).

### `send_sms(phone: str, message: str) -> bool`

Sends an SMS via the SendAfrica API. The complete request-response cycle:

```
send_sms(phone, message)
    │
    ├─ 1. Normalize phone → "+2557XXXXXXXX"
    │
    ├─ 2. Build JSON payload:
    │      { "to": "+2557XXXXXXXX", "message": "..." }
    │
    ├─ 3. POST to SENDAFRICA_BASE_URL/v1/sms/
    │      Headers:
    │        X-API-Key: <SENDAFRICA_API_KEY>
    │        Content-Type: application/json
    │      Timeout: 10 seconds
    │
    ├─ 4. Check response:
    │      ├─ {"success": true, "data": {"message_id": "..."}}
    │      │     → Create SmsLog (status='sent')
    │      │     → Log info
    │      │     → Return True
    │      │
    │      └─ {"success": false, "error": {...}}
    │            → Create SmsLog (status='failed')
    │            → Log warning
    │            → Return False
    │
    └─ 5. Catch errors (network, timeout, JSON parse):
          → Create SmsLog (status='failed')
          → Log error
          → Return False
```

**Key design decisions:**

- **Never raises exceptions** — All errors (network failures, timeouts, HTTP errors, invalid JSON) are caught and translated to a `False` return. Callers never need `try/except`.
- **Always logs to SmsLog** — Every send attempt creates an `SmsLog` row, whether it succeeds or fails. This provides a complete audit trail.
- **Rate limiting is caller's responsibility** — The function itself doesn't rate-limit. The campaigns app adds a 150ms delay between sends when iterating recipients.

---

## Where SMS is Used

| Feature | App | Sender | Message Content |
|---------|-----|--------|-----------------|
| OTP Login | `accounts` | `customer_otp_send` | "Your verification code is 482910. Valid for 5 minutes." |
| Booking Confirmation | `leads` | `book_appointment` | "Your Test Drive for Toyota Hilux is booked for Friday, 14 June at 10:00. Thank you!" |
| Campaign Blasts | `campaigns` | `send_campaign_now` | Personalized template: "Hello {full_name}! Visit our showroom..." |

---

## Configuration

Settings in `car_crm/settings.py`:

```python
SENDAFRICA_API_KEY = os.environ.get('SENDAFRICA_API_KEY', '')
SENDAFRICA_BASE_URL = 'https://api.sendafrica.online'
```

The API key is loaded from the `.env` file (never committed to git):

```
SENDAFRICA_API_KEY=687c72abc476d89ae3584f72c207b223beb84086e51071d8ea21f60833a10172
```

To use a different SMS provider, only `services.py` needs to change — every app calls `send_sms()` through this single interface.

---

## Admin

Registered in `notifications/admin.py`:

### SmsLogAdmin
- **List columns:** `phone`, `message_preview`, `status`, `provider_message_id`, `created_at`
- **Filter:** `status`
- **Search:** `phone`, `message`
- **All fields read-only** — SmsLog is an immutable audit record
- **Custom column:** `message_preview` — truncates long messages to 60 characters

---

## Dependencies

- **`accounts/forms.py`** — imports `normalize_phone()` for phone validation during login.
- **`accounts/views.py`** — imports `send_sms()` and `normalize_phone()` for OTP delivery.
- **`leads/views.py`** — imports `send_sms()` for booking confirmation SMS.
- **`campaigns/admin.py`** — imports `send_sms()` for bulk campaign sending.
- **`campaigns/models.py`** — `CampaignRecipient.sms_log` is a ForeignKey to `SmsLog`.
- **`car_crm/settings.py`** — provides `SENDAFRICA_API_KEY` and `SENDAFRICA_BASE_URL`.
