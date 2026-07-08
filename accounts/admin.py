"""
accounts/admin.py
=================

PURPOSE:
    Configures how the models from accounts/models.py appear in Django's
    built-in admin interface (the /admin/ URL).

    Without this file, CustomUser and OTP would not show up in the admin
    at all (or would appear with a generic, unhelpful layout).

WHAT YOU'LL LEARN:
    - How to register models with the admin site using the @admin.register
      decorator and admin.site.register().
    - How to customise the list view (list_display, list_filter, search_fields).
    - How to organise the detail form with fieldsets (grouping fields into
      collapsible sections).
    - How to subclass UserAdmin to preserve Django's built-in user admin
      features (password change form, permissions UI) while adding our
      custom fields.
    - How to make fields read-only so they cannot be edited in the admin.

RELATIONSHIP TO OTHER FILES:
    - accounts/models.py  imports the models being registered here.
    - The 'CustomUser' model replaces Django's default User via
      AUTH_USER_MODEL in settings.py, so we must also replace the default
      UserAdmin with our CustomUserAdmin.
"""

from django.contrib import admin
# UserAdmin is Django's default admin configuration for the User model.
# We subclass it to adapt it for our CustomUser model (which has different
# fields like 'phone' instead of 'username').
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group    # Django's built-in group model.

from .models import CustomUser, OTP


# ===================================================================
# CUSTOM USER ADMIN
# ===================================================================
# By default, Django's UserAdmin expects fields like 'username', 'email',
# 'first_name', 'last_name'.  Our CustomUser model replaces 'username'
# with 'phone' and has different fields.  So we need to tell the admin
# exactly which fields to display and in what order.
#
# We subclass BaseUserAdmin (which is just UserAdmin imported under a
# different name) and override the key attributes:
#   - list_display       – columns shown in the user list view.
#   - list_filter        – sidebar filters for narrowing down the list.
#   - search_fields      – fields that the search box will query.
#   - ordering           – default sort order.
#   - fieldsets          – layout of the detail/edit form.
#   - add_fieldsets      – layout of the "Add user" form.
# ===================================================================

class CustomUserAdmin(BaseUserAdmin):
    """
    Admin configuration for the CustomUser model.

    -------------------------------------------------------------------
    LIST VIEW (the page that shows all users)
    -------------------------------------------------------------------
    Each attribute below customises the "change list" page
    (the page at /admin/accounts/customuser/).
    """

    # ---------- Columns in the list table ----------
    # Each entry is a field name or callable.  Django will display one
    # column per field.  Clicking on a column header sorts by that field
    # (if the field supports sorting).
    list_display = [
        'phone',           # Phone number (the user's primary identifier).
        'full_name',       # Display name (nullable — shows "-" if empty).
        'is_customer',     # Boolean icon (green checkmark or red X).
        'is_staff',        # Boolean icon — can they access the admin?
        'is_active',       # Boolean icon — is the account enabled?
    ]

    # ---------- Sidebar filters ----------
    # list_filter adds filter options in the right sidebar of the list view.
    # Users can click, e.g., "is_customer = Yes" to see only customers.
    # 'groups' lets admins filter by which permission group a user belongs to.
    list_filter = [
        'is_customer',
        'is_staff',
        'groups',
    ]

    # ---------- Search box ----------
    # When an admin types in the search box, Django will search these
    # fields for a match.  The default lookup is "icontains"
    # (case-insensitive contains).
    search_fields = [
        'phone',
        'full_name',
    ]

    # ---------- Default ordering ----------
    # Newest users appear first.  The minus sign means descending order.
    ordering = ['-created_at']

    # ---------- Detail / Edit form layout ----------
    # fieldsets is a list of tuples.  Each tuple is:
    #   (section_title, {'fields': [list_of_field_names]})
    #
    # This organises the form into collapsible sections (visible in the
    # "change" page — when you click on an individual user).
    #
    # NOTE: We do NOT include 'username' (our model doesn't have one),
    # but we DO include every other field that the default UserAdmin
    # expects so the password change form still works.
    fieldsets = [
        (None, {
            'fields': ['phone', 'password']
        }),
        ('Personal info', {
            'fields': ['full_name']
        }),
        ('Permissions', {
            'fields': [
                'is_customer',
                'is_staff',
                'is_active',
                'is_superuser',
                'groups',
            ]
        }),
        ('Important dates', {
            'fields': ['last_login', 'date_joined']
        }),
    ]

    # ---------- "Add user" form layout ----------
    # add_fieldsets controls the layout of the "Add user" page
    # (/admin/accounts/customuser/add/).  It is separate from fieldsets
    # because the add form typically needs password1 + password2
    # (to confirm the password), while the edit form shows the password
    # as a clickable link to a separate change-password page.
    #
    # 'classes': ['wide'] gives the form fields more horizontal space.
    add_fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': [
                'phone',
                'full_name',
                'password1',   # Django will render password fields automatically
                'password2',   # when we extend BaseUserAdmin.
                'is_customer',
                'is_staff',
            ],
        }),
    ]


# ===================================================================
# OTP ADMIN
# ===================================================================
# The OTP model is registered using the @admin.register decorator instead
# of admin.site.register().  Both approaches work — the decorator is
# slightly more modern and keeps the registration right next to the class.
#
# Because OTP records are audit data, we make most fields read-only so
# that an admin cannot accidentally or maliciously edit OTP codes.
# ===================================================================

@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    """
    Admin configuration for the OTP model.

    Admins can view OTP records but not modify the codes or timestamps
    (they are read-only).  This is intentional — OTPs are audit/log data.
    """

    # Columns to display in the list view.
    list_display = [
        'phone',
        'code',
        'expires_at',
        'is_used',
        'created_at',
    ]

    # Filter by whether the OTP has been used.
    list_filter = ['is_used']

    # Searchable by phone number.
    search_fields = ['phone']

    # Prevent editing of core OTP data.
    # readonly_fields makes these fields display as plain text in the
    # detail form instead of input widgets.  Administrators can view
    # them but cannot change them.
    readonly_fields = [
        'phone',
        'code',
        'expires_at',
        'created_at',
    ]


# ===================================================================
# REGISTER CustomUser WITH ITS ADMIN CLASS
# ===================================================================
# We use admin.site.register() here (instead of @admin.register) because
# we needed to define the class first and then register it.  Both syntaxes
# are equivalent.
#
# We also unregister the default Group admin because we don't typically
# manage groups through the admin — but we keep the Group model registered
# as-is (Django auto-registers it).  The import of Group at the top is
# used implicitly by the 'groups' fields in list_filter and fieldsets.
# ===================================================================

admin.site.register(CustomUser, CustomUserAdmin)
