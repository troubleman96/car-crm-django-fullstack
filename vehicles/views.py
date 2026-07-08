"""
vehicles/views.py
=================

Views are the "V" in Django's MTV pattern (called "Controller" in other
frameworks like MVC). A view is a Python function (or class) that:

    1. Receives an HTTP request (from a user's browser)
    2. Does some work (queries the database, processes form data, etc.)
    3. Returns an HTTP response (usually a rendered HTML page)

This file contains the views for the 'vehicles' app. Each view function maps
to a URL (defined in urls.py) and renders a Django template.
"""

# ---------------------------------------------------------------------------
# render()      → Combines a template with context data and returns an
#                 HttpResponse. This is the standard way to return HTML pages.
# get_object_or_404() → Tries to fetch an object from the DB; if not found,
#                       raises Http404 (returns a 404 page to the browser).
# ---------------------------------------------------------------------------
from django.shortcuts import render, get_object_or_404

# ---------------------------------------------------------------------------
# timezone provides timezone-aware datetime helpers.
# timezone.now() returns the current datetime, respecting the TIME_ZONE
# setting in settings.py. This is safer than Python's datetime.datetime.now()
# because it's timezone-aware — important when filtering dates!
# ---------------------------------------------------------------------------
from django.utils import timezone

# ---------------------------------------------------------------------------
# Import our models so we can query the database.
# Using a relative import (from .models) means "from the same app's models.py".
# We also import from the 'advertising' app — cross-app imports like this are
# common in Django; apps are meant to work together.
# ---------------------------------------------------------------------------
from .models import Car
from advertising.models import Banner, Promotion


def landing_page(request):
    """
    The homepage / landing page of the car dealership website.

    This view gathers three categories of data and passes them all to the
    template, which renders the full homepage HTML.

    request parameter:
        Every Django view receives the HttpRequest object as its first argument.
        It contains everything about the user's request: URL, headers, GET/POST
        data, session info, the current user, etc.
    """

    # -------------------------------------------------------------------
    # Car.objects is the model's "manager" — it's how we query the database.
    # Car.objects.all()       → fetch ALL cars
    # Car.objects.filter(...) → fetch cars matching conditions
    #
    # Here we filter to only show cars with status='available'.
    # This means sold/reserved cars are hidden from the public listing.
    #
    # .prefetch_related('images'):
    #   This is a PERFORMANCE optimization.
    #   Without it, if we loop over 100 cars and access car.images for each,
    #   Django would run 101 SQL queries (1 to get cars + 100 to get images).
    #   With prefetch_related, Django runs only 2 queries total — one for
    #   cars and one for ALL related images, then matches them in Python.
    #
    #   Use prefetch_related for ManyToMany and reverse ForeignKey lookups
    #   (like Car → CarImage via related_name='images').
    #   Use select_related for forward ForeignKey lookups (like Promotion → Car).
    # -------------------------------------------------------------------
    cars = Car.objects.filter(status='available').prefetch_related('images')

    # Filter to only active banners (is_active=True).
    # In Django, field lookups use double-underscore syntax:
    #   field__lookuptype = value
    # is_active=True is a shorthand for is_active__exact=True.
    banners = Banner.objects.filter(is_active=True)

    # Capture the current timestamp — we need this once and reuse it below.
    now = timezone.now()

    # -------------------------------------------------------------------
    # Find promotions that are:
    #   - Active (is_active=True)
    #   - Started already (starts_at <= now)
    #   - Haven't ended yet (ends_at >= now)
    #
    # Lookups used:
    #   starts_at__lte=now  →  starts_at "less than or equal to" now
    #   ends_at__gte=now    →  ends_at "greater than or equal to" now
    #
    # Together these filter to only "currently running" promotions.
    #
    # .select_related('car'):
    #   Unlike prefetch_related (used above), select_related works on
    #   ForeignKey relationships going FORWARD (Promotion → Car).
    #   It does this with a SQL JOIN — so the car data is fetched in the
    #   same query as the promotion, avoiding N+1 queries.
    # -------------------------------------------------------------------
    promotions = Promotion.objects.filter(
        is_active=True,
        starts_at__lte=now,
        ends_at__gte=now,
    ).select_related('car')

    # -------------------------------------------------------------------
    # render() takes:
    #   1. The request object
    #   2. A template path (Django looks in templates/ directories of all
    #      installed apps, plus any TEMPLATES.DIRS in settings.py)
    #   3. A dictionary of "context" — variables that the template can use
    #
    # Inside the template, these variables become available as:
    #   {{ cars }}, {{ banners }}, {{ promotions }}
    # -------------------------------------------------------------------
    return render(request, 'vehicles/landing.html', {
        'cars': cars,
        'banners': banners,
        'promotions': promotions,
    })


def car_detail(request, car_id):
    """
    Shows a single car's detailed information page.

    URL pattern (defined in urls.py):
        path('car/<int:car_id>/', views.car_detail, name='car_detail')

    The <int:car_id> part of the URL captures an integer from the URL path and
    passes it to this function as the 'car_id' parameter.

    Example:
        User visits /car/5/  →  car_id=5  →  this view fetches Car with id=5
    """

    # -------------------------------------------------------------------
    # get_object_or_404 is a convenience shortcut for:
    #
    #   try:
    #       car = Car.objects.get(id=car_id)
    #   except Car.DoesNotExist:
    #       raise Http404("No Car matches the given query.")
    #
    # If the car doesn't exist (e.g., someone visits /car/9999/), the user
    # receives a 404 "Page Not Found" response instead of a 500 error.
    #
    # We pass a queryset (Car.objects.prefetch_related('images')) instead of
    # just Car so we can chain prefetch_related — this way the images are
    # fetched efficiently in the same request.
    # -------------------------------------------------------------------
    car = get_object_or_404(Car.objects.prefetch_related('images'), id=car_id)

    # Render a detail template with just the single car object.
    return render(request, 'vehicles/car_detail.html', {'car': car})
