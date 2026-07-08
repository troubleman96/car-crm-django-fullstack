from django.db import models
from django.conf import settings


class Lead(models.Model):
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('chatbot', 'Chatbot'),
        ('campaign', 'Campaign'),
        ('walk_in', 'Walk-in'),
    ]
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    phone = models.CharField(max_length=15)
    full_name = models.CharField(max_length=150, null=True, blank=True)
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='website')
    interested_car = models.ForeignKey(
        'vehicles.Car', on_delete=models.SET_NULL, null=True, blank=True
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_leads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name or self.phone} ({self.source})'


class Appointment(models.Model):
    TYPE_CHOICES = [
        ('test_drive', 'Test Drive'),
        ('call_back', 'Call Back'),
        ('showroom_visit', 'Showroom Visit'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='appointments')
    car = models.ForeignKey('vehicles.Car', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-scheduled_at']

    def __str__(self):
        return f'{self.get_type_display()} - {self.lead}'
