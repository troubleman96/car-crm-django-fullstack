
import random
from datetime import timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q

from .models import CustomUser, OTP
from .forms import StaffLoginForm, PhoneForm, OTPVerifyForm
from notifications.services import send_sms, normalize_phone


def staff_login_view(request):
    if request.user.is_authenticated:
        return redirect('/admin/')

    form = StaffLoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.cleaned_data['user']

        login(request, user)

        return redirect('/admin/')

    return render(request, 'accounts/staff_login.html', {'form': form})


def staff_logout_view(request):
    logout(request)
    return redirect('/')


def customer_otp_send(request):
    form = PhoneForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        phone = normalize_phone(form.cleaned_data['phone'])

        code = f'{random.randint(0, 999999):06d}'

        print(f'[DEV] OTP for {phone}: {code}')

        expires_at = timezone.now() + timedelta(minutes=5)

        OTP.objects.create(phone=phone, code=code, expires_at=expires_at)

        sms_sent = send_sms(phone, f'Your verification code is {code}. Valid for 5 minutes.')

        if not sms_sent:
            print(f'[DEV] SMS send failed — OTP {code} is still valid for {phone}')
            request.session['otp_phone'] = phone
            return redirect('accounts:otp_verify')

        request.session['otp_phone'] = phone

        return redirect('accounts:otp_verify')

    return render(request, 'accounts/otp_send.html', {'form': form})


def customer_otp_verify(request):
    phone = request.session.get('otp_phone')

    if not phone:
        return redirect('accounts:otp_send')

    form = OTPVerifyForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        code = form.cleaned_data['code']
        now = timezone.now()
        otp = OTP.objects.filter(
            Q(phone=phone) & Q(code=code) & Q(is_used=False) & Q(expires_at__gt=now)
        ).first()

        if otp:
            otp.is_used = True
            otp.save()

            user, _ = CustomUser.objects.get_or_create(
                phone=phone,
                defaults={
                    'is_customer': True,
                    'is_staff': False,
                },
            )

            login(request, user)

            next_url = request.session.pop('booking_next', '/')
            return redirect(next_url)

        messages.error(request, 'Invalid or expired code.')

    return render(request, 'accounts/otp_verify.html', {'form': form})
