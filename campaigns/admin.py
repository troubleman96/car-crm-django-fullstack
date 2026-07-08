import time
from django.contrib import admin, messages
from django.utils import timezone
from .models import Campaign, CampaignRecipient
from notifications.services import send_sms


class CampaignRecipientInline(admin.TabularInline):
    model = CampaignRecipient
    extra = 0
    readonly_fields = ['phone', 'status', 'sms_log']
    can_delete = False


@admin.action(description='Send selected campaigns now')
def send_campaign_now(modeladmin, request, queryset):
    """
    Sends the campaign SMS to all pending recipients.

    NOTE: This runs synchronously in the admin request -- fine for 50-200
    recipients. A production system would use a task queue (Celery, etc.)
    so the admin doesn't hang during large campaigns.
    """
    for campaign in queryset:
        if campaign.status != 'draft':
            messages.warning(request, f'Campaign "{campaign.name}" already sent or sending.')
            continue

        campaign.status = 'sending'
        campaign.save()

        recipients = campaign.recipients.filter(status='pending')
        if not recipients.exists():
            messages.warning(request, f'No pending recipients for "{campaign.name}".')
            campaign.status = 'draft'
            campaign.save()
            continue

        sent_count = 0
        fail_count = 0
        for recipient in recipients:
            # Personalize the message with lead data
            lead = recipient.lead
            full_name = lead.full_name if lead and lead.full_name else 'Valued Customer'
            personalized = campaign.message_template.format(
                full_name=full_name,
                phone=recipient.phone,
            )

            success = send_sms(recipient.phone, personalized)
            if success:
                recipient.status = 'sent'
                sent_count += 1
            else:
                recipient.status = 'failed'
                fail_count += 1
            recipient.save()

            # 150ms delay to respect SendAfrica rate limit (600/min for Pro)
            # 1000ms / 6.6 = ~150ms between requests = ~400/min, well under limit
            time.sleep(0.15)

        campaign.status = 'sent'
        campaign.save()
        messages.success(
            request,
            f'"{campaign.name}": {sent_count} sent, {fail_count} failed.',
        )


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'created_by', 'scheduled_at', 'created_at']
    list_filter = ['status']
    search_fields = ['name']
    inlines = [CampaignRecipientInline]
    actions = [send_campaign_now]


@admin.register(CampaignRecipient)
class CampaignRecipientAdmin(admin.ModelAdmin):
    list_display = ['campaign', 'phone', 'status', 'lead', 'sms_log']
    list_filter = ['status', 'campaign']
    search_fields = ['phone', 'campaign__name']
