# Car CRM — Project Configuration Hub

## Overview

The `car_crm` package is the **Django project configuration hub**. It contains the central `settings.py` (where all apps, databases, security, and third-party integrations are configured), `urls.py` (the root URL routing table), and the WSGI/ASGI entry points for deployment. This is the first code Django loads when the server starts — it ties together every app (accounts, vehicles, leads, chatbot, notifications, campaigns, advertising) into a single working CRM system.

---

## Settings — `car_crm/settings.py`

All critical settings are documented below.

### Security Settings

```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
```

- **`SECRET_KEY`** — Used for cryptographic signing (sessions, CSRF tokens, password reset tokens). Load from environment variable. **Never commit the production key to git.**
- **`DEBUG`** — When `True`, shows detailed error pages with stack traces. Always set to `False` in production.
- **`ALLOWED_HOSTS`** — Comma-separated list of domain names that can serve the site. Prevents HTTP Host header attacks.

### Installed Apps

```python
INSTALLED_APPS = [
    'jazzmin',              # Must come BEFORE django.contrib.admin
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',             # Custom user model, OTP authentication
    'vehicles',             # Car inventory management
    'notifications',        # SMS sending service (SendAfrica)
    'leads',                # Customer leads & appointments
    'chatbot',              # Live chat widget
    'campaigns',            # Bulk SMS marketing
    'advertising',          # Banners & promotions
]
```

**Why Jazzmin comes first:** `jazzmin` must be listed before `django.contrib.admin` because it overrides the admin's default templates. Django processes `INSTALLED_APPS` in order, and Jazzmin's template overrides take effect only when loaded first.

### Database — MySQL vs SQLite Switching

```python
USE_MYSQL = os.environ.get('USE_MYSQL', 'True') == 'True'
```

The project supports **automatic database switching** based on the `USE_MYSQL` environment variable:

| `USE_MYSQL` | Database Used | When to Use |
|-------------|---------------|-------------|
| `True` (default) | MySQL | Production, team development |
| `False` | SQLite (db.sqlite3) | Local development, testing |

**MySQL Configuration:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'car_crm'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

**SQLite Fallback:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**How switching works:**
```python
if USE_MYSQL:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        USE_MYSQL = False
```
If `pymysql` is not installed, it automatically falls back to SQLite. This means you can clone the project, not install MySQL, set `USE_MYSQL=False`, and immediately start developing with SQLite.

### Custom User Model

```python
AUTH_USER_MODEL = 'accounts.CustomUser'
```

This replaces Django's default `auth.User` with our custom model that uses phone numbers for authentication. **This must be set before the first migration** — changing it after migrations have been created is extremely difficult.

### Timezone

```python
TIME_ZONE = 'Africa/Dar_es_Salaam'
```

All dates and times in the database are stored in UTC but displayed in East Africa Time (UTC+3) by default.

### Static & Media Files

```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

- **`STATICFILES_DIRS`** — Additional directories Django searches for static files.
- **`STATIC_ROOT`** — Directory where `collectstatic` gathers all files for production.
- **`MEDIA_ROOT`** — Directory for user-uploaded files (car images, etc.).

### SendAfrica API Configuration

```python
SENDAFRICA_API_KEY = os.environ.get('SENDAFRICA_API_KEY', '')
SENDAFRICA_BASE_URL = 'https://api.sendafrica.online'
```

The API key is loaded from the `.env` file (or environment variables):
```
SENDAFRICA_API_KEY=687c72abc476d89ae3584f72c207b223beb84086e51071d8ea21f60833a10172
```

All SMS sending goes through `notifications/services.py → send_sms()`.

### Jazzmin Admin Theme

Jazzmin replaces Django's default admin with a modern Bootstrap 4-based UI.

**Key settings:**
- `site_title`: Browser tab text ("CarDealTZ Admin")
- `site_header`: Login page header ("CarDealTZ")
- `site_brand`: Top-left brand text ("CarDealTZ")
- `welcome_sign`: Welcome message on login page
- `search_model`: Global search searches `accounts.CustomUser` and `leads.Lead`
- `order_with_respect_to`: Sidebar app order: accounts → vehicles → leads → chatbot → notifications → campaigns
- **Icons:** Each model has a Font Awesome 5 icon (e.g. `fas fa-car` for Car, `fas fa-comments` for ChatSession)
- `changeform_format`: `'horizontal_tabs'` — tabbed layout for edit forms

**UI Tweaks (JAZZMIN_UI_TWEAKS):**
- `navbar`: Dark blue navbar with primary accent
- `sidebar`: Dark sidebar, fixed position
- `navbar_fixed`: True (navbar stays at top when scrolling)
- `sidebar_fixed`: True (sidebar stays when scrolling)

### Login / Logout URLs

```python
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/'
```

These tell Django where to redirect unauthenticated users and where to go after login/logout.

---

## URL Routing — `car_crm/urls.py`

The root URL configuration delegates to each app:

```python
urlpatterns = [
    path('admin/', admin.site.urls),              # Django admin
    path('accounts/', include('accounts.urls')),   # Authentication (login, OTP)
    path('', include('vehicles.urls')),            # Landing page + car detail (mounted at root)
    path('leads/', include('leads.urls')),         # Booking
    path('chatbot/', include('chatbot.urls')),     # Chat API
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**Routing table:**

| URL Prefix | App | Key Endpoints |
|------------|-----|---------------|
| `/admin/` | Django Admin | Full CRUD for all models |
| `/accounts/` | accounts | `/login/`, `/otp/send/`, `/otp/verify/` |
| `/` (root) | vehicles | `/` (landing), `/car/<id>/` (detail) |
| `/leads/` | leads | `/book/` |
| `/chatbot/` | chatbot | `/message/` (API), `/history/<id>/` (API) |

**Why vehicles is mounted at root (`''`):**
The landing page should be at the site root (`https://example.com/`), not at `/vehicles/`. The `vehicles/urls.py` uses `app_name = 'vehicles'` so URL names like `vehicles:landing` still work correctly with the named namespace.

**Static/Media serving in development:**
The `if settings.DEBUG:` block appends URL patterns to serve media files during development. In production, a web server (Nginx) handles media and static files directly.

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | Dev-only fallback | Secret key for cryptographic signing |
| `DJANGO_DEBUG` | `True` | Debug mode (set `False` in production) |
| `DJANGO_ALLOWED_HOSTS` | `localhost,127.0.0.1` | Allowed domain names |
| `USE_MYSQL` | `True` | Use MySQL (`False` = SQLite) |
| `DB_NAME` | `car_crm` | MySQL database name |
| `DB_USER` | `root` | MySQL username |
| `DB_PASSWORD` | (empty) | MySQL password |
| `DB_HOST` | `localhost` | MySQL host |
| `DB_PORT` | `3306` | MySQL port |
| `SENDAFRICA_API_KEY` | (empty) | SendAfrica API key for SMS |

---

## Dependencies

- **Every app in the project** — `INSTALLED_APPS` registers all apps and makes their models, templates, and static files available.
- **`accounts` app** — `AUTH_USER_MODEL = 'accounts.CustomUser'` ties the custom user model into Django's auth system project-wide.
- **`notifications` app** — `SENDAFRICA_API_KEY` and `SENDAFRICA_BASE_URL` are consumed by `notifications/services.py`.
- **`django-jazzmin`** — Third-party package for the admin theme. Must be in `requirements.txt`.
- **`pymysql`** — MySQL database driver. Only needed when using MySQL. Falls back gracefully if not installed.
