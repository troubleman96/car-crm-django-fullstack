"""
vehicles/admin.py
=================

Django's built-in admin interface is a powerful, auto-generated UI for managing
your application's data. This file configures HOW our models appear in that
admin interface.

You access the admin at:  /admin/   (requires a superuser account)

Without registering models here, they won't show up in the admin at all.

Steps to register a model in the admin:
    1. Import the model from .models
    2. Optionally create a ModelAdmin subclass to customize the admin page
    3. Decorate with @admin.register() or call admin.site.register()
"""

from django.contrib import admin

# Import models from THIS app's models.py so we can register them.
from .models import Car, CarImage


class CarImageInline(admin.TabularInline):
    """
    An "Inline" allows you to edit related models on the SAME page as the
    parent model, rather than having to switch to a separate admin page.

    Here, when editing a Car in the admin, we want to see and edit all of
    its CarImage records inline — right on the Car's change form page.

    TabularInline renders the related records as a table (rows and columns).
    There's also StackedInline which renders them as a stacked form (wider,
    more like a regular form).
    """

    # The model that will appear inline.
    model = CarImage

    # extra = 1 means "show 1 blank row at the bottom of the inline so the
    # admin user can add a new image without clicking 'Add another' first".
    # You can set this to 0, 3, etc.
    extra = 1


# -------------------------------------------------------------------
# @admin.register(Car) is a decorator that registers the Car model with
# the admin site, using the custom CarAdmin class below for configuration.
#
# Without registering, Car wouldn't appear in the admin.
# Without CarAdmin, it would still appear but with default settings.
# -------------------------------------------------------------------
@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    """
    Customizes how Car models are displayed and managed in the admin.
    """

    # -------------------------------------------------------------------
    # list_display: Controls which fields appear as COLUMNS in the car
    # list view (the "change list" page that shows all cars).
    #
    # By default, Django just shows the __str__ of each object. Here we
    # override that to show 6 columns: make, model, year, price, status,
    # and created_at.
    #
    # You can include model fields, properties, or even custom methods.
    # -------------------------------------------------------------------
    list_display = ['make', 'model', 'year', 'price', 'status', 'created_at']

    # -------------------------------------------------------------------
    # list_filter: Adds a sidebar with filter links. Each filter auto-generates
    # a list of links that let you narrow down the displayed records.
    #
    # Django understands the field types:
    #   - CharField with choices → filter by each choice value
    #   - BooleanField → filter by Yes/No/All
    #   - DateField → filter by date ranges (Today, Past 7 days, This month, etc.)
    #   - ForeignKey → filter by related objects
    #
    # Here, users can filter by status, make, and year. This is very helpful
    # when you have hundreds of cars and need to find specific ones quickly.
    # -------------------------------------------------------------------
    list_filter = ['status', 'make', 'year']

    # -------------------------------------------------------------------
    # search_fields: Adds a search bar at the top of the list view.
    # Django will search these fields for the user's query text.
    #
    # Searching across text fields uses SQL LIKE / ILIKE queries underneath.
    # For CharField/TextField, Django searches for the query string anywhere
    # in the field value.
    #
    # Here, typing "cam" would find cars with make="Camry" or where
    # "cam" appears in the model name or description.
    # -------------------------------------------------------------------
    search_fields = ['make', 'model', 'description']

    # -------------------------------------------------------------------
    # inlines: Links the CarImageInline we defined above, so when editing
    # a Car, you can add/edit/delete its images right there on the page.
    #
    # This means you don't need a separate admin page for CarImage records
    # (though we register one below for completeness).
    # -------------------------------------------------------------------
    inlines = [CarImageInline]


# -------------------------------------------------------------------
# Register CarImage separately so it also appears as its own section in
# the admin. This allows admins to browse ALL images across ALL cars,
# not just images for a specific car (which they'd see through the inline).
# -------------------------------------------------------------------
@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):
    """
    Customizes the CarImage admin page.
    """

    # Show these columns in the CarImage list view.
    # 'car' will display as a link to the related Car's change page.
    # 'image_url' shows the URL string.
    # 'is_primary' shows a checkmark or X icon.
    list_display = ['car', 'image_url', 'is_primary']

    # Add a filter sidebar so admins can quickly show only primary images
    # or only non-primary images.
    list_filter = ['is_primary']
