"""
campaigns/admin.py
==================

Admin configuration for the Campaign and CampaignRecipient models.

Key feature: the `send_campaign_now` admin action that lets staff
select one or more campaigns in the list view and trigger them
immediately. This is a custom admin action — a function decorated
with @admin.action that operates on the selected queryset.

WARNING: This action runs synchronously inside the HTTP request.
For small campaigns (50-200 recipients) this is fine, but for
large campaigns it would block the admin page until every SMS
is sent. A production system would offload this to a task queue
(like Celery or Django RQ).

Related files:
  - campaigns/models.py — the Campaign and CampaignRecipient models.
  - notifications/services.py — send_sms() does the actual SMS sending.
  - notifications/models.py — SmsLog records each send attempt.
"""

import time
from django.contrib import admin, messages
from django.utils import timezone
from .models import Campaign, CampaignRecipient
from notifications.services import send_sms


# -----------------------------------------------------------------------
# Inline admin for CampaignRecipient
# -----------------------------------------------------------------------
# TabularInline shows related CampaignRecipient rows as a table
# embedded inside the Campaign's change form.
class CampaignRecipientInline(admin.TabularInline):
    """
    Displays recipients as an inline table on the Campaign edit page.

    When an admin user opens a Campaign in the admin, they will
    see all related CampaignRecipient rows displayed below the
    Campaign form fields. This is Django's way of handling
    one-to-many relationships in the admin interface.
    """
    model = CampaignRecipient
    extra = 0                       # don't show extra empty rows
    readonly_fields = ['phone', 'status', 'sms_log']
    can_delete = False              # don't allow deleting from inline


# -----------------------------------------------------------------------
# Custom admin action: send_campaign_now
# -----------------------------------------------------------------------
# Admin actions are functions that operate on a queryset of selected
# objects from the list view. They are registered via the `actions`
# attribute on a ModelAdmin class.
#
# The @admin.action decorator replaces the older pattern of setting
# action.short_description. It is the modern, recommended way.
@admin.action(description='Send selected campaigns now')
def send_campaign_now(modeladmin, request, queryset):
    """
    Send all pending recipients for the selected campaigns.

    This function is called when a staff member:
      1. Goes to the Campaign admin list page.
      2. Checks the checkboxes next to one or more campaigns.
      3. Selects "Send selected campaigns now" from the dropdown.
      4. Clicks "Go".

    Parameters
    ----------
    modeladmin : ModelAdmin
        The CampaignAdmin instance (not used directly here).
    request : HttpRequest
        The current admin HTTP request. Used to display messages
        back to the admin user via django.contrib.messages.
    queryset : QuerySet
        The Campaign objects the user selected.

    How it works:
      1. Loop over each selected campaign.
      2. Skip campaigns that are not in 'draft' status.
      3. Set campaign status to 'sending' and save.
      4. Get all recipients with status='pending'.
      5. If no pending recipients, reset to 'draft' and warn.
      6. For each recipient:
         a. Personalise the message (replace {full_name}, {phone}).
         b. Call send_sms() to send via SendAfrica API.
         c. Update recipient status based on result.
         d. Sleep 150ms to respect API rate limits.
      7. Set campaign status to 'sent' and save.
      8. Show a success/failure summary message.
    """
    for campaign in queryset:
        # --- Skip non-draft campaigns ----------------------------------
        # We can only send campaigns that are in 'draft' status.
        # 'sending' means another admin session is already sending it,
        # and 'sent' means it has already been sent.
        if campaign.status != 'draft':
            messages.warning(
                request,
                f'Campaign "{campaign.name}" already sent or sending.',
            )
            continue

        # --- Transition from 'draft' to 'sending' ----------------------
        campaign.status = 'sending'
        campaign.save()
        # We save here so that if another admin user opens the same
        # campaign, they will see it is already being sent and won't
        # accidentally trigger a second send.

        # --- Fetch pending recipients ----------------------------------
        recipients = campaign.recipients.filter(status='pending')
        # .filter() returns a QuerySet — a lazy collection that is
        # only evaluated when we iterate over it.

        if not recipients.exists():
            # No recipients to send to — abort and revert to 'draft'.
            messages.warning(
                request,
                f'No pending recipients for "{campaign.name}".',
            )
            campaign.status = 'draft'
            campaign.save()
            continue

        # --- Send SMS to each recipient --------------------------------
        sent_count = 0
        fail_count = 0

        for recipient in recipients:
            # Personalise the message template for this recipient.
            # str.format() replaces {placeholders} with actual values.
            # If the lead has no full_name, we use a fallback.
            lead = recipient.lead
            full_name = lead.full_name if lead and lead.full_name else 'Valued Customer'
            personalized = campaign.message_template.format(
                full_name=full_name,
                phone=recipient.phone,
            )

            # Send via the notification service.
            # This is a blocking call — it waits for the HTTP response
            # from SendAfrica before continuing.
            success = send_sms(recipient.phone, personalized)

            if success:
                recipient.status = 'sent'
                sent_count += 1
            else:
                recipient.status = 'failed'
                fail_count += 1

            recipient.save()
            # We save each recipient individually. For bulk operations,
            # Django's bulk_update() would be more efficient, but this
            # is fine for small campaigns.

            # --- Rate limiting -----------------------------------------
            # The SendAfrica API has rate limits (e.g. 600 requests per
            # minute for the Pro plan = 10 requests per second).
            # We sleep 150ms between requests to stay comfortably under
            # the limit. This is a simple "dumb" rate limiter.
            #
            # Formula: sleep_time = 1000ms / (max_requests_per_second)
            # For 600/min: 600/60 = 10/sec → 1000ms / 10 = 100ms.
            # We use 150ms for a safety margin (~400/min).
            time.sleep(0.15)

        # --- Finalize campaign -----------------------------------------
        campaign.status = 'sent'
        campaign.save()

        messages.success(
            request,
            f'"{campaign.name}": {sent_count} sent, {fail_count} failed.',
        )


# -----------------------------------------------------------------------
# Register Campaign with the admin
# -----------------------------------------------------------------------
@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    """
    Admin configuration for the Campaign model.

    Inlines:
      CampaignRecipientInline — shows recipients on the Campaign form.

    Actions:
      send_campaign_now       — sends the campaign via SMS.
    """

    list_display = [
        'name',
        'status',
        'created_by',
        'scheduled_at',
        'created_at',
    ]

    list_filter = ['status']
    search_fields = ['name']

    # Embed the related recipients as an inline table.
    inlines = [CampaignRecipientInline]

    # Register our custom admin action so it appears in the
    # actions dropdown on the change list page.
    actions = [send_campaign_now]


# -----------------------------------------------------------------------
# Register CampaignRecipient with the admin
# -----------------------------------------------------------------------
@admin.register(CampaignRecipient)
class CampaignRecipientAdmin(admin.ModelAdmin):
    """
    Admin configuration for the CampaignRecipient model.

    This is a separate admin page so staff can view and search
    across ALL recipients (not only those within a campaign).
    """

    list_display = ['campaign', 'phone', 'status', 'lead', 'sms_log']
    list_filter = ['status', 'campaign']
    search_fields = ['phone', 'campaign__name']
    # Note: 'campaign__name' uses Django's double-underscore syntax
    # to search across the related Campaign model's name field.
