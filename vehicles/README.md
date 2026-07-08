# Vehicles App — Car Inventory

Manages the dealership's car inventory — CRUD for cars and images, public listing and detail pages.

---

## Models

### Car

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto-generated |
| `make` | VARCHAR(50) | Manufacturer (Toyota, Nissan, BMW, etc.) |
| `model` | VARCHAR(50) | Model name (Hilux, X-Trail, X5, etc.) |
| `year` | SMALLINT | Manufacturing year |
| `price` | DECIMAL(12,2) | Price in Tanzanian Shillings (TZS) |
| `status` | ENUM('available','reserved','sold') | Inventory status |
| `description` | TEXT, nullable | Detailed description, features, condition |
| `created_at` | DATETIME, auto | When added to inventory |

### CarImage

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto-generated |
| `car` | FK -> Car | Parent car (CASCADE delete) |
| `image_url` | VARCHAR(255) | URL or path to image |
| `is_primary` | BOOLEAN | Primary image shown in listings |

---

## Views

### Landing Page (`/`)

- Lists all `status='available'` cars in a responsive grid (1-3 columns)
- Each card shows: primary image (or placeholder), make/model, year, price
- Action buttons: "Book Test Drive" (links to booking with car preselected), "View Details"
- Includes chatbot widget
- Fallback message when no cars available

### Car Detail (`/car/<id>/`)

- Full-width image, car details, price, description
- Additional images gallery (if multiple images exist)
- Action buttons: "Book Test Drive", "Request Call Back"
- Includes chatbot widget

---

## Admin

`CarAdmin` with `CarImageInline`:

- List display: make, model, year, price, status, created_at
- Filters: status, make, year
- Search: make, model, description
- Inline image management (add/remove images from car edit page)

`CarImageAdmin`: Standalone list with filter by is_primary.

---

## URL Endpoints

| URL | View | Description |
|-----|------|-------------|
| `/` | `landing_page` | Public car listing |
| `/car/<int:car_id>/` | `car_detail` | Car detail page |

---

## Seed Data

8 cars with realistic Tanzania-market data:

1. Toyota Hilux (2023) — TZS 95,000,000
2. Toyota Land Cruiser Prado (2022) — TZS 180,000,000
3. Nissan X-Trail (2023) — TZS 65,000,000
4. Suzuki Swift (2024) — TZS 28,000,000
5. BMW X5 (2021) — TZS 150,000,000
6. Mercedes-Benz C-Class (2023) — TZS 85,000,000
7. Honda CR-V (2022) — TZS 72,000,000
8. Mitsubishi Outlander (2023) — TZS 58,000,000

Each car gets one primary image (Unsplash CDN URLs) and all are `status='available'`.

---

## Templates

- `templates/vehicles/landing.html` — Grid listing with Tailwind CSS
- `templates/vehicles/car_detail.html` — Single car view with gallery

Both templates include `{% include 'chatbot/widget.html' %}`.
