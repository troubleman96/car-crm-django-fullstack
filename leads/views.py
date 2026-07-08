from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import Lead, Appointment
from vehicles.models import Car
from notifications.services import send_sms


def book_appointment(request):
    car_id = request.GET.get('car')
    car = None
    if car_id:
        car = get_object_or_404(Car, id=car_id, status='available')

    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        appointment_type = request.POST.get('type', 'test_drive')
        car_id = request.POST.get('car_id')
        scheduled_at_str = request.POST.get('scheduled_at', '')

        if not phone:
            messages.error(request, 'Phone number is required.')
            return render(request, 'leads/book.html', {'car': car, 'cars': Car.objects.filter(status='available')})

        interested_car = None
        if car_id:
            interested_car = Car.objects.filter(id=car_id).first()

        lead, _ = Lead.objects.get_or_create(
            phone=phone,
            defaults={'source': 'website', 'interested_car': interested_car},
        )

        try:
            scheduled_at = timezone.datetime.fromisoformat(scheduled_at_str)
        except (ValueError, TypeError):
            scheduled_at = timezone.now() + timezone.timedelta(days=1)

        appointment = Appointment.objects.create(
            lead=lead,
            car=interested_car,
            type=appointment_type,
            scheduled_at=scheduled_at,
            status='confirmed',
        )

        car_info = f'{interested_car.make} {interested_car.model}' if interested_car else 'a car'
        sms_text = f'Your {appointment.get_type_display()} for {car_info} is booked for {scheduled_at.strftime("%A, %d %B %Y at %H:%M")}. Thank you!'
        send_sms(phone, sms_text)

        messages.success(request, 'Appointment booked! Confirmation SMS sent.')
        return redirect('vehicles:landing')

    return render(request, 'leads/book.html', {
        'car': car,
        'cars': Car.objects.filter(status='available'),
    })
