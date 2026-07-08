# Leads Templates

> **Quick links:** [templates root](../README.md) · [leads app README](../../leads/README.md) · [vehicles templates](../vehicles/README.md) · [chatbot template](../chatbot/README.md) · [root README](../../README.md)

Location: `templates/leads/`

Templates for appointment booking. Extends `base.html`.

---

## Files

### `book.html`
**URL**: `/leads/book/`
**View**: `leads.views.book`
**Purpose**: Appointment booking form. Customers can book a test drive,
request a call back, or schedule a showroom visit.

**Context variables**:
| Variable | Type              | Description                                    |
|----------|-------------------|------------------------------------------------|
| `car`    | `Vehicle` or `None` | Pre-selected vehicle (from `?car=<ID>` query) |

**Sections**:
1. **Breadcrumb** — link back to home page
2. **Selected Car Card** (conditional) — only shown when a `car` object is
   provided in context. Displays make/model/year/price with a "Selected car"
   label.
3. **Booking Form**:
   - `csrf_token` — Django CSRF protection
   - Hidden `car_id` input — carries the vehicle ID (or empty for general inquiry)
   - Phone number field — required
   - Appointment type dropdown — Test Drive / Call Back / Showroom Visit
   - Date & time picker — `datetime-local` HTML5 input
   - Submit button — "Confirm Booking"
4. **Chatbot Widget** — included at the bottom

**Form submission**:
- Method: POST
- Endpoint: same URL (`/leads/book/`)
- On success: redirects to a confirmation page or home
- On error: shows form validation errors

**Key template features**:
- `{{ car.id|default:'' }}` — safely renders empty string when `car` is None
  (avoids the word "None" appearing in the HTML)
- `{% if car %}` — conditionally shows the pre-selected car info card
- `required` attributes on all inputs for browser-side validation

---

## Design Notes

- Clean single-column layout (`max-w-2xl mx-auto`)
- Consistent card styling with other templates (`rounded-xl shadow-sm border`)
- Simple, functional form — no split-screen since it's not an auth page
- All inputs follow the same styling pattern: `rounded-lg`, `focus:ring-2`,
  `focus:border-blue-500`

---

## Related

- [Root templates README](../README.md)
- [leads app README](../../leads/README.md) — for view logic and Lead model
