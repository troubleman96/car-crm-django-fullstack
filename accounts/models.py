from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class CustomUserManager(BaseUserManager):

    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required')

        user = self.model(phone=phone, **extra_fields)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_customer', False)

        return self.create_user(phone, password, **extra_fields)


class CustomUser(AbstractUser):

    username = None

    phone = models.CharField(max_length=15, unique=True)

    full_name = models.CharField(max_length=150, null=True, blank=True)

    password = models.CharField(max_length=255, null=True, blank=True)

    is_customer = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'phone'

    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return self.full_name or self.phone


class OTP(models.Model):

    phone = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f'{self.phone} - {self.code}'
