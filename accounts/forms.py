"""
accounts/forms.py
=================

PURPOSE:
    Defines Django Form classes used by the accounts app's views.

    Forms are the bridge between the HTML templates and the Python code.
    They handle:
        - Rendering HTML input fields (when the template uses {{ form }}).
        - Validating user input (cleaning / error checking).
        - Running custom business logic (e.g., authenticating the user)
          during the validation phase.

WHAT YOU'LL LEARN:
    - The difference between forms.Form (standalone) vs. forms.ModelForm
      (tied to a model).  All three forms here are plain Forms because
      they don't map directly to a single model save.
    - How form.clean() methods work — they are the "global validation"
      step that runs after every individual field has been validated.
    - How Django's authenticate() function works with a custom user model
      that uses 'phone' as the USERNAME_FIELD.
    - The normalise-then-validate pattern: we clean up the phone number
      BEFORE checking it against the database.

RELATIONSHIP TO OTHER FILES:
    - accounts/views.py  imports and uses these forms in staff_login_view,
                         customer_otp_send, and customer_otp_verify.
    - accounts/models.py  is queried indirectly — authenticate() looks up
                          the CustomUser table.
    - notifications/services.py  provides normalize_phone() which is used
                                 by two of the three forms here.
"""

from django import forms
from django.contrib.auth import authenticate

# Import the phone normalisation helper from the notifications app.
# This ensures phone numbers are stored and compared in a consistent
# international format (+2557XXXXXXXX) throughout the project.
from notifications.services import normalize_phone


# ===================================================================
# STAFF LOGIN FORM
# ===================================================================
# This form handles the traditional username+password (actually phone+
# password) login for admin staff.  It has two fields:
#
#   1. phone    – The staff member's phone number.
#   2. password – Their password (rendered as <input type="password">).
#
# The form's clean() method performs authentication.  This is a common
# Django pattern: the form validates the credentials and, on success,
# stores the authenticated user object so the view can simply call
# login(request, user).
# ===================================================================

class StaffLoginForm(forms.Form):
    """
    Form for staff (admin) login with phone number and password.

    Fields:
        phone    – A plain text input (rendered as <input type="text">).
        password – A password input (rendered as <input type="password">)
                   that hides the characters as the user types.

    Validation flow (in order):
        1. Django checks that both fields are present and satisfy their
           basic constraints (max_length, required, etc.).
        2. clean() runs next — our custom logic:
            a. Normalise the phone number to international format.
            b. Call Django's authenticate(phone=..., password=...).
            c. If authentication fails, raise ValidationError.
            d. If the user is not a staff member, raise ValidationError.
            e. Store the authenticated user in cleaned_data['user'].
    """

    phone = forms.CharField(max_length=15, label='Phone Number')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    def clean(self):
        """
        Global form validation (runs after individual field validation).

        Why override clean() instead of clean_<field>()?
            Because authentication needs BOTH phone AND password together.
            clean_<field>() methods only see one field at a time.  clean()
            sees all cleaned_data at once, which is what we need.

        Returns:
            The cleaned_data dictionary (with the authenticated user added).

        Raises:
            forms.ValidationError – displayed as a non-field error in the
                                    template (accessible via
                                    {{ form.non_field_errors }}).
        """
        # super().clean() runs the default validation and returns the
        # cleaned_data dictionary (values that passed individual field checks).
        cleaned = super().clean()

        phone = cleaned.get('phone')
        password = cleaned.get('password')

        # Only attempt authentication if both fields have values.
        # If either is missing, the individual field validators will already
        # have produced an error, so we don't add another one here.
        if phone and password:
            # ---------- Normalise the phone number ----------
            # The user might type "0712345678", "0712 345 678", or
            # "+255712345678".  We normalise to "+255712345678" so the
            # database lookup works regardless of input format.
            phone = normalize_phone(phone)

            # ---------- Authenticate ----------
            # authenticate() is a Django built-in that:
            #   1. Looks up a user whose USERNAME_FIELD == phone.
            #   2. Checks the password against the stored hash.
            #   3. Returns the user object on success, or None on failure.
            # Because we set USERNAME_FIELD = 'phone' in CustomUser,
            # Django knows to use the 'phone' column for the lookup.
            user = authenticate(phone=phone, password=password)

            if user is None:
                # authenticate() returns None when:
                #   - No user with that phone exists, OR
                #   - The password doesn't match the stored hash.
                # We deliberately don't say WHICH one, to avoid leaking
                # information about which phone numbers are registered.
                raise forms.ValidationError('Invalid phone number or password.')

            # ---------- Check staff status ----------
            # Even if the phone+password are correct, we must ensure the
            # user has staff privileges.  Regular customers should not be
            # able to log in via this form.
            if not user.is_staff:
                raise forms.ValidationError('This account does not have staff access.')

            # ---------- Store the user in cleaned_data ----------
            # The view will retrieve it as form.cleaned_data['user'].
            cleaned['user'] = user

        return cleaned


# ===================================================================
# PHONE FORM (OTP send step)
# ===================================================================
# A very simple form with a single phone field.  Used in the first step
# of the customer OTP flow.
#
# There is no custom validation here — the view handles the logic of
# normalisation, OTP generation, and SMS sending after the form passes
# its built-in validation (max_length, required).
# ===================================================================

class PhoneForm(forms.Form):
    """
    Form for the customer to enter their phone number for OTP login.

    Only one field — the phone number.  Validation is minimal:
        - Must not be empty (required by default).
        - Must be 15 characters or fewer.

    The phone number is normalised later in the view (customer_otp_send)
    so we don't duplicate that logic here.
    """

    phone = forms.CharField(max_length=15, label='Phone Number')


# ===================================================================
# OTP VERIFY FORM
# ===================================================================
# The second step of the customer OTP flow.  The user types the 6-digit
# code they received via SMS.
#
# Like PhoneForm, this is intentionally simple.  The complex logic
# (checking expiry, checking is_used, matching the phone) lives in the
# view because it needs access to the session and the database.
# ===================================================================

class OTPVerifyForm(forms.Form):
    """
    Form for the customer to enter the 6-digit verification code.

    Validation:
        - Code must not be empty.
        - Code must be 6 characters or fewer.

    The view (customer_otp_verify) performs the actual database lookup
    and expiry/used checks.  Keeping the form simple makes it reusable
    and easy to test.
    """

    code = forms.CharField(max_length=6, label='Verification Code')
