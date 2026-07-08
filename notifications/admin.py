"""
notifications/admin.py
======================

Configures how the SmsLog model appears in the Django admin interface.

The Django admin is a powerful auto-generated UI for managing your
application's data. By registering a model with a ModelAdmin class,
we control:
  - Which fields appear in the list view.
  - Which columns are sortable / searchable / filterable.
  - Which fields are read-only.

Related file:
  - notifications/models.py — the SmsLog model this admin configures.
"""

from django.contrib import admin
from .models import SmsLog


# -----------------------------------------------------------------------
# Register SmsLog with a custom admin class
# -----------------------------------------------------------------------
# The @admin.register() decorator is a clean way to register a model
# with the admin site. It is equivalent to calling:
#   admin.site.register(SmsLog, SmsLogAdmin)
# but keeps the registration right next to the class definition.
@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    """
    Admin configuration for the SmsLog model.

    Because SmsLog is an audit log, we want staff to be able to
    VIEW entries but not create, edit, or delete them. We achieve
    this by making all fields read-only.
    """

    # -- List view columns -----------------------------------------------
    # list_display controls which fields appear as columns in the
    # admin's "change list" page (the main listing of all records).
    # Each entry can be:
    #   - a model field name (string, e.g. 'phone', 'status')
    #   - a custom method name (e.g. 'message_preview')
    list_display = [
        'phone',
        'message_preview',       # custom method (see below)
        'status',
        'provider_message_id',
        'created_at',
    ]

    # -- Filters & search ------------------------------------------------
    # list_filter adds a sidebar with filter options. Here we add
    # a filter on the 'status' field so staff can quickly see only
    # 'failed' or 'sent' entries.
    list_filter = ['status']

    # search_fields enables the search bar at the top of the list.
    # Django will search for the user's query in the 'phone' and
    # 'message' fields (using an SQL "LIKE" query behind the scenes).
    search_fields = ['phone', 'message']

    # -- Read-only fields ------------------------------------------------
    # readonly_fields prevents staff from editing these fields in
    # the detail form. Since SmsLog is an immutable audit record,
    # we mark everything as read-only.
    readonly_fields = [
        'phone',
        'message',
        'status',
        'provider_message_id',
        'created_at',
    ]

    # -- Custom list column: message_preview -----------------------------
    @admin.display(description='Message')
    def message_preview(self, obj):
        """
        Return a truncated version of the message for the list view.

        The @admin.display decorator sets the column header label
        in the admin. Without it, Django would use "Message Preview".

        Why truncate? SMS messages can be hundreds of characters long.
        Showing the full message in the list would make the table
        unreadable. Instead we show the first 60 characters with an
        ellipsis.

        Args:
            obj: An SmsLog instance (automatically passed by Django).

        Returns:
            A string of up to 63 characters.
        """
        if len(obj.message) > 60:
            return obj.message[:60] + '...'
        return obj.message
