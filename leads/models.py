"""
leads/models.py — Database models for the Leads & Appointments app.

This file defines two models:
  - Lead:     A potential customer who has shown interest in a vehicle.
  - Appointment: A scheduled event (test drive, call-back, showroom visit)
                tied to a specific Lead.

These models are the backbone of the customer relationship workflow.
Other parts of the project (views, admin, chatbot) read and write
these models to manage the dealership's sales pipeline.
"""

# -------------------------------------------------------------------
# Django's models module gives us the base class `Model` and all the
# field types (CharField, ForeignKey, DateTimeField, etc.).
# -------------------------------------------------------------------
from django.db import models

# settings.AUTH_USER_MODEL points to the custom User model for this
# project (or the default Django User). We use it instead of a hard-
# coded 'User' string so the relationship respects the project's
# user configuration. This is a Django best practice.
from django.conf import settings


class Lead(models.Model):
    """
    Represents a sales lead — a person who might buy a car.

    Each Lead stores:
      - Who they are (name, phone)
      - How they found us (source)
      - Which car they're interested in
      - What stage of the sales process they're in (status)
      - Which salesperson is handling them (assigned_to)

    Relationships:
      - customer    -> links to the User model (could be a registered user or None)
      - interested_car -> links to a Car in the vehicles app
      - assigned_to  -> links to the User model (the salesperson)
    """

    # --- SOURCE_CHOICES ---
    # A list of (stored_value, display_label) tuples. Django uses the
    # first element in each tuple as the actual database value and the
    # second for human-readable display (e.g., in admin drop-downs).
    # The 'choices' parameter on a CharField enforces that only these
    # values are allowed.
    SOURCE_CHOICES = [
        ('website', 'Website'),   # Lead came from the main website form
        ('chatbot', 'Chatbot'),   # Lead came from the live chat bot
        ('campaign', 'Campaign'), # Lead came from a marketing campaign
        ('walk_in', 'Walk-in'),   # Customer walked into the showroom
    ]

    # --- STATUS_CHOICES ---
    # These represent the stages of the sales pipeline. A lead is
    # 'new' when created, then moves through 'contacted' -> 'qualified'
    # -> 'won' or 'lost' as the sales team works it.
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('won', 'Won'),
        ('lost', 'Lost'),
    ]

    # ------------------------------------------------------------------
    # customer: ForeignKey to the User model.
    #   - SET_NULL: if the User is deleted, the lead's customer field
    #     becomes NULL instead of being deleted (data preservation).
    #   - null=True, blank=True: the lead might be anonymous (e.g., a
    #     chatbot conversation without login), so this is optional.
    # ------------------------------------------------------------------
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    # phone: The customer's phone number. This is often the primary
    # identifier for a lead because many users interact via SMS or chat
    # without creating an account. Stored as a CharField (not IntegerField)
    # because phone numbers can start with 0, contain +, etc.
    phone = models.CharField(max_length=15)

    # full_name: Optional — the customer might not give their name
    # immediately (e.g., first chatbot message).
    full_name = models.CharField(max_length=150, null=True, blank=True)

    # source: How the lead entered the system. Defaults to 'website'.
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default='website')

    # interested_car: ForeignKey to the vehicles.Car model.
    #   - The string 'vehicles.Car' is a "lazy reference" — it avoids
    #     circular import issues by letting Django resolve the
    #     relationship at runtime.
    #   - SET_NULL: if the Car is removed from inventory, the lead
    #     record is kept (the field just becomes NULL).
    interested_car = models.ForeignKey(
        'vehicles.Car', on_delete=models.SET_NULL, null=True, blank=True
    )

    # status: The lead's current stage in the sales pipeline.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='new')

    # assigned_to: ForeignKey to the User model — the salesperson handling
    # this lead. related_name='assigned_leads' lets us do
    # `user.assigned_leads.all()` to get all leads for a given user.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='assigned_leads'
    )

    # auto_now_add=True: Automatically set to the current timestamp when
    # the row is first created. This value is NOT updated on subsequent saves.
    created_at = models.DateTimeField(auto_now_add=True)

    # auto_now=True: Automatically set to the current timestamp EVERY time
    # the row is saved. Great for "last updated" tracking.
    updated_at = models.DateTimeField(auto_now=True)

    # --- Meta class ---
    # Meta is a special inner class where we configure model-level options.
    # Here we set the default ordering so that queries return newest leads
    # first (descending created_at). The '-' prefix means descending order.
    class Meta:
        ordering = ['-created_at']

    # --- __str__ method ---
    # This defines the human-readable representation of a Lead object.
    # Django uses this everywhere: the admin panel, error messages,
    # foreign key drop-downs, etc.
    def __str__(self):
        # Use full_name if available; otherwise fall back to phone.
        # Append the source in parentheses for easy identification.
        return f'{self.full_name or self.phone} ({self.source})'


class Appointment(models.Model):
    """
    Represents a scheduled appointment tied to a Lead.

    An appointment can be:
      - A test drive of a specific car
      - A call-back request from the sales team
      - A showroom visit

    Relationships:
      - lead -> links to Lead (each appointment belongs to one lead)
      - car  -> links to Car (optional — some appointments don't specify
                a particular car)
    """

    # Choices for what kind of appointment this is.
    TYPE_CHOICES = [
        ('test_drive', 'Test Drive'),
        ('call_back', 'Call Back'),
        ('showroom_visit', 'Showroom Visit'),
    ]

    # Choices for the appointment's current status.
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # ForeignKey to Lead with CASCADE delete: if the Lead is deleted,
    # all its appointments are deleted too. related_name='appointments'
    # allows us to access `lead.appointments.all()`.
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='appointments')

    # ForeignKey to Car (optional). A test drive needs a car specified;
    # a call-back might not.
    car = models.ForeignKey('vehicles.Car', on_delete=models.SET_NULL, null=True, blank=True)

    # type: The kind of appointment (test drive, call back, etc.).
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)

    # scheduled_at: When the appointment is supposed to happen.
    # This is a DateTimeField (not DateField) because we need time.
    scheduled_at = models.DateTimeField()

    # status: Starts as 'pending' by default.
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    # notes: Optional free-text field for sales team notes about the appointment.
    notes = models.TextField(null=True, blank=True)

    # Recorded automatically when the appointment row is first created.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Show upcoming/scheduled appointments first (most recent dates).
        ordering = ['-scheduled_at']

    def __str__(self):
        # get_type_display() is a Django convenience method automatically
        # created for any field with 'choices'. It returns the human-readable
        # label (e.g., "Test Drive") instead of the stored value ("test_drive").
        return f'{self.get_type_display()} - {self.lead}'
