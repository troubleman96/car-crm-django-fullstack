from django.shortcuts import render, get_object_or_404
from .models import Car


def landing_page(request):
    cars = Car.objects.filter(status='available').prefetch_related('images')
    return render(request, 'vehicles/landing.html', {'cars': cars})


def car_detail(request, car_id):
    car = get_object_or_404(Car.objects.prefetch_related('images'), id=car_id)
    return render(request, 'vehicles/car_detail.html', {'car': car})
