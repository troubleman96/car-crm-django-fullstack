"""
notifications/models.py
=======================

Defines the SmsLog model, which records every SMS sent through the
application. Think of this as an "audit log" — it stores every send
attempt so we can track delivery, debug problems, and prove to the
business that messages were sent.

We keep models.py minimal: just the data structure. The actual SMS
sending logic lives in services.py.

Related files:
  - notifications/services.py — calls the SendAfrica API and creates
    SmsLog rows (the main consumer of this model).
  - notifications/admin.py — lets staff view/search/filter SmsLog
    entries in the Django admin.
  - campaigns/models.py — CampaignRecipient has a ForeignKey to SmsLog
    so we can link a campaign send to its corresponding log entry.
"""

from django.db import models


class SmsLog(models.Model):
    """
    Records one SMS send attempt.

    A row is created EVERY time we try to send an SMS — whether the
    API call succeeds or fails. This way we always have a paper trail.

    Fields
    ------
    phone : CharField
        The normalized Tanzanian phone number (e.g. "+255712345678").
    message : TextField
        The raw SMS body that was sent.
    status : CharField (choices: sent / delivered / failed)
        'sent'      — the SendAfrica API accepted the message.
        'delivered' — the handset confirmed receipt (future use).
        'failed'    — the API rejected it, or a network error occurred.
    provider_message_id : CharField (nullable)
        The ID returned by SendAfrica for this message. Useful for
        looking up delivery reports in the provider's dashboard.
    created_at : DateTimeField
        Automatically set to now() when the row is created.
        Because we use auto_now_add, we never set this manually.
    """

    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]

    # -- Field definitions -----------------------------------------------

    phone = models.CharField(max_length=15)
    # max_length=15 fits "+255" + 9 digits = 13 chars, with a little
    # wiggle room. Tanzanian numbers are exactly 12 chars when fully
    # qualified: +255 7XX XXX XXX (13 with +).

    message = models.TextField()
    # TextField (unlike CharField) has no length limit. SMS messages
    # are typically 160 characters, but the SendAfrica API supports
    # longer messages that get concatenated automatically.

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='sent',
    )
    # The choices kwarg makes Django render a <select> dropdown in
    # forms/admin. The first element of each tuple is stored in the
    # DB; the second is the human-readable label.
    # default='sent' means newly created rows default to 'sent'.

    provider_message_id = models.CharField(
        max_length=64,
        null=True,   # allows NULL in the database
        blank=True,  # allows empty string in forms (admin)
    )
    # nullable because we only get a message_id from SendAfrica when
    # the API call succeeds. On failure this stays NULL.

    created_at = models.DateTimeField(auto_now_add=True)
    # auto_now_add=True sets the value once, when the row is first
    # inserted, and never changes it afterwards. Perfect for a
    # timestamp of creation.

    # -- Metadata --------------------------------------------------------

    class Meta:
        ordering = ['-created_at']
        # "-created_at" means descending order — newest entries first.
        # This is the default ordering whenever we query SmsLog.objects.

    # -- String representation -------------------------------------------

    def __str__(self):
        """
        Defines how this model appears in the admin, dropdowns, etc.
        Django calls this whenever it needs a human-readable label
        for an instance.
        """
        return f'{self.phone} - {self.status}'
