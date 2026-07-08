from django.contrib import admin
from .models import Lead, Appointment


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    readonly_fields = ['created_at']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'source', 'status', 'interested_car', 'assigned_to', 'created_at']
    list_filter = ['source', 'status', 'interested_car__make']
    search_fields = ['full_name', 'phone']
    inlines = [AppointmentInline]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['lead', 'car', 'type', 'scheduled_at', 'status', 'created_at']
    list_filter = ['type', 'status', 'scheduled_at']
    search_fields = ['lead__full_name', 'lead__phone']
