# Notifications App — SMS Gateway (SendAfrica)

Thin wrapper around the SendAfrica SMS API. This is the **ONLY** app that calls the SendAfrica API — all other apps import `send_sms()` from here.

---

## Core Service: `send_sms()`

**File:** `notifications/services.py`

```python
from notifications.services import send_sms

success = send_sms(phone="0712345678", message="Hello from CarDealTZ!")
# Returns: True (accepted by API) or False (any failure)
```

### Behavior

| Scenario | Returns | Logged As |
|----------|---------|-----------|
| API accepts message | `True` | `status='sent'` with provider_message_id |
| API rejects (invalid phone, no credits) | `False` | `status='failed'` |
| Network error / timeout | `False` | `status='failed'` |
| JSON decode error | `False` | `status='failed'` |

**Never raises exceptions.** The calling code (OTP login, booking, campaigns) will not crash if SMS fails. Always check the return value if you need to know the outcome.

### Phone Normalization

```python
normalize_phone("0712345678")     # -> "+255712345678"
normalize_phone("255712345678")   # -> "+255712345678"
normalize_phone("+255712345678")  # -> "+255712345678"
normalize_phone("255 71 234 5678") # -> "+255712345678"
```

Only Tanzania numbers (07xx, 06xx prefixes, or +255) are accepted.

---

## Model: SmsLog

Every SMS attempt is logged here:

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto |
| `phone` | VARCHAR(15) | Recipient phone |
| `message` | TEXT | SMS content |
| `status` | ENUM('sent','delivered','failed') | Delivery status |
| `provider_message_id` | VARCHAR(64), nullable | SendAfrica message_id |
| `created_at` | DATETIME, auto | When the SMS was sent |

---

## Configuration

| Env Variable | Required | Description |
|-------------|----------|-------------|
| `SENDAFRICA_API_KEY` | Yes | From SendAfrica dashboard (Settings > API Keys) |
| `SENDAFRICA_BASE_URL` | No (default) | `https://api.sendafrica.online` |

---

## Where SMS Is Sent

| Feature | File | Message Example |
|---------|------|-----------------|
| OTP Login | `accounts/views.py:customer_otp_send` | "Your verification code is 482910. Valid for 5 minutes." |
| Booking confirmation | `leads/views.py:book_appointment` | "Your Test Drive for Toyota Hilux is booked for Friday, 14 June at 10:00." |
| Campaign blast | `campaigns/admin.py:send_campaign_now` | Template-based, personalized per lead |

---

## SendAfrica API Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/sms/` | POST | Send SMS |
| `/v1/credits/balance` | GET | Check balance |
| `/v1/payments/` | POST | Top up credits |
| `/v1/packages` | GET | List credit packages |

**Auth:** `X-API-Key` header with your API key.

**Rate Limit:** 60/min (Free), 600/min (Pro), 6000/min (Enterprise).

For full docs, see `sendafrica-docs.md` (the developer guide provided alongside this project).

---

## Testing Without SendAfrica

Set `SENDAFRICA_API_KEY` to any non-empty string. The service will attempt the HTTP call and log failures — it never raises, so your app flow won't break. Check `SmsLog` to see what would have been sent.

For unit testing:

```python
from unittest.mock import patch
from notifications.services import send_sms

@patch('notifications.services.urllib.request.urlopen')
def test_send_sms(mock_urlopen):
    mock_urlopen.return_value.__enter__.return_value.read.return_value = \
        b'{"success": true, "data": {"message_id": "test-123"}}'
    assert send_sms("0712345678", "Test") == True
```
