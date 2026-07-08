"""
advertising/models.py
=====================

Defines data models for the 'advertising' Django app.

This app handles promotional content — banners (hero images on the homepage)
and promotions (special deals on specific cars). By keeping these in a
separate app, we follow Django's philosophy of "reusable apps": you could
drop this app into another project and it would work independently.

The 'advertising' app relates to the 'vehicles' app via a ForeignKey
(Promotion → Car). This is normal — Django apps are designed to work together.
"""

from django.db import models


class Banner(models.Model):
    """
    A banner is a large promotional image shown on the landing page
    (like a "hero" section on a website).

    Banners are simple: they display an image with a title, an optional
    subtitle, and an optional click-through link. Admins can reorder them
    and toggle them on/off without deleting them.
    """

    # The headline text displayed on the banner (e.g., "Summer Sale 2025").
    # max_length=200 is a reasonable limit for a headline.
    title = models.CharField(max_length=200)

    # Optional subtitle text displayed below the title.
    # null=True  → DB column allows NULL values
    # blank=True → form validation allows empty values
    # Together: "this field is optional"
    subtitle = models.TextField(null=True, blank=True)

    # URL pointing to the banner image file.
    # max_length=500 to accommodate long CDN or cloud storage URLs.
    image_url = models.CharField(max_length=500)

    # URL the user is taken to when they click the banner.
    # This is optional — a banner might be purely decorative.
    # The help_text attribute appears as a tooltip in the admin form, guiding
    # the admin user on what this field is for.
    link_url = models.CharField(max_length=500, null=True, blank=True,
                                help_text='Optional URL when banner is clicked')

    # -------------------------------------------------------------------
    # BooleanField = True/False.
    # is_active acts as a "soft delete" or "publish toggle" — admins can
    # deactivate a banner (it won't show on the site) without deleting it.
    # This is much safer than deleting (you can always re-enable it).
    # -------------------------------------------------------------------
    is_active = models.BooleanField(default=True)

    # -------------------------------------------------------------------
    # order controls the display sequence of banners.
    # SmallIntegerField uses less DB space than IntegerField — sufficient for
    # ordering (you probably won't need more than ~32,000 banners).
    # default=0 means new banners go first by default (since the Meta
    # ordering below sorts ascending by 'order').
    # -------------------------------------------------------------------
    order = models.SmallIntegerField(default=0)

    # Automatically set to the current timestamp when the banner is created.
    # auto_now_add=True: set once on creation, never modified after.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # -------------------------------------------------------------------
        # ordering determines the default sort order for queries.
        # ['order', '-created_at'] means:
        #   1st pass: sort by 'order' ascending (ASC — lowest number first)
        #   2nd pass: within the same 'order' value, sort by created_at
        #             descending (DESC — newest first).
        #
        # This ensures banners appear in a deliberate order, with ties broken
        # by newest-first.
        # -------------------------------------------------------------------
        ordering = ['order', '-created_at']

    def __str__(self):
        """
        Returns the title as the string representation.
        This means the admin list will show the banner's title rather than
        "Banner object (1)".
        """
        return self.title


class Promotion(models.Model):
    """
    Links a special promotional label/discount to a specific Car.

    For example: "2024 Toyota Camry — Hot Deal! 15% off"
    Each promotion belongs to exactly one car, and a car can have multiple
    promotions (though typically only one active at a time).

    Promotions can be time-bound (has a start and end date) so they
    automatically appear and disappear from the website.
    """

    # -------------------------------------------------------------------
    # Similar pattern to Car.STATUS_CHOICES — a list of (value, label) tuples.
    # value is stored in DB, label is displayed to users.
    # Labels are human-readable, values are "machine-friendly" short strings.
    # -------------------------------------------------------------------
    LABEL_CHOICES = [
        ('featured', 'Featured'),       # General promotion
        ('sale',     'Sale'),           # Discounted price
        ('new',      'New Arrival'),    # Recently added inventory
        ('hot',      'Hot Deal'),       # Special limited-time offer
    ]

    # -------------------------------------------------------------------
    # ForeignKey linking to Car in the 'vehicles' app.
    #
    # The string 'vehicles.Car' is a "lazy reference" — it avoids import
    # order issues. Django resolves this at model setup time, not at import
    # time. You can also use the actual imported class:
    #     from vehicles.models import Car
    #     car = models.ForeignKey(Car, ...)
    #
    # on_delete=models.CASCADE:
    #   If the referenced Car is deleted, this Promotion is also deleted.
    #   This makes sense: you can't have a promotion for a car that no
    #   longer exists in the database.
    #
    # related_name='promotions':
    #   Lets us go backwards from a Car to its promotions:
    #     car_instance.promotions.all()
    #   Without this, Django would use the default 'promotion_set'.
    # -------------------------------------------------------------------
    car = models.ForeignKey('vehicles.Car', on_delete=models.CASCADE, related_name='promotions')

    # Stores the promotional badge/label (e.g., "Hot Deal").
    # The choices restrict it to the values defined in LABEL_CHOICES.
    label = models.CharField(max_length=10, choices=LABEL_CHOICES, default='featured')

    # Optional discount percentage (e.g., 15 means "15% off").
    # SmallIntegerField is fine here (0-100 range).
    # null=True, blank=True makes this optional.
    # help_text provides guidance in the admin form.
    discount_percent = models.SmallIntegerField(null=True, blank=True,
                                                help_text='Discount percentage (e.g. 15 for 15% off)')

    # A toggle to quickly enable/disable a promotion without deleting it.
    is_active = models.BooleanField(default=True)

    # -------------------------------------------------------------------
    # DateTimeField for the promotion's start and end times.
    # null=True, blank=True means the promotion can have no time limit
    # (runs indefinitely once activated).
    #
    # In the landing_page view (views.py), we filter:
    #     starts_at__lte=now  AND  ends_at__gte=now
    # to find currently-active, time-bound promotions.
    # If starts_at is NULL, the __lte filter would exclude it — so in a
    # real project you might want to handle "no start date = always started".
    # -------------------------------------------------------------------
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)

    # Timestamp automatically set when the promotion is first created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Newest promotions first by default.
        ordering = ['-created_at']

    def __str__(self):
        """
        Returns a string like: "Hot Deal: 2024 Toyota Camry"
        Note: self.get_label_display() returns the HUMAN-READABLE label
        (e.g., "Hot Deal") rather than the stored value (e.g., "hot").
        Django auto-generates get_<fieldname>_display() for any field
        that has the choices= option set.
        """
        return f'{self.get_label_display()}: {self.car}'
