from django.contrib import admin
from .models import SmsLog


@admin.register(SmsLog)
class SmsLogAdmin(admin.ModelAdmin):
    list_display = ['phone', 'message_preview', 'status', 'provider_message_id', 'created_at']
    list_filter = ['status']
    search_fields = ['phone', 'message']
    readonly_fields = ['phone', 'message', 'status', 'provider_message_id', 'created_at']

    @admin.display(description='Message')
    def message_preview(self, obj):
        return obj.message[:60] + '...' if len(obj.message) > 60 else obj.message
