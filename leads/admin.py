"""
leads/admin.py — Django admin configuration for the Leads app.

This file registers the Lead and Appointment models with Django's
built-in admin interface and customises how they are displayed,
filtered, and searched.

By registering models here, the sales team can manage leads and
appointments through the /admin/ web interface without needing
to write SQL or use the Django shell.
"""

# The admin module provides ModelAdmin (for customising the admin
# interface) and the registration decorator @admin.register().
from django.contrib import admin

# Import the models we want to register with the admin site.
from .models import Lead, Appointment


class AppointmentInline(admin.TabularInline):
    """
    Allows viewing/editing Appointments directly on the Lead admin page.

    "Inline" means the appointments appear as a table embedded within the
    Lead's change form — you don't have to navigate away to see them.

    TabularInline displays them in a row-and-column table layout (as
    opposed to StackedInline which shows them in a stacked block layout).

    Attributes:
      - model:      Which model to inline (Appointment, in this case).
      - extra:      How many empty rows to show for adding new records.
                    0 means "don't show extra blank forms."
      - readonly_fields: Fields shown but not editable in the inline.
    """
    model = Appointment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """
    Customise how Lead objects appear in the Django admin.

    @admin.register(Lead) is a decorator that registers this class as
    the admin configuration for the Lead model. It's equivalent to:
        admin.site.register(Lead, LeadAdmin)

    Attributes:
      - list_display: Controls which columns appear in the list view.
      - list_filter:  Adds filter sidebar widgets on the right.
      - search_fields: Enables the search box at the top of the list view.
      - inlines:      Embeds related models (Appointment) on the detail page.
    """
    list_display = [
        'full_name', 'phone', 'source', 'status',
        'interested_car', 'assigned_to', 'created_at',
    ]
    # list_filter generates filter links based on the field values.
    # 'interested_car__make' uses the double-underscore (__) to follow
    # the ForeignKey relationship and filter by the Car's make field.
    list_filter = ['source', 'status', 'interested_car__make']
    search_fields = ['full_name', 'phone']
    # inlines = [AppointmentInline] attaches the inline so that when
    # you edit a Lead, you see all its appointments in the same page.
    inlines = [AppointmentInline]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """
    Customise how Appointment objects appear in the Django admin.
    """
    list_display = ['lead', 'car', 'type', 'scheduled_at', 'status', 'created_at']
    list_filter = ['type', 'status', 'scheduled_at']
    # For searching by a related model's field, use double underscores:
    # 'lead__full_name' means "search in Lead.full_name".
    search_fields = ['lead__full_name', 'lead__phone']
