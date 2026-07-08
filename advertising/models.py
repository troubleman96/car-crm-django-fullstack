from django.db import models


class Banner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.TextField(null=True, blank=True)
    image_url = models.CharField(max_length=500)
    link_url = models.CharField(max_length=500, null=True, blank=True,
                                help_text='Optional URL when banner is clicked')
    is_active = models.BooleanField(default=True)
    order = models.SmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.title


class Promotion(models.Model):
    LABEL_CHOICES = [
        ('featured', 'Featured'),
        ('sale', 'Sale'),
        ('new', 'New Arrival'),
        ('hot', 'Hot Deal'),
    ]

    car = models.ForeignKey('vehicles.Car', on_delete=models.CASCADE, related_name='promotions')
    label = models.CharField(max_length=10, choices=LABEL_CHOICES, default='featured')
    discount_percent = models.SmallIntegerField(null=True, blank=True,
                                                help_text='Discount percentage (e.g. 15 for 15% off)')
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_label_display()}: {self.car}'
