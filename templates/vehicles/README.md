# Vehicles Templates

Location: `templates/vehicles/`

Templates for browsing and viewing cars. Both extend `base.html` and
include the chatbot widget.

---

## Files

### `landing.html`
**URL**: `/`
**View**: `vehicles.views.landing_page`
**Purpose**: Main homepage. Displays a rotating banner carousel, hot deals
(promotions), and the full vehicle inventory grid.

**Context variables**:
| Variable      | Type              | Description                                  |
|---------------|-------------------|----------------------------------------------|
| `banners`     | QuerySet of `Banner` | Active banners with image, title, link    |
| `promotions`  | QuerySet of `Promotion` | Active promotions with discount, label   |
| `cars`        | QuerySet of `Vehicle` | All vehicles (used in the inventory grid) |

**Sections**:
1. **Banner Carousel** (Alpine.js) — auto-advances every 5s, dot navigation.
   Falls back to text heading when no banners exist.
2. **Hot Deals** — promotion cards with colored labels (sale=red, hot=orange,
   new=green), discount display, action buttons.
3. **Full Inventory Grid** — 3-column responsive grid of all vehicles.
   Heading changes dynamically ("All Vehicles" if promotions exist).
   Includes `{% empty %}` fallback when no cars.
4. **Chatbot Widget** — included at the bottom via `{% include %}`.

**Key template features**:
- `dictsortreversed:"is_primary"|first` — selects the primary image
- Alpine.js `x-data` + `x-init` for auto-playing carousel
- Conditional sections via `{% if banners %}`, `{% if promotions %}`
- `{% empty %}` inside `{% for car in cars %}` for zero-state

---

### `car_detail.html`
**URL**: `/car/<id>/`
**View**: `vehicles.views.car_detail`
**Purpose**: Single-vehicle detail page showing primary image, info, and actions.

**Context variables**:
| Variable | Type              | Description                        |
|----------|-------------------|------------------------------------|
| `car`    | `Vehicle` instance | The vehicle with its `images.all` |

**Sections**:
1. **Breadcrumb** — link back to home page
2. **Primary Image** — large hero image, falls back to placeholder SVG
3. **Vehicle Info** — make/model/year (h1), price (TZS formatted), description
4. **Action Buttons** — "Book Test Drive" and "Request Call Back", both link to
   `leads/book/?car=<id>`
5. **Thumbnail Gallery** — appears only when `car.images.all|length > 1`
6. **Chatbot Widget** — floating chat bubble

---

## Design Notes

- Both templates use Tailwind CSS utility classes consistently
- Cards use `rounded-xl shadow-sm border border-gray-200` pattern
- The primary image selection logic is shared across both templates:
  `car.images.all|dictsortreversed:"is_primary"|first`
- Prices formatted with `|floatformat:0` and prefixed with "TZS"
- Responsive grids: `grid-cols-1 sm:grid-cols-2 lg:grid-cols-3`
- All internal links use `{% url %}` — never hardcoded

---

## Related

- [Root templates README](../README.md)
- [vehicles app README](../../vehicles/README.md) — for view logic
- [advertising app README](../../advertising/README.md) — for Banner/Promotion models
