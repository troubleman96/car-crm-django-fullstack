"""
car_crm/urls.py
===============

The URL configuration (a.k.a. "URLconf") for the Car Retail CRM project.

This is the central routing table for the entire Django application.
When a web request arrives, Django starts at the top of urlpatterns
and tries each URL pattern IN ORDER until one matches the requested
path. The first match determines which view function (or sub-URLconf)
handles the request.

How URL routing works in Django:
  1. A user visits e.g. http://example.com/leads/new/
  2. Django strips the domain, leaving the path "/leads/new/".
  3. It walks through urlpatterns top-to-bottom.
  4. The pattern 'leads/' (with include()) matches the prefix "/leads/".
  5. Django strips the matched prefix ("leads/") and passes the
     remainder ("new/") to the leads/urls.py URLconf.
  6. That sub-URLconf then matches "new/" to its view.

This file also handles:
  - Static/media file serving during development (DEBUG mode).
  - The built-in Django admin at /admin/.

Apps included:
  accounts/ → URLs for user authentication (login, logout, register).
  (empty)   → Vehicles is mounted at root (e.g. /, /vehicles/...).
  leads/    → Lead management URLs.
  chatbot/  → Chatbot-related URLs.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


# -----------------------------------------------------------------------
# urlpatterns — the master list of URL routes
# -----------------------------------------------------------------------
# Each element is a path() call that maps a URL pattern to either:
#   - a view function (e.g. admin.site.urls is a set of views)
#   - another URLconf via include() (which delegates routing)
#
# path(route, view, kwargs=None, name=None)
#   route : str — the URL pattern (e.g. 'admin/', 'leads/')
#   view  : the view function or include() result
#   name  : a unique identifier for reverse URL lookups
#
# Django processes path() patterns in order. More specific patterns
# should come before catch-all patterns.
#
# Trailing slashes: Django by default appends a slash to URLs that
# don't have one (APPEND_SLASH setting). All patterns here use a
# trailing slash convention.
urlpatterns = [
    # --- Django Admin ------------------------------------------------
    # admin.site.urls is a set of pre-built views that power the
    # entire admin interface. Access at http://example.com/admin/.
    path('admin/', admin.site.urls),

    # --- Accounts (authentication) -----------------------------------
    # All URLs starting with /accounts/ are handled by the accounts
    # app. The include() function points Django to accounts/urls.py,
    # which defines the actual route-to-view mappings.
    path('accounts/', include('accounts.urls')),

    # --- Vehicles (mounted at root) ----------------------------------
    # Blank string '' means this is mounted at the site root.
    # If vehicles/urls.py has a pattern for '', it handles the
    # homepage at http://example.com/.
    path('', include('vehicles.urls')),

    # --- Leads -------------------------------------------------------
    # All URLs starting with /leads/ are delegated to leads/urls.py.
    path('leads/', include('leads.urls')),

    # --- Chatbot -----------------------------------------------------
    # All URLs starting with /chatbot/ are delegated to chatbot/urls.py.
    path('chatbot/', include('chatbot.urls')),
]

# -----------------------------------------------------------------------
# Static/media file serving (development only)
# -----------------------------------------------------------------------
# During development (DEBUG=True), Django can serve user-uploaded media
# files (images, documents etc.) directly. The static() helper appends
# the necessary URL patterns to urlpatterns.
#
# In production, a web server like Nginx would serve media files
# directly — Django should never serve media in production because it
# is slow and insecure.
if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,                # e.g. '/media/'
        document_root=settings.MEDIA_ROOT, # e.g. '/var/www/media/'
    )
