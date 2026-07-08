"""
leads/urls.py — URL configuration for the Leads app.

This module maps URL patterns to view functions. When a user visits
a URL like /leads/book/, Django checks the patterns here and calls
the corresponding view function.

This file is included from the project's main urls.py via something like:
    path('leads/', include('leads.urls'))
"""

# -------------------------------------------------------------------
# path:    The primary function for defining URL patterns in Django 2+.
#          It replaces the older url() pattern from Django 1.x.
# include: Not used here, but typically used in the root URLconf to
#          pull in other app URLconfs.
# -------------------------------------------------------------------
from django.urls import path

# Import views from the current app's views module.
# The dot (.) means "this package" — i.e., leads/views.py.
from . import views

# -------------------------------------------------------------------
# app_name: Defines the "application namespace" for URL reversing.
#
# When you have multiple apps, URL names might collide (e.g., two
# apps could both have a 'book' view). Setting app_name lets you
# use the colon syntax to disambiguate, e.g.:
#   {% url 'leads:book' %}   or   reverse('leads:book')
#
# This value must match the namespace used in the project's main
# urls.py when including this app's URLs.
# -------------------------------------------------------------------
app_name = 'leads'

# -------------------------------------------------------------------
# urlpatterns: The list of route-to-view mappings Django checks
#              in order (top to bottom). The first match wins.
#
# Each entry uses the path() function:
#   path(route, view, kwargs=None, name=None)
#
#   route: A URL string (can include <converter:name> captures).
#   view:  The view function (or class-based view.as_view()).
#   name:  A unique identifier for this URL — used for reverse
#          resolution (so you can change URLs without updating
#          every template link).
# -------------------------------------------------------------------
urlpatterns = [
    # Matches /leads/book/ and calls views.book_appointment.
    # The name='book' lets us refer to this URL as 'leads:book'.
    path('book/', views.book_appointment, name='book'),
]
