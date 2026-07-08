from django.db import models
from django.conf import settings


class Campaign(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
    ]
    name = models.CharField(max_length=150)
    message_template = models.TextField(
        help_text='Plain text. Use {full_name} for lead name, {phone} for lead phone.'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CampaignRecipient(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name='recipients')
    lead = models.ForeignKey('leads.Lead', on_delete=models.SET_NULL, null=True, blank=True)
    phone = models.CharField(max_length=15)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    sms_log = models.ForeignKey('notifications.SmsLog', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['campaign', 'phone']

    def __str__(self):
        return f'{self.campaign.name} - {self.phone}'
