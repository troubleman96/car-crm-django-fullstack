# Accounts Templates

> **Quick links:** [templates root](../README.md) · [accounts app README](../../accounts/README.md) · [vehicles templates](../vehicles/README.md) · [leads templates](../leads/README.md) · [root README](../../README.md)

Location: `templates/accounts/`

These are the authentication pages. They are **standalone** — they do NOT
extend `base.html`. Each is a full-screen split layout with a car image
on the left and a form on the right.

---

## Files

### `staff_login.html`
**URL**: `/accounts/login/`
**View**: `accounts.views.staff_login_view`
**Purpose**: Staff (employee) login with phone + password.

**Context variables**:
- `form` — A Django Form instance with fields `phone` and `password`.
  Access errors via `form.non_field_errors`.

**Flow**:
1. User enters phone number (e.g. `+255711000001`) and password
2. Form validates and normalizes phone (adds `+255` prefix if missing)
3. Django `authenticate()` checks credentials + `is_staff=True`
4. On success → redirect to `/admin/`
5. On failure → shows error banner

**Layout**:
- Left (hidden on mobile): BMW image, "Drive Your Success Forward" branding
- Right: card with phone icon input, lock icon input, dark "Sign in" button,
  OR divider, OTP login link

---

### `otp_send.html`
**URL**: `/accounts/otp/send/`
**View**: `accounts.views.customer_otp_send`
**Purpose**: Customer login step 1 — enter phone to receive a 6-digit SMS code.

**Context variables**: (none — just a phone input form that POSTs to itself)

**Flow**:
1. User enters phone number (e.g. `0712345678` or `+255712345678`)
2. View normalizes phone, generates random 6-digit OTP, stores in DB with
   5-minute expiry, sends via SMS (SendAfrica API)
3. Stores phone in session (`otp_phone`) and redirects to `otp_verify`
4. On error → stays on page with error message

**Layout**:
- Left (hidden on mobile): Mercedes image, stats (500+ sold, 50+ brands)
- Right: phone icon header, phone input, blue "Send Code" button,
  OR divider, staff login link

---

### `otp_verify.html`
**URL**: `/accounts/otp/verify/`
**View**: `accounts.views.customer_otp_verify`
**Purpose**: Customer login step 2 — enter the 6-digit code from SMS.

**Context variables**: (none — session holds the phone number from step 1)

**Security features**:
- OTP is **single-use** (`is_used` flag prevents replay attacks)
- OTP **expires after 5 minutes** (checked via `expires_at`)
- Phone is stored in **session**, not a hidden form field (prevents tampering)
- Code input has `inputmode="numeric"` and `autocomplete="one-time-code"`
  for native mobile OTP auto-fill

**Flow**:
1. Phone number loaded from session (set by `otp_send`)
2. User enters the 6-digit code
3. View looks up OTP record matching `phone + code + not used + not expired`
4. If valid → marks used, logs user in, redirects to home (or booking page)
5. If invalid/expired → shows error, user can click "Send new code"

**Layout**:
- Left (hidden on mobile): Range Rover image, "Almost There!" heading,
  security notice badge
- Right: message icon header, large OTP input with wide letter-spacing,
  dark "Verify Code" button, "Send new code" link

---

## Design Notes

- All three pages use a consistent split-screen pattern:
  - Desktop (`lg:`): 50/50 split, car image + gradient overlay on left
  - Mobile: image hidden, full-width form centered
- Background car images via Unsplash (hardcoded URLs)
- Font Awesome icons for inputs (phone, lock, paper plane, check)
- Gradient backgrounds (`from-gray-50 to-blue-50/30`) on the form side
- Shadow and rounded corners (`rounded-2xl`, `shadow-xl`) on form cards
- Consistent spacing, font sizes, and color palette

---

## Related

- [Root templates README](../README.md)
- [accounts app README](../../accounts/README.md) — for view logic
