# Accounts App — Authentication & User Management

Handles two separate login flows and all user data for the CRM.

---

## Models

### CustomUser

Extends Django's `AbstractUser`. Phone number is the username field.

| Field | Type | Description |
|-------|------|-------------|
| `phone` | VARCHAR(15), unique, PK | Tanzania phone number (+2557xxxxxxxx) |
| `full_name` | VARCHAR(150), nullable | Display name |
| `password` | VARCHAR(255), nullable | NULL for customers (OTP-only), hashed for staff |
| `is_customer` | Boolean, default=True | Regular customer (OTP login) |
| `is_staff` | Boolean, default=False | Can access /admin |
| `is_active` | Boolean, default=True | Soft disable |
| `created_at` | DateTime, auto | Account creation timestamp |
| `last_login` | DateTime, inherited | From AbstractUser |
| `date_joined` | DateTime, inherited | From AbstractUser |

Staff roles use Django's built-in `auth_group` + `auth_user_groups` tables.

### OTP

One-time passwords for customer login.

| Field | Type | Description |
|-------|------|-------------|
| `phone` | VARCHAR(15) | Phone the OTP was sent to |
| `code` | VARCHAR(6) | 6-digit code |
| `expires_at` | DateTime | Code expiry (5 min after creation) |
| `is_used` | Boolean, default=False | Once verified, marked used |
| `created_at` | DateTime, auto | When the OTP was created |

---

## Authentication Flows

### Customer Login (OTP)

```
1. Customer enters phone number  ->  /accounts/otp/send/  (GET)
2. System generates 6-digit code  ->  stores in accounts_otp
3. System sends SMS with code     ->  via SendAfrica API
4. Customer enters code           ->  /accounts/otp/verify/ (POST)
5. Code verified?                 ->  get_or_create CustomUser(is_customer=True)
6. Logged in via session auth     ->  redirect to / or booking flow
```

### Staff Login (Password)

```
1. Staff enters phone + password  ->  /accounts/login/ (POST)
2. authenticate(phone, password)  ->  checks is_staff=True
3. Logged in via session auth     ->  redirect to /admin/
```

---

## URL Endpoints

| URL | View | Method | Description |
|-----|------|--------|-------------|
| `/accounts/login/` | `staff_login_view` | GET, POST | Staff login form |
| `/accounts/logout/` | `staff_logout_view` | GET | Logout, redirect to / |
| `/accounts/otp/send/` | `customer_otp_send` | GET, POST | Request OTP code |
| `/accounts/otp/verify/` | `customer_otp_verify` | GET, POST | Verify OTP code |

---

## Groups (Django Auth)

Created via data migration (`accounts/migrations/0002_create_groups.py`):

| Group | Permissions | Typical Members |
|-------|-------------|-----------------|
| **Admin** | Add, change, delete, view — ALL models | System admins |
| **Marketing** | Add, change, view — Leads, Campaigns, CampaignRecipients | Marketing team |
| **Sales** | Add, change, view — Leads, Appointments | Sales reps |
| **Support** | View — ChatSessions, ChatMessages, Leads (read-only) | Support agents |

---

## Admin Registration

`CustomUserAdmin` extends Django's `UserAdmin` with phone-based authentication:

- List display: phone, full_name, is_customer, is_staff, is_active
- List filters: is_customer, is_staff, groups
- Search: phone, full_name
- Fieldsets organized by info, permissions, dates

`OTPAdmin`: Read-only view of OTP records with list filter by `is_used`.

---

## Seed Data

Created by `python manage.py seed_data`:

| Phone | Password | Role | Group |
|-------|----------|------|-------|
| +255711000001 | admin123 | Superuser/Staff | Admin |
| +255711000002 | marketing123 | Staff | Marketing |
| +255711000003 | sales123 | Staff | Sales |
| +255711000004 | support123 | Staff | Support |
| +255712000001 | (OTP only) | Customer | — |
| +255712000002 | (OTP only) | Customer | — |

---

## Dependencies

- `notifications.services.send_sms` — sending OTP codes via SMS
- `django.contrib.auth` — session auth, groups, permissions
- `django.contrib.admin` — admin site registration
