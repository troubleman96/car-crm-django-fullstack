"""
vehicles/models.py
===================

Defines the data models (database tables) for the 'vehicles' Django app.

In Django, each class that inherits from models.Model becomes a database table.
Each class attribute (field) becomes a column in that table.

This file is the "M" in Django's MTV (Model-Template-View) pattern — it defines
what data our application stores and how different pieces of data relate to
each other.

Think of this as the blueprint for the database. Django will use this file to
automatically create (or alter) the actual database tables when you run:
    python manage.py makemigrations
    python manage.py migrate
"""

# ---------------------------------------------------------------------------
# django.db.models is Django's ORM (Object-Relational Mapper).
# It lets us define database tables as Python classes — we never write raw SQL.
# ---------------------------------------------------------------------------
from django.db import models


class Car(models.Model):
    """
    Represents a single car in the dealership's inventory.

    Each Car instance = one row in the 'vehicles_car' database table (Django
    auto-names it as <app_name>_<class_name_lowercased>).

    Fields defined here become columns in that table. Django handles creating,
    reading, updating, and deleting rows — all through Python code.
    """

    # -----------------------------------------------------------------------
    # STATUS_CHOICES is a list of tuples. Each tuple is (value_in_db, display_label).
    # Django uses these for two things:
    #   1) It restricts the 'status' field to only these values at the DB level.
    #   2) It automatically generates a <select> dropdown in forms and the admin.
    # -----------------------------------------------------------------------
    STATUS_CHOICES = [
        ('available', 'Available'),  # (stored in DB, shown to users)
        ('reserved',  'Reserved'),
        ('sold',      'Sold'),
    ]

    # CharField = a short text column (VARCHAR in SQL).
    # max_length is *required* for CharField — it sets the column size.
    make = models.CharField(max_length=50)          # e.g. "Toyota", "Ford"
    model = models.CharField(max_length=50)         # e.g. "Camry", "Mustang"

    # SmallIntegerField stores small whole numbers (uses less space than IntegerField).
    # Good for years (1900–2100 range), ages, etc.
    year = models.SmallIntegerField()

    # DecimalField stores fixed-precision decimal numbers — perfect for money.
    #   max_digits    = total number of digits (both sides of the decimal point)
    #   decimal_places = digits after the decimal point
    # NEVER use FloatField for money — floating-point rounding errors are a
    # disaster for financial data!
    price = models.DecimalField(max_digits=12, decimal_places=2)

    # CharField with choices= renders as a <select> dropdown in forms.
    # default='available' means new cars start with this status automatically
    # if no other status is given.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='available')

    # TextField = larger text column (TEXT in SQL), no max_length limit.
    # null=True  → allows NULL in the database (empty = NULL, not empty string '')
    # blank=True → allows empty values in forms/validation (without this, Django
    #              would require a value in forms even if null=True is set).
    # Together they mean "this field is optional".
    description = models.TextField(null=True, blank=True)

    # DateTimeField stores a date + time.
    # auto_now_add=True: automatically sets the value to the current timestamp
    # ONCE, when the row is first created. It never changes on subsequent saves.
    # This is perfect for "created at" or "date joined" fields.
    created_at = models.DateTimeField(auto_now_add=True)

    # -------------------------------------------------------------------
    # The Meta class is a container for "metadata" — settings about the
    # model that aren't fields. Common options:
    #   ordering   → default sort order when querying (e.g., Car.objects.all())
    #   verbose_name / verbose_name_plural → human-readable names for admin
    #   db_table   → custom table name (otherwise Django auto-names it)
    # -------------------------------------------------------------------
    class Meta:
        # ordering = ['-created_at'] means: when you do Car.objects.all(),
        # results come back newest-first (the minus sign = descending order).
        # This is the default ordering for *all* queries unless you override
        # it with .order_by() on a specific queryset.
        ordering = ['-created_at']

    # -------------------------------------------------------------------
    # __str__ is Python's "string representation" method.
    # When you print() a Car instance, or when Django displays a car in the
    # admin interface, it calls this method to get a human-readable label.
    # Without it, the admin would show "Car object (1)" — not very helpful!
    #
    # The f-string (f'{...}') is Python 3's formatted string literal.
    # -------------------------------------------------------------------
    def __str__(self):
        return f'{self.year} {self.make} {self.model}'


class CarImage(models.Model):
    """
    Stores image URLs associated with a Car.

    This is a separate model (and therefore a separate database table) from
    Car because a car can have multiple images. By creating a separate model
    and linking it to Car via a ForeignKey, we create a one-to-many relationship:
        One Car  →  Many CarImage records.

    This approach (a separate "image" table) is more flexible than storing
    images as a JSON array inside the Car table — we can query, filter, and
    manage each image independently.
    """

    # -------------------------------------------------------------------
    # ForeignKey creates a many-to-one relationship.
    #
    #   CarImage → Car   (each image belongs to ONE car)
    #   Car      → many CarImages  (a car can have MANY images)
    #
    # The ForeignKey field stores the 'id' of the related Car in the database
    # (Django handles this automatically — the column is named 'car_id').
    #
    # on_delete=models.CASCADE:
    #   If a Car is deleted, ALL its CarImage rows are ALSO deleted.
    #   This prevents "orphan" records that point to nothing.
    #   Common alternatives:
    #     - PROTECT: prevent deletion of a Car if it has images
    #     - SET_NULL: set car_id to NULL (requires null=True)
    #
    # related_name='images':
    #   This is the name we use to go *backwards* from Car to its images.
    #   If a car variable is a Car instance, we can do:
    #       car.images.all()
    #   ...which returns all CarImage records for that car.
    #   Without related_name, Django would default to 'carimage_set'.
    # -------------------------------------------------------------------
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name='images')

    # CharField to store a URL string (e.g., "https://example.com/car1.jpg").
    # In production you'd likely use Django's ImageField/FileField with
    # upload_to= to handle file uploads, but storing URLs is simpler for now.
    image_url = models.CharField(max_length=255)

    # BooleanField stores True/False (a CHECK or TINYINT in the database).
    # default=False: new images are NOT primary by default.
    # The view/template can use this to pick which image to show as the
    # "main" photo for a car listing.
    is_primary = models.BooleanField(default=False)

    def __str__(self):
        # The f-string calls self.car.__str__() automatically
        # (Django converts the Car object to its string representation).
        return f'Image for {self.car}'
