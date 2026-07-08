# Advertising App — Banners & Promotions

> **Quick links:** [`vehicles` app](../vehicles/README.md) · [vehicles templates](../templates/vehicles/README.md) · [templates advertising](../templates/advertising/README.md) · [root README](../README.md)

## Overview

The `advertising` app manages **promotional content** displayed on the dealership's landing page. It provides two models: `Banner` (hero slider images) and `Promotion` (special deals on specific cars with discount badges). The `vehicles` app's landing page view imports these models and passes them to the template, where banners render as an Alpine.js carousel and promotions appear as labelled "Hot Deal" cards. This app follows Django's "reusable app" philosophy — it is self-contained and could be dropped into another project.

---

## Models

### Banner

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `title` | `CharField(max_length=200)` | Required | Headline text displayed on the banner |
| `subtitle` | `TextField` | `null=True, blank=True` | Optional secondary text below the title |
| `image_url` | `CharField(max_length=500)` | Required | URL pointing to the banner image |
| `link_url` | `CharField(max_length=500)` | `null=True, blank=True` | Optional click-through URL (when user clicks the banner) |
| `is_active` | `BooleanField` | `default=True` | Toggle to show/hide the banner without deleting it |
| `order` | `SmallIntegerField` | `default=0` | Display order (ascending — lower numbers appear first) |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Created timestamp |

**Meta:** `ordering = ['order', '-created_at']` — sorted by `order` ascending, then newest first for ties.

### Promotion

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `car` | `ForeignKey('vehicles.Car')` | `on_delete=CASCADE, related_name='promotions'` | The car this promotion applies to |
| `label` | `CharField(max_length=10)` | `choices=LABEL_CHOICES, default='featured'` | Promotional badge type |
| `discount_percent` | `SmallIntegerField` | `null=True, blank=True` | Optional discount percentage (e.g. 15 = 15% off) |
| `is_active` | `BooleanField` | `default=True` | Toggle to activate/deactivate |
| `starts_at` | `DateTimeField` | `null=True, blank=True` | When the promotion becomes active (nullable = indefinite) |
| `ends_at` | `DateTimeField` | `null=True, blank=True` | When the promotion expires (nullable = indefinite) |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Created timestamp |

**LABEL_CHOICES:**

| Value | Display Label | CSS Colour |
|-------|---------------|------------|
| `featured` | Featured | Blue |
| `sale` | Sale | Red |
| `new` | New Arrival | Green |
| `hot` | Hot Deal | Orange |

**Meta:** `ordering = ['-created_at']` — newest promotions first.

---

## How It Connects to the Landing Page

The `vehicles/views.py` `landing_page` view imports both models and includes them in the template context:

```python
from advertising.models import Banner, Promotion

def landing_page(request):
    cars = Car.objects.filter(status='available').prefetch_related('images')
    
    # All active banners, ordered by 'order' field
    banners = Banner.objects.filter(is_active=True)
    
    # Current promotions (active + within date range)
    now = timezone.now()
    promotions = Promotion.objects.filter(
        is_active=True,
        starts_at__lte=now,
        ends_at__gte=now,
    ).select_related('car')
    
    return render(request, 'vehicles/landing.html', {
        'cars': cars,
        'banners': banners,
        'promotions': promotions,
    })
```

### How the Landing Page Displays Them

**Banners** — Rendered as an Alpine.js auto-advancing carousel:
- Each banner is a full-width slide with background image, title overlay, subtitle, and optional "Learn More" button
- Auto-advances every 5 seconds
- Dot indicators at the bottom for manual navigation
- If no banners exist, a static fallback heading is shown instead

```
┌──────────────────────────────────────────────────────────┐
│  [Image]                                                 │
│  ┌──────────────────────────────────────────────────┐    │
│  │  Summer Sale 2025                                │    │
│  │  Up to 20% off selected models                  │    │
│  │  [Learn More →]                                  │    │
│  └──────────────────────────────────────────────────┘    │
│          ● ○ ○ ○  (dot navigation)                      │
└──────────────────────────────────────────────────────────┘
```

**Promotions** — Rendered as labelled cards within a "🔥 Hot Deals" section:
- Each card shows a coloured label badge (based on `label` field)
- The car's primary image (or a placeholder if none)
- Make, model, year, and price
- If `discount_percent` is set: shows the actual price with a strikethrough "original" price
- Two action buttons: "Book Test Drive" and "View Details"
- The entire "Hot Deals" section is hidden if no active promotions exist

```
┌─────────────────────┐ ┌─────────────────────┐
│ HOT DEAL  ┌────────┐│ │ SALE      ┌────────┐│
│           │  Img   ││ │           │  Img   ││
│           └────────┘│ │           └────────┘│
│ Toyota Hilux 2023   │ │ BMW X5 2021         │
│ TZS 95,000,000      │ │ TZS 150,000,000     │
│ ~~TZS 110,000,000~~ │ │ [Book] [Details]    │
│ [Book] [Details]    │ │                     │
└─────────────────────┘ └─────────────────────┘
```

---

## How to Create Banners and Promotions in Admin

### Creating a Banner

1. Go to `/admin/advertising/banner/add/`
2. Fill in:
   - **Title** — e.g., "Summer Sale 2025"
   - **Subtitle** — e.g., "Up to 20% off selected models"
   - **Image URL** — paste a URL to the banner image (e.g. from Unsplash)
   - **Link URL** — optional, e.g. `/leads/book/`
   - **Active** — checked (to display on site)
   - **Order** — 0 for first position, 1 for second, etc.
3. Click "Save"

### Creating a Promotion

1. First ensure the car exists in the vehicles inventory.
2. Go to `/admin/advertising/promotion/add/`
3. Fill in:
   - **Car** — select the car from the dropdown
   - **Label** — choose Sale, Hot Deal, New Arrival, or Featured
   - **Discount Percent** — optional (e.g. 15 for 15% off)
   - **Active** — checked
   - **Starts At** — when the promotion should begin
   - **Ends At** — when the promotion should end
4. Click "Save"

**Tip:** Set `ends_at` in the past to expire a promotion. Set both `starts_at` and `ends_at` to `null`/blank for an indefinite promotion.

---

## URLs

The advertising app has **no public URLs**. Its models are consumed by the `vehicles` app's landing page view.

---

## Admin

Registered in `advertising/admin.py`:

### BannerAdmin
- **List columns:** `title`, `is_active`, `order`, `created_at`
- **Filter:** `is_active`
- **Search:** `title`
- **List editable:** `is_active`, `order` — toggle active status and change order directly from the list view (bulk save at the bottom)

### PromotionAdmin
- **List columns:** `car`, `label`, `discount_percent`, `is_active`, `starts_at`, `ends_at`
- **Filter:** `label`, `is_active`
- **Search:** `car__make`, `car__model`
- **List editable:** `is_active` — toggle active status directly from the list view

---

## Dependencies

- **`vehicles/models.py`** — `Promotion.car` is a ForeignKey to `Car` with `related_name='promotions'`.
- **`vehicles/views.py`** — The landing page view imports `Banner` and `Promotion` from this app.
- **`vehicles/templates/vehicles/landing.html`** — Renders banners and promotions using the context provided by the landing page view.
