from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Car
from advertising.models import Banner, Promotion


def landing_page(request):
    cars = Car.objects.filter(status='available').prefetch_related('images')
    banners = Banner.objects.filter(is_active=True)
    now = timezone.now()
    promotions = Promotion.objects.filter(
        is_active=True,
        starts_at__lte=now,
        ends_at__gte=now,
    ).select_related('car')
    return render(request, 'vehicles/landing.html', {
        'cars': cars,
        'banners': banners,
        'promotions': promotions,
    })


def car_detail(request, car_id):
    car = get_object_or_404(Car.objects.prefetch_related('images'), id=car_id)
    return render(request, 'vehicles/car_detail.html', {'car': car})
