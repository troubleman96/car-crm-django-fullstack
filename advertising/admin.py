"""
advertising/admin.py
====================

Configures how the 'advertising' app's models (Banner, Promotion) appear in
Django's admin interface.

The admin panel is a powerful built-in feature that auto-generates a full CRUD
(Create, Read, Update, Delete) interface for your models. You configure it
here — deciding which fields appear in lists, what filters are available,
and which fields can be edited directly from the list view.

To access the admin:
    1. Create a superuser:  python manage.py createsuperuser
    2. Run the server:      python manage.py runserver
    3. Visit:               http://127.0.0.1:8000/admin/
"""

from django.contrib import admin

# Import the models we want to register with the admin interface.
from .models import Banner, Promotion


# -------------------------------------------------------------------
# @admin.register(Banner) is a decorator that registers Banner with the
# admin site using BannerAdmin as the configuration class.
#
# The decorator approach (@admin.register) is the modern way to register
# models. The older way is:
#     admin.site.register(Banner, BannerAdmin)
# Both work — the decorator is just more concise and keeps the model and
# its admin class close together.
# -------------------------------------------------------------------
@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """
    Customises the Banner admin pages.
    """

    # -------------------------------------------------------------------
    # list_display: Sets the columns shown in the banner list view.
    #
    # Each item in the list is a field name (or method name) on the model.
    # Django displays these as columns. Clicking a column header may sort
    # the list (depending on the field type).
    #
    # Here we show: title, active status, display order, and creation date.
    # -------------------------------------------------------------------
    list_display = ['title', 'is_active', 'order', 'created_at']

    # -------------------------------------------------------------------
    # list_filter: Adds a sidebar with a filter for is_active (Yes/No/All).
    # This lets an admin quickly see only active or only inactive banners.
    # -------------------------------------------------------------------
    list_filter = ['is_active']

    # -------------------------------------------------------------------
    # search_fields: Adds a search bar that searches across the 'title' field.
    # Typing "summer" would find banners with "summer" in the title.
    # -------------------------------------------------------------------
    search_fields = ['title']

    # -------------------------------------------------------------------
    # list_editable: Makes fields editable directly from the LIST view
    # (without having to click into each item's detail page).
    #
    # With list_editable = ['is_active', 'order'], the admin can:
    #   - Toggle a banner on/off with a checkbox
    #   - Change the order by typing a number
    #   - Then click "Save" at the bottom — all changes are saved at once.
    #
    # This is a HUGE time-saver for bulk operations! However, the fields
    # in list_editable MUST also appear in list_display (so Django knows
    # where to put the editable widget).
    #
    # IMPORTANT: Fields in list_editable come AFTER any link fields in
    # list_display. Django puts the "edit link" on the first column of
    # list_display — so if you make the first field editable, you lose
    # the click-through link!
    # -------------------------------------------------------------------
    list_editable = ['is_active', 'order']


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    """
    Customises the Promotion admin pages.
    """

    # Display columns: which car the promotion is for, what label/badge it
    # has, the discount percentage, whether it's active, and date range.
    list_display = ['car', 'label', 'discount_percent', 'is_active', 'starts_at', 'ends_at']

    # Filter sidebar: filter by promotional label (e.g., show only "Sale"
    # promotions) and by active/inactive status.
    list_filter = ['label', 'is_active']

    # -------------------------------------------------------------------
    # search_fields on related model fields:
    # 'car__make' searches the Car's 'make' field.
    # 'car__model' searches the Car's 'model' field.
    #
    # The double-underscore (__) is Django's way of "following" a
    # relationship. So 'car__make' means: follow the ForeignKey 'car' to
    # the Car model, then search its 'make' field.
    #
    # This allows admins to type "Toyota" and see all promotions on Toyotas
    # without having to open each promotion to check.
    # -------------------------------------------------------------------
    search_fields = ['car__make', 'car__model']

    # Allow admins to toggle is_active directly from the list view.
    list_editable = ['is_active']
