
from django.contrib import admin


from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import CustomUser, OTP


class CustomUserAdmin(BaseUserAdmin):


    list_display = [
        'phone',
        'full_name',
        'is_customer',
        'is_staff',
        'is_active',
    ]


    list_filter = [
        'is_customer',
        'is_staff',
        'groups',
    ]


    search_fields = [
        'phone',
        'full_name',
    ]


    ordering = ['-created_at']


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


    add_fieldsets = [
        (None, {
            'classes': ['wide'],
            'fields': [
                'phone',
                'full_name',
                'password1',
                'password2',
                'is_customer',
                'is_staff',
            ],
        }),
    ]


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):


    list_display = [
        'phone',
        'code',
        'expires_at',
        'is_used',
        'created_at',
    ]


    list_filter = ['is_used']


    search_fields = ['phone']


    readonly_fields = [
        'phone',
        'code',
        'expires_at',
        'created_at',
    ]


admin.site.register(CustomUser, CustomUserAdmin)
