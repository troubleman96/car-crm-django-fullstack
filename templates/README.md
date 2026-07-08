# CarDealTZ Templates

> **Quick links:** [accounts templates](accounts/README.md) · [vehicles templates](vehicles/README.md) · [leads templates](leads/README.md) · [chatbot template](chatbot/README.md) · [advertising templates](advertising/README.md) · [accounts app](../accounts/README.md) · [vehicles app](../vehicles/README.md) · [leads app](../leads/README.md) · [chatbot app](../chatbot/README.md) · [root README](../README.md)

Location: `templates/`

This directory contains all Django HTML templates for the CarDealTZ CRM.
Below is a map of every template, what it does, and how they connect.

---

## Folder Structure

```
templates/
├── README.md              ← you are here
├── base.html              ← master layout (nav, messages, footer)
├── accounts/              ← authentication pages (standalone, no base.html)
│   ├── staff_login.html   ← staff phone + password login
│   ├── otp_send.html      ← customer OTP step 1: enter phone
│   └── otp_verify.html    ← customer OTP step 2: enter code
├── vehicles/              ← public vehicle browsing (extend base.html)
│   ├── landing.html       ← homepage with banner carousel + car grid
│   └── car_detail.html    ← single-vehicle detail page
├── leads/                 ← appointment booking (extends base.html)
│   └── book.html          ← booking form for test drives / call backs
├── chatbot/               ← AI chat widget (included by other templates)
│   └── widget.html        ← floating chat bubble + Alpine.js
└── advertising/           ← (reserved for future banner templates)
```

---

## Template Hierarchy

**Pages that use `base.html`** (show nav bar):
```
base.html
├── vehicles/landing.html        →  /
├── vehicles/car_detail.html     →  /car/<id>/
└── leads/book.html              →  /leads/book/
```

**Standalone pages** (full-screen, no nav bar):
```
accounts/staff_login.html        →  /accounts/login/
accounts/otp_send.html           →  /accounts/otp/send/
accounts/otp_verify.html         →  /accounts/otp/verify/
```

**Included partials** (not standalone pages):
```
chatbot/widget.html    ← included by landing.html, car_detail.html, book.html
```

---

## Template-to-URL Map

| URL                        | Template                    | View                        |
|----------------------------|-----------------------------|-----------------------------|
| `/`                        | `vehicles/landing.html`     | `vehicles.views.landing_page`       |
| `/car/<id>/`               | `vehicles/car_detail.html`  | `vehicles.views.car_detail`        |
| `/leads/book/`             | `leads/book.html`           | `leads.views.book`                 |
| `/accounts/login/`         | `accounts/staff_login.html` | `accounts.views.staff_login_view`  |
| `/accounts/otp/send/`      | `accounts/otp_send.html`    | `accounts.views.customer_otp_send` |
| `/accounts/otp/verify/`    | `accounts/otp_verify.html`  | `accounts.views.customer_otp_verify` |

---

## Context Variables Per Template

See each subfolder README for the full list. Brief summary:

| Template                | Key Context              |
|-------------------------|--------------------------|
| `landing.html`          | `banners`, `promotions`, `cars` |
| `car_detail.html`       | `car` (Vehicle instance) |
| `book.html`             | `car` (optional Vehicle) |
| `staff_login.html`      | `form` (LoginForm)       |
| `otp_send.html`         | (formless — just phone input) |
| `otp_verify.html`       | (formless — just code input) |
| `widget.html`           | `user.phone` (from global context) |

---

## Comment Conventions

This project uses three kinds of comments in Django templates:

| Syntax                    | Purpose                                  |
|---------------------------|------------------------------------------|
| `{# single line #}`       | Short inline notes (safe, single-line)   |
| `{% comment %} ... {% endcomment %}` | Multi-line documentation blocks |
| `{% comment %}` ... | File-level headers explaining the template's purpose and flow |

**Never** use multi-line `{# #}` — Django 6.0.7 does not properly hide
template tags (`{% %}` / `{{ }}`) inside them, causing them to leak into
the rendered HTML.

---

## Visual Design

- **Base layout**: Tailwind CSS, sticky nav bar, responsive (hamburger menu on mobile)
- **Auth pages**: Full-screen split layout — left side car image + branding, right side form
- **Landing page**: Alpine.js banner carousel, promotion cards ("Hot Deals"), vehicle grid
- **Car detail**: Primary image hero, info + description, thumbnail gallery, action buttons
- **Chat widget**: Fixed position bottom-right, Alpine.js-powered, session-based conversation

---

## Dependencies

- **Tailwind CSS** — loaded from CDN in `base.html`
- **Font Awesome 6** — icons, loaded from CDN in all templates
- **Alpine.js 3** — interactivity (carousel, chat widget), loaded in `widget.html`

Template files should never hardcode URLs — use `{% url '...' %}` and
`{% load static %}` instead.
