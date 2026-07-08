"""
notifications/services.py
=========================

SendAfrica SMS service — the ONLY module that talks to the SendAfrica
SMS API. Every other app (campaigns, leads, etc.) imports `send_sms()`
from here when it needs to send a text message.

Key design decisions:

  1. Centralisation — one function sends SMS, so there is one place to
     change if we switch providers (e.g. from SendAfrica to Twilio).

  2. Safety — this module NEVER raises an exception to its caller.
     It always returns True (message accepted) or False (something
     went wrong). The caller never needs a try/except.

  3. Audit trail — every send attempt is logged in SmsLog whether it
     succeeds or fails. This gives us full traceability.

  4. Phone normalisation — Tanzania uses the +255 country code. Users
     might type "0712345678", "255712345678", or "+255 712 345 678".
     normalize_phone() turns any of these into "+255712345678".

Dependencies:
  - notifications.models.SmsLog  (the audit-log model)
  - django.conf.settings          (SENDAFRICA_BASE_URL, SENDAFRICA_API_KEY)
"""

import logging
import re
import urllib.request
import urllib.error
import json

from django.conf import settings
from .models import SmsLog


# -----------------------------------------------------------------------
# Logger setup
# -----------------------------------------------------------------------
# We use Python's standard logging module. __name__ evaluates to
# "notifications.services", which is the logger name that appears in
# log output. Configuration (what gets logged, where it goes) is in
# settings.py / LOGGING dict.
logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# SendAfrica endpoint URL
# -----------------------------------------------------------------------
# settings.SENDAFRICA_BASE_URL is defined in car_crm/settings.py
# (typically something like "https://api.sendafrica.com").
# We append "/v1/sms/" to hit the SMS-sending endpoint.
SENDAFRICA_SEND_URL = f'{settings.SENDAFRICA_BASE_URL}/v1/sms/'


# -----------------------------------------------------------------------
# normalize_phone()
# -----------------------------------------------------------------------
def normalize_phone(phone: str) -> str:
    """
    Convert a raw phone string into a standardised +255 format.

    Tanzanian phone numbers follow this pattern:
      Country code: +255
      Subscriber:   XX XXX XXX  (9 digits, starting with 7)

    Users may enter the number in any of these common formats:
      0712345678   (local — starts with 0)
      255712345678 (international — without +)
      +255712345678(fully qualified)
      0712 345 678 (with spaces or hyphens)

    This function handles all of the above and returns a clean
    international format: +255712345678

    How it works (step by step):
      1. Strip spaces, dashes, parentheses, and any other visual
         separators so the input is a solid string of digits (and
         possibly a leading +).
      2. If it starts with "0", replace the leading "0" with
         Tanzania's country code "+255". Example: "0712..." → "+255712..."
      3. If it starts with "255" (but no "+"), prepend a "+" so it
         becomes "+255...".
      4. If it does not start with "+" at this point, assume it is
         a local number that was not caught by the "0" case and
         prepend "+255" anyway as a fallback.
      5. Return the cleaned string.

    Note: This function performs basic format normalisation, NOT
    full validation. It does not check that the number has exactly
    9 digits after the country code or that it starts with a valid
    Tanzanian prefix (7XX). A real production system would add
    stronger validation.
    """
    # Step 1 — remove whitespace and common visual separators.
    # \s matches any whitespace character (space, tab, newline).
    # The character class [\s\-\(\)] also matches literal hyphen,
    # opening parenthesis, and closing parenthesis.
    # re.sub() replaces every match with '' (empty string).
    phone = re.sub(r'[\s\-\(\)]', '', phone)

    # Step 2 — local format starting with "0"
    if phone.startswith('0'):
        # Keep everything after the leading "0", prepend "+255".
        phone = '+255' + phone[1:]

    # Step 3 — international format without the "+"
    elif phone.startswith('255'):
        # Just add the missing "+" at the front.
        phone = '+' + phone

    # Step 4 — fallback (e.g. bare "712345678")
    if not phone.startswith('+'):
        phone = '+255' + phone

    return phone


# -----------------------------------------------------------------------
# send_sms()
# -----------------------------------------------------------------------
def send_sms(phone: str, message: str) -> bool:
    """
    Send an SMS via the SendAfrica API.

    This is the main function other apps call. It:

      1. Normalises the phone number.
      2. Builds a JSON payload with the recipient and message.
      3. Sends an HTTP POST request to SendAfrica.
      4. Inspects the JSON response from SendAfrica.
      5. Creates an SmsLog row to record the outcome.
      6. Returns True on success, False on failure.

    Args:
        phone:   A Tanzanian phone number in almost any format
                 (07xx, 2557xx, +2557xx, with or without spacing).
        message: The SMS body text.

    Returns:
        True  — the API accepted the message (status 'sent').
        False — the API rejected it OR a network error occurred.

    Important:
        This function NEVER raises an exception to the caller.
        Network timeouts, invalid JSON, HTTP 500 errors — all are
        caught and translated into a False return and a log entry.
    """
    # --- Step 1: Normalise the phone number -----------------------------
    phone = normalize_phone(phone)

    # --- Step 2: Build the JSON payload ---------------------------------
    # json.dumps() serialises a Python dict into a JSON string.
    # .encode('utf-8') converts that string into bytes, because
    # urllib.request needs the data argument as bytes.
    payload = json.dumps({
        'to': phone,
        'message': message,
    }).encode('utf-8')

    # --- Step 3: Prepare the HTTP request object ------------------------
    # urllib.request.Request is an HTTP request that we can configure
    # with a URL, HTTP method, body (data), and custom headers.
    req = urllib.request.Request(
        SENDAFRICA_SEND_URL,
        data=payload,
        headers={
            # API key authentication — SendAfrica expects this in a
            # custom header. The actual key lives in settings.py (or
            # environment variables) and must NEVER be hard-coded.
            'X-API-Key': settings.SENDAFRICA_API_KEY,
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    # --- Step 4: Send the request and handle the response ---------------
    # The try/except block ensures we catch ANY possible error and
    # handle it gracefully (return False) rather than crashing.
    try:
        # urlopen() performs the actual HTTP request. We give it a
        # 10-second timeout so the request doesn't hang forever if
        # the SendAfrica server is unreachable.
        with urllib.request.urlopen(req, timeout=10) as resp:
            # Read the response body (bytes), decode it to a string
            # (UTF-8), and parse the JSON string into a Python dict.
            body = json.loads(resp.read().decode())

            # SendAfrica returns {"success": true, "data": { ... }}
            # on success, and {"success": false, "error": { ... }}
            # on failure. We check the 'success' key.
            if body.get('success'):
                # --- Success path ---------------------------------------
                # Extract the provider's message ID from the nested
                # "data" object. If it's missing, default to ''.
                msg_id = body.get('data', {}).get('message_id', '')

                # Log the successful send to the database.
                # SmsLog.objects.create() is a Django QuerySet
                # method that inserts a new row and returns the
                # model instance.
                SmsLog.objects.create(
                    phone=phone,
                    message=message,
                    status='sent',
                    provider_message_id=msg_id,
                )

                # Log to the application log file (for operations).
                logger.info('SMS sent to %s: message_id=%s', phone, msg_id)

                return True

            else:
                # --- API-level failure ----------------------------------
                # The API responded normally (HTTP 200) but indicated
                # failure — e.g. invalid phone number, insufficient
                # credit, blocked sender ID.
                error = body.get('error', {})

                # Log a warning (not an error — the API didn't crash,
                # the request was just rejected for a business reason).
                logger.warning('SendAfrica error for %s: %s', phone, error)

                # Record the failed attempt in the audit log.
                SmsLog.objects.create(
                    phone=phone,
                    message=message,
                    status='failed',
                )
                return False

    # --- Step 5: Catch network / transport / parsing errors -------------
    # We catch MULTIPLE exception types in one except clause:
    #
    #   URLError       — DNS lookup failure, connection refused, timeout.
    #   HTTPError      — the server returned a non-2xx status
    #                    (e.g. 401 Unauthorized, 500 Internal Server Error).
    #                    HTTPError is a subclass of URLError, but we list
    #                    both for clarity.
    #   OSError        — lower-level OS issues (e.g. socket error).
    #   json.JSONDecodeError — the response body was not valid JSON.
    #
    # The "as e" syntax binds the exception instance to the variable
    # `e` so we can access its string representation with str(e).
    except (urllib.error.URLError, urllib.error.HTTPError,
            OSError, json.JSONDecodeError) as e:
        logger.error('SMS send failed for %s: %s', phone, str(e))

        # Still log the attempt as 'failed' — the audit trail must be
        # complete even when the network is down.
        SmsLog.objects.create(
            phone=phone,
            message=message,
            status='failed',
        )
        return False
