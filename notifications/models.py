from django.db import models


class SmsLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    phone = models.CharField(max_length=15)
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    provider_message_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone} - {self.status}'
