"""
accounts/views.py
=================

PURPOSE:
    Contains all the view functions (request handlers) for the accounts app.
    Each view corresponds to a URL pattern defined in accounts/urls.py.

    There are two authentication flows in this project:

    1. STAFF LOGIN (username + password)
        - Staff members (dealership employees) log in with their phone number
          and password through a standard Django form.
        - After login they are redirected to /admin/ (Django's admin site).

    2. CUSTOMER LOGIN (OTP / SMS code)
        - Website customers log in by entering their phone number and then
          typing a 6-digit code sent via SMS.
        - No password is involved — the OTP *is* the authenticator.
        - This flow uses Django sessions to remember the phone number
          between the "send" step and the "verify" step.

WHAT YOU'LL LEARN:
    - How Django views receive an HttpRequest and return an HttpResponse.
    - How to use Django's authentication system (login, logout, authenticate).
    - How to work with sessions to pass data between requests.
    - How OTP-based (passwordless) authentication works in practice.
    - The request-response cycle: URL → view → template (or redirect).

RELATIONSHIP TO OTHER FILES:
    - accounts/forms.py  defines the forms that these views validate.
    - accounts/models.py  provides CustomUser and OTP that the views query.
    - accounts/urls.py   maps URL patterns to these view functions.
    - notifications/services.py  provides send_sms() and normalize_phone().
"""

import random                           # For generating random OTP codes.
from datetime import timedelta          # For setting OTP expiry.
from django.utils import timezone       # Timezone-aware 'now'.
from django.shortcuts import render, redirect  # Render templates & redirect.
from django.contrib.auth import login, authenticate, logout  # Auth helpers.
from django.contrib import messages     # Flash messages for user feedback.
from django.db.models import Q          # For complex ORM queries (AND/OR).

# Local imports — our own models, forms, and notification service.
from .models import CustomUser, OTP
from .forms import StaffLoginForm, PhoneForm, OTPVerifyForm
from notifications.services import send_sms, normalize_phone


# ===================================================================
# STAFF LOGIN VIEW
# ===================================================================
# URL:  /accounts/login/
# Template: accounts/staff_login.html
#
# Flow:
#   1. If the user is already logged in, skip the form and redirect them
#      straight to the admin dashboard.
#   2. If the request is POST, validate the StaffLoginForm.
#   3. On success, the form's clean() method has already authenticated the
#      user and stored the user object in form.cleaned_data['user'].
#   4. Call Django's login() to create the session, then redirect to /admin/.
#   5. If GET (or validation fails), just render the login template.
# ===================================================================

def staff_login_view(request):
    """
    Handle staff (admin) login via phone + password.

    This view is intentionally separate from the customer OTP flow.
    Staff always need a password; customers never do.
    """
    # ---------- Already logged in?  Skip the form. ----------
    # request.user.is_authenticated is True when the request carries a valid
    # session for an existing user.  We check this early so we don't show
    # the login page to someone who is already authenticated.
    if request.user.is_authenticated:
        return redirect('/admin/')

    # ---------- Build the form ----------
    # request.POST or None  is a Django idiom:
    #   - On GET:  request.POST is empty → form is unbound (no data, no errors).
    #   - On POST: request.POST contains submitted data → form is bound.
    form = StaffLoginForm(request.POST or None)

    # ---------- Process the form on POST ----------
    if request.method == 'POST' and form.is_valid():
        # form.is_valid() calls the form's clean() method, which runs
        # validation including authentication.  If it passes, the
        # authenticated user object is stored in cleaned_data['user'].
        user = form.cleaned_data['user']

        # login() creates a session for this user in Django's session
        # backend (database by default).  It also attaches the user to
        # request.user for the rest of this request cycle.
        login(request, user)

        # Redirect to the admin dashboard.
        return redirect('/admin/')

    # ---------- Render the template (GET or invalid POST) ----------
    # The template receives the form so it can display fields and errors.
    return render(request, 'accounts/staff_login.html', {'form': form})


# ===================================================================
# STAFF LOGOUT VIEW
# ===================================================================
# URL:  /accounts/logout/
#
# Very simple — calls Django's logout() which flushes the session, then
# redirects to the homepage.
# ===================================================================

def staff_logout_view(request):
    """
    Log the current user out and redirect to the homepage.

    logout() does three things:
        1. Flushes the session data.
        2. Calls request.user.save() to update last_login.
        3. Sets request.user to an AnonymousUser for this request.
    """
    logout(request)
    return redirect('/')


# ===================================================================
# CUSTOMER OTP — SEND
# ===================================================================
# URL:  /accounts/otp/send/
# Template: accounts/otp_send.html
#
# Flow:
#   1. Display a form asking for the customer's phone number.
#   2. On POST, validate the number, normalise it, generate a random
#      6-digit OTP, save it to the database, and attempt to send it via SMS.
#   3. If SMS sending fails, show an error message and stay on the page.
#   4. If SMS sending succeeds, store the phone in the session and redirect
#      to the OTP verification step.
#
# IMPORTANT: In development mode, the OTP is printed to the console (the
# print() statement) so you don't need real SMS credits to test.
# ===================================================================

def customer_otp_send(request):
    """
    Step 1 of the customer OTP flow — collect phone number and send a code.

    Session usage:
        After a successful SMS send, we store the phone number in
        request.session['otp_phone'].  The next view (customer_otp_verify)
        reads this value to know *who* is trying to verify a code.
        This prevents a malicious user from tampering with the phone number
        in the verification step.
    """
    form = PhoneForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # ---------- Normalise the phone number ----------
        # normalize_phone() strips spaces/dashes and converts the number
        # to international format (+2557XXXXXXXX).  This is critical because
        # the SMS API (SendAfrica) expects a standard format.
        phone = normalize_phone(form.cleaned_data['phone'])

        # ---------- Generate a random 6-digit code ----------
        # random.randint(0, 999999) gives us a number between 0 and 999999.
        # The f-string format :06d  pads it to exactly 6 digits, so e.g.
        # 4829 becomes "004829".  This ensures the code is always 6 chars.
        code = f'{random.randint(0, 999999):06d}'

        # DEV NOTE: In production you'd remove or guard this print statement.
        # It prints the OTP to the console so developers can test without
        # actually sending SMS messages.
        print(f'[DEV] OTP for {phone}: {code}')

        # ---------- Set the expiry time (5 minutes from now) ----------
        # timezone.now() returns the current time in the project's timezone
        # (set in settings.py).  timedelta(minutes=5) adds 5 minutes.
        expires_at = timezone.now() + timedelta(minutes=5)

        # ---------- Save the OTP to the database ----------
        # We use OTP.objects.create() which is a shortcut for:
        #   otp = OTP(...)
        #   otp.save()
        OTP.objects.create(phone=phone, code=code, expires_at=expires_at)

        # ---------- Send the SMS via the notification service ----------
        # send_sms() calls the SendAfrica API and returns True if accepted,
        # False otherwise.  It also logs the attempt in SmsLog.
        sms_sent = send_sms(phone, f'Your verification code is {code}. Valid for 5 minutes.')

        if not sms_sent:
            # DEV: SMS failed but OTP was printed to console — allow proceed.
            # In production, remove this fallback and let the error show.
            print(f'[DEV] SMS send failed — OTP {code} is still valid for {phone}')
            request.session['otp_phone'] = phone
            return redirect('accounts:otp_verify')

        # ---------- Remember the phone in the session ----------
        # We store the phone number so the verify view can retrieve it
        # without making the customer type it again.  The session is
        # stored server-side (in the django_session table) with a cookie
        # linking it to this browser.
        request.session['otp_phone'] = phone

        # Redirect to the verification page.
        # The named URL pattern 'accounts:otp_verify' is defined in
        # accounts/urls.py as name='otp_verify'.
        return redirect('accounts:otp_verify')

    # GET request — just show the blank form.
    return render(request, 'accounts/otp_send.html', {'form': form})


# ===================================================================
# CUSTOMER OTP — VERIFY
# ===================================================================
# URL:  /accounts/otp/verify/
# Template: accounts/otp_verify.html
#
# Flow:
#   1. Read the phone number from the session (placed there by
#      customer_otp_send).
#   2. If there's no phone in the session, the customer skipped the send
#      step, so redirect them back to it.
#   3. On POST, validate the code and look up a matching OTP record that:
#        - belongs to that phone number
#        - has the exact code they typed
#        - has NOT been used yet (is_used=False)
#        - has NOT expired yet (expires_at > now)
#   4. If found:
#        a. Mark the OTP as used (prevents replay).
#        b. Find or create a CustomUser for that phone number.
#        c. Log the user in.
#        d. Redirect to the page they were trying to visit (or homepage).
#   5. If NOT found, show an error and let them try again.
# ===================================================================

def customer_otp_verify(request):
    """
    Step 2 of the customer OTP flow — verify the code the user entered.

    Key design decisions:
        - The phone number comes from the session, NOT from the form.
          This prevents a user from entering one phone for the SMS and
          a different one for the code (session tampering protection).
        - get_or_create() is used so that a CustomUser row is created the
          FIRST time a phone successfully verifies an OTP.  Subsequent
          logins just fetch the existing user.
        - 'booking_next' in session is an optional redirect target set by
          the booking app — e.g., if a customer starts a booking before
          logging in, they are redirected back to complete it after auth.
    """
    # ---------- Retrieve the phone from the session ----------
    # .get('otp_phone') returns None if the key doesn't exist, rather
    # than raising a KeyError.  This is safer than session['otp_phone'].
    phone = request.session.get('otp_phone')

    if not phone:
        # If there is no phone in the session, the customer hasn't gone
        # through the send step.  Redirect them to the start of the flow.
        return redirect('accounts:otp_send')

    form = OTPVerifyForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        # ---------- Look up the OTP ----------
        # We use a complex filter with Q objects:
        #   Q(phone=phone)       – must match the phone
        #   & Q(code=code)       – AND must match the code
        #   & Q(is_used=False)   – AND must NOT have been used before
        #   & Q(expires_at__gt=now) – AND must not be expired
        #                              (__gt means "greater than")
        # .first() returns the first matching row or None if no match.
        code = form.cleaned_data['code']
        now = timezone.now()
        otp = OTP.objects.filter(
            Q(phone=phone) & Q(code=code) & Q(is_used=False) & Q(expires_at__gt=now)
        ).first()

        if otp:
            # ---------- Mark the OTP as used ----------
            # This is crucial!  If we didn't set is_used=True, someone
            # could reuse the same code multiple times (a "replay attack").
            # Once used, the filter above (is_used=False) will exclude it.
            otp.is_used = True
            otp.save()

            # ---------- Get or create the CustomUser ----------
            # get_or_create() returns a tuple: (user, created).
            #   - If a CustomUser with this phone already exists, it fetches it.
            #   - If not, it creates one with the defaults we specify.
            # 'created' is True if a new user was created, False otherwise.
            # We don't need the 'created' flag here, so we use underscore.
            user, _ = CustomUser.objects.get_or_create(
                phone=phone,
                defaults={
                    'is_customer': True,
                    'is_staff': False,    # Customers are never staff.
                },
            )

            # ---------- Log the user in ----------
            # Same login() call used in the staff view — creates a session.
            login(request, user)

            # ---------- Redirect: booking page or home ----------
            # If the user was trying to access a booking page before logging
            # in, the booking app stored the redirect URL in the session as
            # 'booking_next'.  We pop it (retrieve and remove) so it's not
            # reused accidentally.  Default to '/' (homepage).
            next_url = request.session.pop('booking_next', '/')
            return redirect(next_url)

        # ---------- Invalid code — show an error ----------
        messages.error(request, 'Invalid or expired code.')

    # GET or invalid POST — show the verification form.
    return render(request, 'accounts/otp_verify.html', {'form': form})
