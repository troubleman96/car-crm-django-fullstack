"""
===============================================================================
 DJANGO SETTINGS — CarDealTZ CRM
===============================================================================
 This is the main configuration file for the entire CarDealTZ project.
 Django reads this file when the server starts to know:
   - Which apps are installed
   - Which database to connect to
   - What templates/static files to use
   - Security, timezone, and other global settings

 Think of this as the "control panel" for your Django project.
===============================================================================
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

# ---------------------------------------------------------------------------
# BASE DIRECTORY
# ---------------------------------------------------------------------------
# Path(__file__).resolve().parent.parent gives us the project root folder
# (the one containing manage.py). We use this to build paths throughout.
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# SECURITY SETTINGS
# ---------------------------------------------------------------------------
# SECRET_KEY is used for cryptographic signing (sessions, CSRF, tokens).
# In production, generate a strong random key and NEVER commit it to git.
# DEBUG=True shows detailed error pages — turn it OFF in production!
# ALLOWED_HOSTS controls which domain names can serve your site.
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.environ.get('DJANGO_DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# ---------------------------------------------------------------------------
# INSTALLED APPS
# ---------------------------------------------------------------------------
# Every app you create (or install via pip) must be listed here.
# Order matters: 'jazzmin' must come before 'django.contrib.admin' so it
# overrides the admin templates. Our custom apps come last.
# Each app handles one business domain:
#   accounts     -> Users, authentication, OTP login
#   vehicles     -> Car inventory (the core product)
#   advertising  -> Banners and promotions for marketing
#   leads        -> Customer leads and appointments
#   chatbot      -> Live chat widget on the website
#   notifications-> SMS sending service (SendAfrica)
#   campaigns    -> Bulk SMS marketing campaigns
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'vehicles',
    'notifications',
    'leads',
    'chatbot',
    'campaigns',
    'advertising',
]

# ---------------------------------------------------------------------------
# MIDDLEWARE
# ---------------------------------------------------------------------------
# Middleware are "processing layers" that every HTTP request passes through.
# Think of them like an assembly line: Security -> Session -> CSRF -> Auth -> etc.
# Each middleware can inspect/modify the request before it reaches your view,
# and inspect/modify the response before it goes back to the browser.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'car_crm.urls'

# ---------------------------------------------------------------------------
# TEMPLATES
# ---------------------------------------------------------------------------
# Templates are HTML files that Django fills in with data from your views.
# 'DIRS' points to our project-level templates/ folder (shared across apps).
# 'APP_DIRS' means Django also looks inside each app's templates/ folder.
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'car_crm.wsgi.application'

# ---------------------------------------------------------------------------
# DATABASE — MySQL (primary) or SQLite (fallback)
# ---------------------------------------------------------------------------
# USE_MYSQL environment variable controls which database we use.
# - If True (default): connects to MySQL using the settings below.
# - If False: uses SQLite (db.sqlite3 in project root).
# SQLite is great for development/testing on your laptop.
# MySQL is what you'd use in production or for team projects.
# The pymysql library acts as a MySQL driver for Django.
USE_MYSQL = os.environ.get('USE_MYSQL', 'True') == 'True'

if USE_MYSQL:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        USE_MYSQL = False

if USE_MYSQL:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'car_crm'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', 'darkknight'),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ---------------------------------------------------------------------------
# USER MODEL
# ---------------------------------------------------------------------------
# We use a custom user model (CustomUser in accounts/models.py) instead of
# Django's built-in User. This lets us log in with phone numbers instead of
# usernames/emails — more natural for a Tanzanian car dealership CRM.
AUTH_USER_MODEL = 'accounts.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# INTERNATIONALIZATION & TIMEZONE
# ---------------------------------------------------------------------------
# Since this CRM is for a Tanzanian car dealership, we set the timezone
# to Africa/Dar_es_Salaam (UTC+3). All dates/times in the database are
# stored in UTC but displayed in this timezone automatically.
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Dar_es_Salaam'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# STATIC & MEDIA FILES
# ---------------------------------------------------------------------------
# Static files = CSS, JavaScript, images that are PART of your code.
# Media files = user-uploaded content (car photos, etc.)
# In production, you'd serve these from a CDN or web server (Nginx).
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# LOGIN / LOGOUT URLS
# ---------------------------------------------------------------------------
# These tell Django where to redirect users based on their login state.
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/'

# ---------------------------------------------------------------------------
# SENDAFRICA SMS API CONFIGURATION
# ---------------------------------------------------------------------------
# SendAfrica (https://api.sendafrica.online) is our SMS gateway provider.
# The API key must be set in the .env file (never committed to git).
# All SMS sending goes through notifications/services.py -> send_sms().
SENDAFRICA_API_KEY = os.environ.get('SENDAFRICA_API_KEY', '')
SENDAFRICA_BASE_URL = 'https://api.sendafrica.online'

# ---------------------------------------------------------------------------
# JAZZMIN — MODERN ADMIN THEME
# ---------------------------------------------------------------------------
# Jazzmin replaces Django's default admin interface with a modern,
# Bootstrap 4-based UI that looks like a real SaaS product.
# All settings below control colors, layout, icons, and navigation.
JAZZMIN_SETTINGS = {
    # -- Branding -----------------------------------------------------------
    'site_title': 'CarDealTZ Admin',       # <title> tag text
    'site_header': 'CarDealTZ',            # Header on the login page
    'site_brand': 'CarDealTZ',             # Text in the top-left brand area
    'site_logo': None,
    'login_logo': None,
    'login_logo_dark': None,
    'site_logo_classes': 'img-circle',
    'site_icon': None,
    'welcome_sign': 'Welcome to CarDealTZ CRM',
    'copyright': 'CarDealTZ',

    # -- Search -- which models appear in the global admin search -----------
    'search_model': ['accounts.CustomUser', 'leads.Lead'],

    # -- User avatar --------------------------------------------------------
    'user_avatar': None,

    # -- Top menu links -----------------------------------------------------
    'topmenu_links': [
        {'name': 'Home', 'url': 'admin:index', 'permissions': ['auth.view_user']},
        {'name': 'Site', 'url': '/', 'new_window': True},
    ],

    # -- User menu (top-right dropdown) -------------------------------------
    'usermenu_links': [
        {'name': 'View Site', 'url': '/', 'new_window': True},
    ],

    # -- Sidebar ------------------------------------------------------------
    'show_sidebar': True,
    'navigation_expanded': True,
    'hide_apps': [],
    'hide_models': [],

    # -- Order of apps/models in the sidebar --------------------------------
    'order_with_respect_to': ['accounts', 'vehicles', 'leads', 'chatbot', 'notifications', 'campaigns'],

    'custom_links': {},

    # -- Icons (Font Awesome 5) for each model ------------------------------
    'icons': {
        'accounts.CustomUser': 'fas fa-users',
        'accounts.OTP': 'fas fa-shield-alt',
        'vehicles.Car': 'fas fa-car',
        'vehicles.CarImage': 'fas fa-image',
        'leads.Lead': 'fas fa-user-tie',
        'leads.Appointment': 'fas fa-calendar-check',
        'chatbot.ChatSession': 'fas fa-comments',
        'chatbot.ChatMessage': 'fas fa-comment-dots',
        'notifications.SmsLog': 'fas fa-sms',
        'campaigns.Campaign': 'fas fa-bullhorn',
        'campaigns.CampaignRecipient': 'fas fa-receipt',
        'auth.Group': 'fas fa-users-cog',
        'auth.User': 'fas fa-user',
        'advertising.Banner': 'fas fa-image',
        'advertising.Promotion': 'fas fa-star',
    },
    'default_icon_parents': 'fas fa-chevron-circle-right',
    'default_icon_children': 'fas fa-circle',
    'related_modal_active': False,
    'custom_css': None,
    'custom_js': None,
    'use_google_fonts_cdn': True,
    'show_ui_builder': False,
    'changeform_format': 'horizontal_tabs',
    'changeform_format_overrides': {},
    'language_chooser': False,
}

# -- Jazzmin UI tweaks (colors, navbar, sidebar) --------------------------
JAZZMIN_UI_TWEAKS = {
    'navbar_small_text': False,
    'footer_small_text': False,
    'body_small_text': False,
    'brand_small_text': False,
    'brand_colour': False,
    'accent': 'accent-primary',
    'navbar': 'navbar-dark navbar-primary',
    'no_navbar_border': False,
    'navbar_fixed': True,
    'layout_boxed': False,
    'footer_fixed': False,
    'sidebar_fixed': True,
    'sidebar': 'sidebar-dark-primary',
    'sidebar_nav_small_text': False,
    'sidebar_disable_expand': False,
    'sidebar_nav_child_indent': False,
    'sidebar_nav_compact_style': False,
    'sidebar_nav_legacy_style': False,
    'sidebar_nav_flat_style': False,
    'theme': 'default',
    'dark_mode_theme': None,
    'button_classes': {
        'primary': 'btn-primary',
        'secondary': 'btn-secondary',
        'info': 'btn-info',
        'warning': 'btn-warning',
        'danger': 'btn-danger',
        'success': 'btn-success',
    },
}
