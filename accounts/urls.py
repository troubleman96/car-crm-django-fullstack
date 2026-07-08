"""
accounts/urls.py
================

PURPOSE:
    Maps URL patterns to view functions for the accounts app.

    This is the "routing table" for everything under the
    /accounts/ prefix.  When a user visits a URL like
    http://example.com/accounts/login/, Django consults this file to
    determine which view function should handle the request.

WHAT YOU'LL LEARN:
    - How Django's URL dispatcher works: path() converts a URL string
      into a call to a view function.
    - The purpose of app_name and the name= parameter — together they
      create "named URL patterns" that you can reference in templates
      ({% url 'accounts:staff_login' %}) and views (redirect('accounts:otp_send')).
    - How to keep your URL configuration clean by splitting it across
      multiple app-level urls.py files, then including them in the
      project's root urls.py.

RELATIONSHIP TO OTHER FILES:
    - This file imports view functions from accounts/views.py.
    - The project's root URL configuration (car_retail/urls.py) includes
      this file using:
          path('accounts/', include('accounts.urls'))
    - Templates use these names, e.g., {% url 'accounts:otp_send' %}
    - Views use these names, e.g., redirect('accounts:otp_verify')
"""

from django.urls import path
# Import ALL views from the views module of THIS app.
# The dot (.) means "the current package" — i.e., accounts/views.py.
from . import views


# -------------------------------------------------------------------
# app_name defines the "namespace" for this app's URL patterns.
# When used with the name= parameter below, it creates fully-qualified
# URL names like 'accounts:staff_login'.
#
# Why namespaces?
#   They prevent naming collisions.  If two different apps both have
#   a URL named 'login', Django needs to know which one you mean.
#   'accounts:login' and 'blog:login' are unambiguous.
# -------------------------------------------------------------------
app_name = 'accounts'


# -------------------------------------------------------------------
# urlpatterns is a list of path() objects.  Django processes them in
# order and returns the first match.  If no pattern matches, Django
# returns a 404 error.
#
# Each path() takes:
#   1. route  – the URL string (without the /accounts/ prefix, because
#               the root urls.py already strips that off).
#   2. view   – the view function to call.
#   3. name   – a unique identifier for this URL, used for reverse
#               URL resolution (the {% url %} tag and redirect()).
# -------------------------------------------------------------------
urlpatterns = [
    # Staff authentication
    path('login/', views.staff_login_view, name='staff_login'),
    path('logout/', views.staff_logout_view, name='staff_logout'),

    # Customer OTP (passwordless) authentication
    path('otp/send/', views.customer_otp_send, name='otp_send'),
    path('otp/verify/', views.customer_otp_verify, name='otp_verify'),
]
