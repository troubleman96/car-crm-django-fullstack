# Vehicles App — Car Inventory Management

## Overview

The `vehicles` app manages the dealership's **car inventory** — the core product of the CRM. It defines two models (`Car` and `CarImage`) and provides two public views: the **landing page** (homepage) which displays available cars alongside banners and promotions from the `advertising` app, and a **car detail page** for individual vehicle information. This app is the central hub that leads, bookings, and promotions all connect to.

---

## Models

### Car

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `make` | `CharField(max_length=50)` | Required | Car manufacturer (e.g. "Toyota", "BMW") |
| `model` | `CharField(max_length=50)` | Required | Model name (e.g. "Hilux", "X5") |
| `year` | `SmallIntegerField` | Required | Manufacturing year |
| `price` | `DecimalField(max_digits=12, decimal_places=2)` | Required | Price in Tanzanian Shillings (TZS). Uses `DecimalField` (not `FloatField`) for accurate financial calculations. |
| `status` | `CharField(max_length=10)` | `choices=STATUS_CHOICES, default='available'` | One of: `available`, `reserved`, `sold` |
| `description` | `TextField` | `null=True, blank=True` | Optional detailed description |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Timestamp of when the car was added to inventory |

**STATUS_CHOICES:**
- `available` — visible on the public landing page
- `reserved` — hidden from public listing (a deposit has been paid)
- `sold` — hidden from public listing (sale completed)

**Meta:** `ordering = ['-created_at']` — newest cars first by default.

### CarImage

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `car` | `ForeignKey(Car)` | `on_delete=CASCADE, related_name='images'` | The car this image belongs to. `CASCADE` means deleting a car deletes all its images. |
| `image_url` | `CharField(max_length=255)` | Required | URL pointing to the image file (remote or local) |
| `is_primary` | `BooleanField` | `default=False` | Flag to designate the main/thumbnail image for a car listing |

**Relationship:** One `Car` → many `CarImage` records (one-to-many). Access via `car.images.all()`.

---

## How It Works

### Landing Page Rendering

The `landing_page` view in `views.py` gathers three categories of data and passes them to the `vehicles/landing.html` template:

```
landing_page(request)
    │
    ├─ 1. Fetch available cars
    │     Car.objects.filter(status='available')
    │         .prefetch_related('images')
    │     └─ Only cars with status='available' are shown
    │     └─ prefetch_related prevents N+1 queries for images
    │
    ├─ 2. Fetch active banners
    │     Banner.objects.filter(is_active=True)
    │     └─ From the advertising app
    │
    └─ 3. Fetch current promotions
          Promotion.objects.filter(
              is_active=True,
              starts_at__lte=now,
              ends_at__gte=now,
          ).select_related('car')
          └─ Only active promotions within their date range
          └─ select_related JOINs the Car data in the same query
```

**Template rendering order on the landing page:**

1. **Banner Carousel** — If banners exist, an Alpine.js-powered carousel auto-advances every 5 seconds showing banner images, titles, subtitles, and optional "Learn More" links. Falls back to a static hero heading if no banners.

2. **Hot Deals / Promotions** — If active promotions exist, a grid of promotion cards shows a coloured label badge (sale=red, hot=orange, new=green, featured=blue), the car's primary image, make/model/year, price with optional strikethrough discount, and "Book Test Drive" / "View Details" buttons.

3. **All Vehicles Grid** — Always rendered. A responsive 3-column grid of every available car. Each card shows the primary image, make/model/year, price, and action buttons. If no cars exist, an "empty state" message is displayed.

4. **Global CTA** — A "Book a Showroom Visit" link at the bottom.

5. **Chatbot Widget** — `{% include 'chatbot/widget.html' %}` loads the floating chat widget.

### Car Detail Page

```
/car/<car_id>/
    │
    └─ car_detail(request, car_id)
          car = get_object_or_404(
              Car.objects.prefetch_related('images'),
              id=car_id
          )
          └─ Renders vehicles/car_detail.html with the single car
          └─ 404 if the car ID doesn't exist
```

The `car_id` parameter is captured from the URL via the path converter `<int:car_id>`.

---

## URLs

| URL Pattern | View Function | Name | Description |
|-------------|---------------|------|-------------|
| `/` | `landing_page` | `vehicles:landing` | Homepage — shows banners, promotions, and all available cars |
| `/car/<int:car_id>/` | `car_detail` | `vehicles:car_detail` | Single car detail page |

Note: The vehicles app is mounted at the **root** of the site (`path('', include('vehicles.urls'))` in the project's `urls.py`), so `/` is the landing page and `/car/5/` is a car detail page.

---

## Admin

Registered in `vehicles/admin.py`:

### CarAdmin
- **List columns:** `make`, `model`, `year`, `price`, `status`, `created_at`
- **Filters:** `status`, `make`, `year`
- **Search:** `make`, `model`, `description`
- **Inline:** `CarImageInline` — manage all car images directly on the Car edit page

### CarImageAdmin
- **List columns:** `car`, `image_url`, `is_primary`
- **Filter:** `is_primary`

### CarImageInline (TabularInline)
- Shows related `CarImage` records as a table on the Car change form
- `extra = 1` — shows one blank row for adding a new image

---

## Performance Optimizations

- **`prefetch_related('images')`** — Used in both views to fetch all related images in 2 queries (1 for cars + 1 for images) instead of N+1 queries.
- **`select_related('car')`** — Used in the promotions query to JOIN the Car data in the same SQL query, avoiding a separate query for each promotion's car.
- **`filter(status='available')`** — Only fetches cars that should be visible to the public, reducing the result set.

---

## Dependencies

- **`advertising/models.py`** — The landing page imports `Banner` and `Promotion` from the advertising app to build the homepage context.
- **`accounts/models.py`** — `CustomUser` is referenced indirectly when booking links pass user context.
- **`leads` app** — The "Book Test Drive" buttons on car cards link to `/leads/book/?car=<id>`.
- **`chatbot` app** — The landing page includes `chatbot/widget.html`.
- **`templates/base.html`** — The landing template extends this base layout.
