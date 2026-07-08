
from django.contrib import admin


from .models import Car, CarImage


class CarImageInline(admin.TabularInline):


    model = CarImage


    extra = 1


@admin.register(Car)
class CarAdmin(admin.ModelAdmin):


    list_display = ['make', 'model', 'year', 'price', 'status', 'created_at']


    list_filter = ['status', 'make', 'year']


    search_fields = ['make', 'model', 'description']


    inlines = [CarImageInline]


@admin.register(CarImage)
class CarImageAdmin(admin.ModelAdmin):


    list_display = ['car', 'image_url', 'is_primary']


    list_filter = ['is_primary']
