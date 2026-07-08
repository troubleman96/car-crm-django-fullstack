import logging
import re
import ssl
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
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as resp:
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

    except urllib.error.HTTPError as e:
        error_body = e.read().decode(errors='replace')
        logger.error('SMS send failed for %s: HTTP %d %s \u2014 body: %s',
                     phone, e.code, e.reason, error_body)
        print(f'[SENDAFRICA ERROR] {e.code} {e.reason}: {error_body}')
        SmsLog.objects.create(phone=phone, message=message, status='failed')
    except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
        logger.error('SMS send failed for %s: %s', phone, str(e))
        SmsLog.objects.create(phone=phone, message=message, status='failed')
        return False
