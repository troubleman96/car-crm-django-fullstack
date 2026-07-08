"""
leads/views.py — View functions for booking appointments.

This module contains the `book_appointment` view, which handles both:
  - GET:  Renders the booking form with available cars.
  - POST: Validates input, creates/retrieves a Lead, creates an Appointment,
          sends an SMS confirmation, and redirects to the landing page.

Flow summary:
  1. Visitor arrives on the booking page (optionally with a ?car=ID param).
  2. Fills in phone number, appointment type, and preferred date/time.
  3. On POST, the view:
       a. Finds or creates a Lead by phone number (get_or_create).
       b. Creates an Appointment linked to that Lead.
       c. Sends a confirmation SMS via the notification service.
       d. Redirects back to the vehicle landing page with a success message.
"""

# -------------------------------------------------------------------
# render:    Renders an HTML template with a context dictionary.
# redirect:  Sends an HTTP redirect response to another URL.
# get_object_or_404: Fetches an object or returns HTTP 404 if not found.
# -------------------------------------------------------------------
from django.shortcuts import render, redirect, get_object_or_404

# Django's built-in "messages" framework — a way to flash one-time
# notifications to the user (shown on the next page load).
from django.contrib import messages

# timezone-aware datetime utilities. Django recommends using
# timezone.now() instead of datetime.now() because it respects the
# project's timezone setting (settings.TIME_ZONE).
from django.utils import timezone

# Our own Lead and Appointment models — these define the database tables.
from .models import Lead, Appointment

# The Car model from the vehicles app — we need it to look up and
# validate which car the user is interested in.
from vehicles.models import Car

# send_sms: A custom utility function from the notifications app.
# It takes a phone number and message text, then sends an SMS
# (e.g., via Africa's Talking or Twilio API).
from notifications.services import send_sms


def book_appointment(request):
    """
    Handle the appointment booking flow (GET = form, POST = process).

    This view is accessed at the URL /leads/book/ (defined in leads/urls.py).
    """

    # ------------------------------------------------------------------
    # GET handling — reading the optional ?car= query parameter.
    #
    # When a user clicks "Book Test Drive" from a specific car's page,
    # the link might be /leads/book/?car=5. This pre-selects the car
    # in the booking form so the user doesn't have to choose it again.
    # ------------------------------------------------------------------
    car_id = request.GET.get('car')  # Returns None if 'car' isn't in the URL
    car = None
    if car_id:
        # get_object_or_404 tries to fetch the Car. If the ID doesn't
        # exist OR the car isn't 'available', it raises Http404.
        # The filter(status='available') ensures we don't offer cars
        # that are already sold.
        car = get_object_or_404(Car, id=car_id, status='available')

    # ------------------------------------------------------------------
    # POST handling — the user submitted the booking form.
    # ------------------------------------------------------------------
    if request.method == 'POST':
        # --- Extract and clean form data ---
        # .strip() removes leading/trailing whitespace that users might
        # accidentally include (e.g., " 0712345678 " -> "0712345678").
        phone = request.POST.get('phone', '').strip()
        appointment_type = request.POST.get('type', 'test_drive')
        car_id = request.POST.get('car_id')
        scheduled_at_str = request.POST.get('scheduled_at', '')

        # --- Validation: phone is required ---
        # If no phone is provided, re-render the form with an error message
        # and preserve the previously selected car/cars so the user doesn't
        # have to start over.
        if not phone:
            messages.error(request, 'Phone number is required.')
            return render(request, 'leads/book.html', {
                'car': car,
                'cars': Car.objects.filter(status='available'),
            })

        # --- Look up the selected car (optional) ---
        interested_car = None
        if car_id:
            # We use .filter(...).first() instead of get_object_or_404 here
            # because the car_id might be empty or invalid. This is safer
            # — we silently treat a missing/bad car_id as "no car selected".
            interested_car = Car.objects.filter(id=car_id).first()

        # ------------------------------------------------------------------
        # get_or_create: The "find or create" pattern.
        #
        # Lead.objects.get_or_create(phone=phone, defaults={...})
        #
        # This tries to find a Lead with the given phone number:
        #   - If found: returns (existing_lead, False)
        #   - If not found: creates a new Lead with the phone AND the
        #     fields in 'defaults', then returns (new_lead, True)
        #
        # Why use this? A returning customer with the same phone number
        # should not create a duplicate Lead — we want to keep their
        # history of appointments together under one Lead record.
        #
        # The underscore (_) is a Python convention for "I don't need
        # this value" — here we throw away the boolean "created" flag.
        # ------------------------------------------------------------------
        lead, _ = Lead.objects.get_or_create(
            phone=phone,
            defaults={'source': 'website', 'interested_car': interested_car},
        )

        # --- Parse the scheduled datetime ---
        # The browser sends the datetime as an ISO-8601 string (e.g.,
        # "2025-06-15T14:30"). We convert it to a timezone-aware
        # datetime object using timezone.datetime.fromisoformat().
        try:
            scheduled_at = timezone.datetime.fromisoformat(scheduled_at_str)
        except (ValueError, TypeError):
            # If parsing fails (empty string, bad format), fall back to
            # "tomorrow at this time" as a sensible default.
            scheduled_at = timezone.now() + timezone.timedelta(days=1)

        # --- Create the Appointment record ---
        # Appointment.objects.create(...) is a shortcut for creating a
        # new instance and saving it in one step.
        appointment = Appointment.objects.create(
            lead=lead,
            car=interested_car,
            type=appointment_type,
            scheduled_at=scheduled_at,
            status='confirmed',  # Booked appointments start as 'confirmed'
        )

        # ------------------------------------------------------------------
        # SMS notification — build a human-readable text message and send it.
        #
        # This uses the custom notifications service. In a real deployment,
        # send_sms would make an API call to an SMS gateway (e.g.,
        # Africa's Talking). For now it might just print to console or
        # log the message for testing purposes.
        # ------------------------------------------------------------------
        car_info = f'{interested_car.make} {interested_car.model}' if interested_car else 'a car'
        sms_text = (
            f'Your {appointment.get_type_display()} for {car_info} '
            f'is booked for {scheduled_at.strftime("%A, %d %B %Y at %H:%M")}. '
            f'Thank you!'
        )
        send_sms(phone, sms_text)

        # --- Flash a success message and redirect ---
        # The success message will appear on the next page (usually on
        # the vehicles landing page) thanks to Django's messages
        # middleware and the template's {% if messages %} block.
        messages.success(request, 'Appointment booked! Confirmation SMS sent.')

        # Redirect to the 'vehicles:landing' URL (defined in vehicles/urls.py).
        # The redirect pattern (POST -> Redirect -> GET) prevents the
        # browser from resubmitting the form if the user hits Refresh.
        return redirect('vehicles:landing')

    # ------------------------------------------------------------------
    # GET fallback — render the empty booking form.
    #
    # If the request is not a POST (i.e., it's a GET, HEAD, etc.),
    # we show the form. The context includes:
    #   - 'car': The pre-selected car (if any) passed via ?car=ID
    #   - 'cars': A list of all available cars for the dropdown/selection
    # ------------------------------------------------------------------
    return render(request, 'leads/book.html', {
        'car': car,
        'cars': Car.objects.filter(status='available'),
    })
