"""
vehicles/urls.py
================

URL configuration for the 'vehicles' Django app.

This file maps URL patterns (what comes after the domain name in a web address)
to view functions. When a user visits a URL, Django walks through the patterns
in order and calls the first view whose pattern matches.

These app-specific URLs are then "included" in the project's main urls.py
(typically at the project root level), which prefixes them with /vehicles/.

Example flow:
    1. User visits:  http://example.com/vehicles/car/3/
    2. Root urls.py matches 'vehicles/' and includes this file
    3. This file matches 'car/3/' → calls views.car_detail(car_id=3)
    4. The view function runs and returns an HTML response
"""

# ---------------------------------------------------------------------------
# django.urls.path: The main function for defining URL patterns in Django 2.0+.
# It replaces the older re_path() / url() style with a simpler syntax.
# ---------------------------------------------------------------------------
from django.urls import path

# ---------------------------------------------------------------------------
# Import views from the current app's views.py.
# The dot in 'from . import views' means "from the same directory/package".
# ---------------------------------------------------------------------------
from . import views

# ---------------------------------------------------------------------------
# app_name sets the "application namespace" for this URL configuration.
#
# Why is this important?
#   When you have multiple apps (vehicles, advertising, etc.), they might have
#   views with the same name (e.g., both might have a "detail" view). Namespaces
#   let Django tell them apart.
#
# In templates, you'd refer to a URL like this:
#   {% url 'vehicles:car_detail' car_id=5 %}
#   {% url 'vehicles:landing' %}
#
# The 'vehicles:' prefix comes from app_name = 'vehicles'.
# Without app_name, you'd need to be careful that URL names don't collide
# across different apps.
# ---------------------------------------------------------------------------
app_name = 'vehicles'

# ---------------------------------------------------------------------------
# urlpatterns is a list of path() calls. Django checks each pattern in order
# and stops at the first match.
#
# path() arguments:
#   1. route    → a URL string (without domain, without leading/trailing slash
#                 in modern Django — it handles slashes automatically).
#   2. view     → the view function to call when the URL matches.
#   3. name     → a unique name for this URL, used for reverse URL lookups
#                 (e.g., in {% url %} template tags or redirect() in views).
#
# Angle brackets < > in the route capture URL segments:
#   <int:car_id>  captures an integer and passes it as the 'car_id' kwarg
#   <str:slug>    captures a string
#   <uuid:id>     captures a UUID
#   <path:path>   captures any path (including slashes)
# ---------------------------------------------------------------------------
urlpatterns = [
    # The homepage of the vehicles section.
    # '' means: match the root of the vehicles app (i.e., /vehicles/).
    # Calls views.landing_page.
    path('', views.landing_page, name='landing'),

    # Detail page for a single car.
    # Example matches: /vehicles/car/1/, /vehicles/car/42/, etc.
    # The <int:car_id> part is captured from the URL and passed to the view
    # as the 'car_id' parameter.
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
]
