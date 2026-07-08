"""
SendAfrica SMS service.

This is the ONLY place in the codebase that calls the SendAfrica API.
All other apps import send_sms() from here to send SMS messages.

Logs every send attempt (success or failure) into SmsLog.
Never raises an exception -- returns True on success, False on failure.
"""

import logging
import re
import urllib.request
import urllib.error
import json
from django.conf import settings
from .models import SmsLog

logger = logging.getLogger(__name__)

SENDAFRICA_SEND_URL = f'{settings.SENDAFRICA_BASE_URL}/v1/sms/'


def normalize_phone(phone: str) -> str:
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    if phone.startswith('0'):
        phone = '+255' + phone[1:]
    elif phone.startswith('255'):
        phone = '+' + phone
    if not phone.startswith('+'):
        phone = '+255' + phone
    return phone


def send_sms(phone: str, message: str) -> bool:
    """
    Send an SMS via SendAfrica API.

    Args:
        phone: Tanzania phone number (07xx, +2557xx, or 2557xx).
        message: SMS text content.

    Returns:
        True if the API accepted the message, False otherwise.

    Logs every attempt in SmsLog for audit/debugging.
    """
    phone = normalize_phone(phone)
    payload = json.dumps({
        'to': phone,
        'message': message,
    }).encode('utf-8')

    req = urllib.request.Request(
        SENDAFRICA_SEND_URL,
        data=payload,
        headers={
            'X-API-Key': settings.SENDAFRICA_API_KEY,
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode())
            if body.get('success'):
                msg_id = body.get('data', {}).get('message_id', '')
                SmsLog.objects.create(
                    phone=phone,
                    message=message,
                    status='sent',
                    provider_message_id=msg_id,
                )
                logger.info('SMS sent to %s: message_id=%s', phone, msg_id)
                return True
            else:
                error = body.get('error', {})
                logger.warning('SendAfrica error for %s: %s', phone, error)
                SmsLog.objects.create(
                    phone=phone,
                    message=message,
                    status='failed',
                )
                return False
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, json.JSONDecodeError) as e:
        logger.error('SMS send failed for %s: %s', phone, str(e))
        SmsLog.objects.create(
            phone=phone,
            message=message,
            status='failed',
        )
        return False
