from django import forms
from django.contrib.auth import authenticate

from notifications.services import normalize_phone


class StaffLoginForm(forms.Form):

    phone = forms.CharField(max_length=15, label='Phone Number')
    password = forms.CharField(widget=forms.PasswordInput, label='Password')

    def clean(self):
        cleaned = super().clean()

        phone = cleaned.get('phone')
        password = cleaned.get('password')

        if phone and password:
            phone = normalize_phone(phone)

            user = authenticate(phone=phone, password=password)

            if user is None:
                raise forms.ValidationError('Invalid phone number or password.')

            if not user.is_staff:
                raise forms.ValidationError('This account does not have staff access.')

            cleaned['user'] = user

        return cleaned


class PhoneForm(forms.Form):

    phone = forms.CharField(max_length=15, label='Phone Number')


class OTPVerifyForm(forms.Form):

    code = forms.CharField(max_length=6, label='Verification Code')
