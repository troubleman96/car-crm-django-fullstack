# Accounts App — User Authentication & OTP Login

## Overview

The `accounts` app handles **all user authentication** in the CarDealTZ CRM. It provides two separate login flows: **staff users** (dealership employees) log in with a phone number and password via a standard Django form, while **customers** (website visitors) log in using a passwordless OTP (One-Time Password) flow that sends a 6-digit code via SMS. The app defines a **custom user model** (`CustomUser`) that replaces Django's default `User` model, using the phone number as the unique login identifier instead of a username or email.

---

## Models

### CustomUser

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `phone` | `CharField(max_length=15)` | `unique=True` | Tanzania phone number in +255 format. Used as the login identifier. |
| `full_name` | `CharField(max_length=150)` | `null=True, blank=True` | Display name. Nullable because customers may not provide it during initial OTP registration. |
| `password` | `CharField(max_length=255)` | `null=True, blank=True` | Overrides inherited `password` to be nullable. Customers (OTP users) have no password — their password is set to "unusable". |
| `is_customer` | `BooleanField` | `default=True` | Custom flag to distinguish customers from staff. Used in admin filtering. |
| `is_staff` | `BooleanField` | `default=False` | Controls access to the Django admin site. |
| `is_active` | `BooleanField` | `default=True` | Can be used to deactivate accounts. |
| `is_superuser` | `BooleanField` | Inherited | Grants all permissions without explicit assignment. |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Timestamp of when the user was created. |

**Key configuration:**
- `USERNAME_FIELD = 'phone'` — tells Django to use the `phone` field for authentication (instead of the default `username`).
- `REQUIRED_FIELDS = []` — no additional prompts when running `createsuperuser`.
- `objects = CustomUserManager()` — custom manager that knows how to create users without a `username` field.

**CustomUserManager** provides two methods:
- `create_user(phone, password=None, **extra_fields)` — creates a regular user. If no password is given, calls `set_unusable_password()` (customers authenticate via OTP, not a password).
- `create_superuser(phone, password=None, **extra_fields)` — creates a staff user with `is_staff=True`, `is_superuser=True`, `is_customer=False`.

### OTP

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `phone` | `CharField(max_length=15)` | Indexed | The phone number the code was sent to. |
| `code` | `CharField(max_length=6)` | — | The 6-digit verification code (padded with leading zeros, e.g. "004829"). |
| `expires_at` | `DateTimeField` | — | Timestamp after which the code is no longer valid (currently 5 minutes from creation). |
| `is_used` | `BooleanField` | `default=False` | Prevents replay attacks — once verified, the same code cannot be reused. |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Timestamp of creation. |

**Meta:** `indexes = [models.Index(fields=['phone'])]` — database index on `phone` for fast lookups.

---

## How It Works — Two Authentication Flows

### Flow 1: Staff Password Login

```
User visits /accounts/login/
         │
         ▼
  Enter phone + password
         │
         ▼
  StaffLoginForm.clean()
    ├─ normalize_phone(phone)         → +255 format
    ├─ authenticate(phone, password)  → Django auth system
    ├─ Check user.is_staff            → reject customers
    └─ Store user in cleaned_data
         │
         ▼
  View calls login(request, user)
         │
         ▼
  Redirect to /admin/
```

Staff users have a password stored (hashed via `set_password()`). The `StaffLoginForm` in `forms.py` normalises the phone number, calls Django's `authenticate()`, verifies the user has `is_staff=True`, and stores the authenticated user in `cleaned_data['user']`. The view then calls `login()` to create a session and redirects to `/admin/`.

### Flow 2: Customer OTP (Passwordless) Login

```
Step 1: GET /accounts/otp/send/          Step 2: GET /accounts/otp/verify/
         │                                         │
         ▼                                         ▼
  Enter phone number                     Enter 6-digit code
         │                                         │
         ▼                                         ▼
  POST /accounts/otp/send/               POST /accounts/otp/verify/
         │                                         │
         ├─ normalize_phone(phone)                  ├─ Read phone from session
         ├─ Generate random 6-digit code            ├─ Look up OTP where:
         ├─ Save OTP to DB (expires 5min)           │   phone=session_phone
         ├─ send_sms(phone, code)                   │   code=form_code
         ├─ Store phone in session                  │   is_used=False
         └─ Redirect to verify page                 │   expires_at > now
                                                    ├─ If found:
                                                    │   ├─ Mark OTP is_used=True
                                                    │   ├─ get_or_create CustomUser
                                                    │   ├─ login(request, user)
                                                    │   └─ Redirect (home or booking)
                                                    └─ If not found:
                                                        └─ Show error "Invalid or expired"
```

**Key security design:**
- The phone number is stored in the **session** (not the form) during step 2, preventing session tampering.
- The OTP is marked `is_used=True` after successful verification — the same code cannot be reused.
- `get_or_create()` creates a `CustomUser` row the **first** time a phone successfully verifies an OTP. Subsequent logins just fetch the existing user.
- The optional `booking_next` session variable lets the booking app redirect users back to complete a booking after authentication.

### Phone Normalization

The `normalize_phone()` function in `notifications/services.py` converts any input format to the standard international format `+2557XXXXXXXX`:

| Input | Output |
|-------|--------|
| `0712345678` | `+255712345678` |
| `255712345678` | `+255712345678` |
| `+255712345678` | `+255712345678` |
| `0712 345 678` | `+255712345678` |
| `+255 712-345-678` | `+255712345678` |

**Algorithm:**
1. Strip all whitespace, dashes, and parentheses.
2. If starts with `0`, replace leading `0` with `+255`.
3. If starts with `255` (no `+`), prepend `+`.
4. If still doesn't start with `+`, prepend `+255` as fallback.

---

## URLs

| URL Pattern | View Function | Name | Method | Description |
|-------------|---------------|------|--------|-------------|
| `/accounts/login/` | `staff_login_view` | `accounts:staff_login` | GET, POST | Staff login form (phone + password) |
| `/accounts/logout/` | `staff_logout_view` | `accounts:staff_logout` | GET | Logout and redirect to `/` |
| `/accounts/otp/send/` | `customer_otp_send` | `accounts:otp_send` | GET, POST | Customer OTP step 1 — enter phone |
| `/accounts/otp/verify/` | `customer_otp_verify` | `accounts:otp_verify` | GET, POST | Customer OTP step 2 — enter code |

---

## Forms

| Form Class | Fields | Purpose |
|------------|--------|---------|
| `StaffLoginForm` | `phone`, `password` | Staff login with custom `clean()` that authenticates user |
| `PhoneForm` | `phone` | Simple phone input for OTP send step |
| `OTPVerifyForm` | `code` | Simple code input for OTP verify step |

---

## Admin

Registered in `accounts/admin.py`:

### CustomUserAdmin (extends BaseUserAdmin)
- **List columns:** `phone`, `full_name`, `is_customer`, `is_staff`, `is_active`
- **Filters:** `is_customer`, `is_staff`, `groups`
- **Search:** `phone`, `full_name`
- **Fieldsets:** Personal info, Permissions, Important dates
- **Add form:** Includes `password1`/`password2` for setting staff passwords

### OTPAdmin
- **List columns:** `phone`, `code`, `expires_at`, `is_used`, `created_at`
- **Filters:** `is_used`
- **Search:** `phone`
- **All fields read-only** — OTPs are immutable audit records

Access at `/admin/accounts/` (superuser/staff only).

---

## Seed Data

Run `python manage.py seed_data` to populate the database with sample records:

| Type | Phone | Password | Name | Role |
|------|-------|----------|------|------|
| Staff | `+255711000001` | `admin123` | Admin User | Superuser |
| Staff | `+255711000002` | `marketing123` | Marketing User | Staff |
| Staff | `+255711000003` | `sales123` | Sales User | Staff |
| Staff | `+255711000004` | `support123` | Support User | Staff |
| Customer | `+255712000001` | (none/OTP) | Juma Mwangi | Customer |
| Customer | `+255712000002` | (none/OTP) | Aisha Mohamed | Customer |

---

## Dependencies

- **`notifications/services.py`** — imports `send_sms()` and `normalize_phone()` for OTP delivery and phone formatting.
- **`car_crm/settings.py`** — `AUTH_USER_MODEL = 'accounts.CustomUser'` replaces the default Django User model project-wide.
- **Django built-ins:** `django.contrib.auth` (authenticate, login, logout), `django.contrib.sessions` (session storage), `django.contrib.messages` (flash messages).
