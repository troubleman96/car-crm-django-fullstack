"""
accounts/models.py
===================

PURPOSE:
    Defines the database models (tables) for the 'accounts' Django app.
    This app handles user authentication — both staff (admin) users and
    customer (website) users.

WHAT YOU'LL LEARN:
    - How to create a custom user model that uses phone numbers instead of
      usernames or emails for login.
    - How to write a custom model manager (BaseUserManager subclass) so that
      Django knows how to create users and superusers with your custom fields.
    - How to define a simple OTP model for phone-based authentication.
    - How Django model fields become database columns, and how Meta classes
      add indexes and other table-level behaviour.

RELATIONSHIP TO OTHER FILES:
    - accounts/forms.py  uses these models to validate and authenticate users.
    - accounts/views.py  queries these models (e.g. creating OTP records,
                        looking up users by phone).
    - accounts/admin.py  registers these models so they appear in the Django
                        admin interface.
"""

# ---------------------------------------------------------------------------
# django.contrib.auth.models provides AbstractUser (a ready-made User model
# with password hashing, permissions, etc.) and BaseUserManager (a helper
# class for writing custom "object" managers that know how to create users).
# ---------------------------------------------------------------------------
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models               # Django's ORM — turns Python
# classes into database tables.


# ===================================================================
# CUSTOM USER MANAGER
# ===================================================================
# Django expects every User model to have a corresponding Manager that
# provides create_user() and create_superuser() methods.  We subclass
# BaseUserManager so we keep all the default Manager behaviour but can
# customise how new users are created (in our case, using a phone number
# instead of a username).
# ===================================================================

class CustomUserManager(BaseUserManager):
    """
    Manager for the CustomUser model.

    Because we removed the 'username' field, we must tell Django how to
    create users and superusers.  The default UserManager assumes a
    username field exists, so we override it here.

    Key concepts:
        - self.model  refers to the model this manager is attached to
                       (i.e. CustomUser).
        - self._db    is the database alias (usually 'default') so that
                       saves go to the right database.
        - set_password()  hashes the password — we NEVER store raw passwords.
        - set_unusable_password()  marks the user as having no usable password
                       (useful for OTP-only customer accounts).
    """

    def create_user(self, phone, password=None, **extra_fields):
        """
        Create and return a regular user identified by their phone number.

        Steps:
            1. Validate that a phone number was provided.
            2. Build a model instance (not yet saved to DB).
            3. Hash the password if one was given, otherwise mark the
               password as unusable (the user will log in via OTP instead).
            4. Save to the database.
            5. Return the user object.
        """
        if not phone:
            raise ValueError('Phone number is required')

        # Build an unsaved CustomUser instance with the fields we have.
        user = self.model(phone=phone, **extra_fields)

        if password:
            # Hashes the password so the raw text is never stored.
            user.set_password(password)
        else:
            # For customer accounts (OTP-based login), there is no password.
            # set_unusable_password() makes login(password) always fail,
            # which is exactly what we want — customers authenticate via SMS code.
            user.set_unusable_password()

        # save(using=self._db) ensures we use the correct database.
        # In a multi-DB setup, 'using' tells Django which DB to write to.
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """
        Create a superuser (staff member with full admin access).

        We automatically set:
            - is_staff = True   (can access the Django admin)
            - is_superuser = True (has every permission)
            - is_customer = False (so the admin listing distinguishes
                                   staff from website customers)

        Then we delegate to create_user() to handle the common logic.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_customer', False)

        return self.create_user(phone, password, **extra_fields)


# ===================================================================
# CUSTOM USER MODEL
# ===================================================================
# AbstractUser already provides:
#   - password, last_login, is_superuser, groups, user_permissions,
#     date_joined
# We keep most of those and only override what we need.
#
# WHY a custom user model?
#   Django's default User model uses a 'username' field.  Our project
#   identifies users by their phone number instead, so we need to swap
#   it out.  The official Django docs *strongly* recommend setting
#   AUTH_USER_MODEL at the start of every new project for this reason.
# ===================================================================

class CustomUser(AbstractUser):
    """
    Our application's user model.

    Differences from the default Django User:
        - No username field (we set username = None).
        - Login is done via 'phone' (the USERNAME_FIELD).
        - Customers do NOT have a password (they authenticate via OTP).
        - Staff users have a password and log in through a separate form.

    Fields (each becomes a column in the 'accounts_customuser' table):
        phone       – Tanzania phone number, unique, serves as the login ID.
        full_name   – Display name (nullable because the customer might not
                      provide it during initial OTP registration).
        password    – Overrides the inherited password field to make it
                      nullable (customers don't need a password).
        is_customer – Boolean flag to easily distinguish customers from staff
                      in queries and the admin.
        is_staff    – Inherited from AbstractUser; controls admin access.
        is_active   – Inherited; can be used to deactivate accounts.
        created_at  – Auto-set timestamp of when the user was first created.

    Relationships to other models:
        - This model is referenced by everything that has a "user" FK
          (e.g. orders, enquiries, bookings).
        - Django's AUTH_USER_MODEL setting in settings.py points here.
    """

    # -------------------------------------------------------------------
    # Remove the inherited 'username' field entirely.
    # Setting it to None tells Django "don't create this column".
    # -------------------------------------------------------------------
    username = None

    # -------------------------------------------------------------------
    # Phone number — the primary identifier for every user.
    # CharField because phone numbers can start with '+' and contain digits.
    # max_length=15  comfortably holds international numbers (+2557XXXXXXXX).
    # unique=True    ensures no two users share the same phone number.
    # -------------------------------------------------------------------
    phone = models.CharField(max_length=15, unique=True)

    # -------------------------------------------------------------------
    # Full name — optional for customers (they might not have filled a profile).
    # null=True   allows the database to store NULL for missing values.
    # blank=True  allows Django forms to accept an empty string.
    # -------------------------------------------------------------------
    full_name = models.CharField(max_length=150, null=True, blank=True)

    # -------------------------------------------------------------------
    # Password — overriding AbstractUser's password field to make it
    # nullable.  Customer accounts (OTP-based) have no password, so this
    # column will be NULL for them.  Staff accounts still store a hashed
    # password here.
    # -------------------------------------------------------------------
    password = models.CharField(max_length=255, null=True, blank=True)

    # -------------------------------------------------------------------
    # is_customer — a custom boolean that is NOT on the default User model.
    # Defaults to True because the majority of users will be customers.
    # We use this in the admin to filter and display user types.
    # -------------------------------------------------------------------
    is_customer = models.BooleanField(default=True)

    # -------------------------------------------------------------------
    # is_staff — inherited from AbstractUser, but we redeclare it with a
    # default of False so that new users are NOT automatically given
    # admin access.
    # -------------------------------------------------------------------
    is_staff = models.BooleanField(default=False)

    # -------------------------------------------------------------------
    # is_active — inherited, redeclared with default True (user is active
    # from the moment they verify their phone).
    # -------------------------------------------------------------------
    is_active = models.BooleanField(default=True)

    # -------------------------------------------------------------------
    # created_at — automatically set to the current timestamp when the
    # row is first inserted.  auto_now_add=True means it is NOT updated
    # on subsequent saves.
    # -------------------------------------------------------------------
    created_at = models.DateTimeField(auto_now_add=True)

    # -------------------------------------------------------------------
    # USERNAME_FIELD tells Django which field is used for authentication
    # (i.e., the identifier the user types in the login form).
    # By default it is 'username'; we change it to 'phone'.
    # -------------------------------------------------------------------
    USERNAME_FIELD = 'phone'

    # -------------------------------------------------------------------
    # REQUIRED_FIELDS is a list of field names that will be prompted for
    # when creating a superuser via `createsuperuser`.
    # Because we don't require email or full_name, the list is empty.
    # -------------------------------------------------------------------
    REQUIRED_FIELDS = []

    # -------------------------------------------------------------------
    # Attach our custom manager so that CustomUser.objects.create_user()
    # and create_superuser() work correctly.
    # -------------------------------------------------------------------
    objects = CustomUserManager()

    def __str__(self):
        """
        The human-readable representation of a user.

        Django admin and shell use this to display the object.
        We show the full name if available, otherwise fall back to the
        phone number (every user is guaranteed to have one).
        """
        return self.full_name or self.phone


# ===================================================================
# OTP MODEL (One-Time Password)
# ===================================================================
# When a customer enters their phone number on the website, we send them
# a 6-digit code via SMS.  That code and its metadata are stored here.
#
# This model is the "server-side record" of every OTP that was issued.
# The verification view will look up a matching record to decide whether
# the code the user typed is correct and still valid.
# ===================================================================

class OTP(models.Model):
    """
    Stores a one-time verification code sent via SMS.

    Fields:
        phone      – The phone number the code was sent to.
        code       – The 6-digit numeric code (stored as a string so
                     leading zeros are preserved, e.g. "004235").
        expires_at – Timestamp after which this code is no longer valid.
        is_used    – Boolean flag to prevent replay attacks: once an OTP
                     is verified, it cannot be used again.
        created_at – Timestamp of when the OTP was created.
    """

    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """
        Meta options are not fields — they configure table-level behaviour.

        Here we add a database index on the 'phone' column so that lookups
        like  OTP.objects.filter(phone='...')  are fast, even when the
        table has thousands of rows.  Without an index, the database would
        have to scan every row (a "full table scan").
        """
        indexes = [
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        """
        String representation for the admin and shell: "phone - code"
        Example: "+255712345678 - 482901"
        """
        return f'{self.phone} - {self.code}'
