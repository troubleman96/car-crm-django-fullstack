"""
campaigns/models.py
===================

Defines two models for bulk SMS marketing campaigns:

  Campaign          — represents one marketing campaign (e.g. "July
                      Sale Promo"). Contains the message template,
                      status, schedule, and the staff member who
                      created it.

  CampaignRecipient — a single recipient within a campaign. Links a
                      campaign to a lead and tracks whether the SMS
                      was sent successfully.

Data flow:
  1. Staff create a Campaign with a message template containing
     placeholders like {full_name} and {phone}.
  2. Staff add recipients (CampaignRecipient rows) linked to leads.
  3. Staff trigger the campaign from the admin, which calls
     send_sms() for each recipient, personalising the template.
  4. The result (sent / failed) is recorded on each recipient, and
     the corresponding SmsLog is linked.

Related files:
  - campaigns/admin.py — admin configuration + the send_campaign_now
    action that triggers the SMS sending.
  - notifications/services.py — the send_sms() function used to send
    each individual message.
  - notifications/models.py — SmsLog model linked via ForeignKey.
  - leads/models.py — the Lead model that provides contact data.
"""

from django.db import models
from django.conf import settings


class Campaign(models.Model):
    """
    A single SMS marketing campaign.

    A campaign is essentially: a message template + a list of
    recipients. When the campaign is "sent", the template is
    rendered for each recipient (replacing placeholders with
    their data) and sent via the SendAfrica API.

    Status lifecycle:
      draft → sending → sent

    Fields
    ------
    name : CharField
        A human-readable label for the campaign (e.g. "March Promo").
    message_template : TextField
        The SMS body with {full_name} and {phone} as placeholders
        that get replaced per-recipient at send time.
    created_by : ForeignKey → User
        The staff member who created this campaign. Nullable so that
        if the user is deleted, the campaign record survives.
    status : CharField (draft / sending / sent)
        Tracks the campaign through its lifecycle.
    scheduled_at : DateTimeField (nullable)
        Reserved for future use — a scheduled send time. Currently
        campaigns are sent immediately via the admin action.
    created_at : DateTimeField
        Auto-set timestamp of when the campaign row was first saved.
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
    ]

    name = models.CharField(max_length=150)

    message_template = models.TextField(
        help_text='Plain text. Use {full_name} for lead name, {phone} for lead phone.'
    )
    # help_text appears below the form field in the Django admin to
    # guide staff on what placeholders are available.

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,   # Reference to the User model
        on_delete=models.SET_NULL,  # If user is deleted, set NULL (don't delete campaigns)
        null=True,                  # Allow NULL in DB
        blank=True,                 # Allow empty in admin forms
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='draft',
    )

    scheduled_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']   # newest campaigns first by default

    def __str__(self):
        return self.name


class CampaignRecipient(models.Model):
    """
    A single recipient belonging to a campaign.

    This is a "through" or "junction" model that connects a Campaign
    to a Lead, while also tracking the sending status for that
    individual recipient.

    Why a separate model instead of a ManyToManyField on Campaign?
      - We need to store per-recipient status (pending/sent/failed).
      - We need to link each recipient to its SmsLog entry.
      - A ManyToManyField with a "through" model would accomplish
        the same thing, but this explicit approach is simpler.

    Status lifecycle:
      pending → sent
      pending → failed

    Fields
    ------
    campaign : ForeignKey → Campaign
        The campaign this recipient belongs to. CASCADE means if the
        campaign is deleted, all its recipients are deleted too.
    lead : ForeignKey → Lead (nullable)
        The lead this recipient is based on. SET_NULL preserves the
        recipient record even if the lead is deleted (the phone
        number is stored directly, so we can still send).
    phone : CharField
        The phone number to send to. Stored redundantly on this model
        (instead of always looking up lead.phone) so that the
        recipient record is self-contained and survives lead deletion.
    status : CharField (pending / sent / failed)
        Tracks the send state for THIS specific recipient.
    sms_log : ForeignKey → SmsLog (nullable)
        Links to the SmsLog record created when the SMS was sent.
        SET_NULL ensures we don't lose recipient data if SmsLog
        entries are ever cleaned up.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,                 # delete recipients if campaign is deleted
        related_name='recipients',                # allows campaign.recipients.all()
    )

    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,                # keep recipient if lead is deleted
        null=True,
        blank=True,
    )

    phone = models.CharField(max_length=15)
    # Stored directly so the recipient is usable even if the
    # linked Lead is deleted.

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
    )

    sms_log = models.ForeignKey(
        'notifications.SmsLog',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    # Linked after the SMS is sent so we can trace from a recipient
    # back to the exact API response details.

    class Meta:
        ordering = ['campaign', 'phone']

    def __str__(self):
        return f'{self.campaign.name} - {self.phone}'
