from django.db import models


class ChatSession(models.Model):
    lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    phone = models.CharField(max_length=15, null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Session {self.id} - {self.phone or "Anonymous"}'


class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('customer', 'Customer'),
        ('bot', 'Bot'),
        ('agent', 'Agent'),
    ]

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'[{self.sender}] {self.message[:50]}'
