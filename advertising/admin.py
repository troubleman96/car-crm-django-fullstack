
from django.contrib import admin


from .models import Banner, Promotion


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):


    list_display = ['title', 'is_active', 'order', 'created_at']


    list_filter = ['is_active']


    search_fields = ['title']


    list_editable = ['is_active', 'order']


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):


    list_display = ['car', 'label', 'discount_percent', 'is_active', 'starts_at', 'ends_at']


    list_filter = ['label', 'is_active']


    search_fields = ['car__make', 'car__model']


    list_editable = ['is_active']
