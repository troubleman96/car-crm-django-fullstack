from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', views.staff_login_view, name='staff_login'),
    path('logout/', views.staff_logout_view, name='staff_logout'),
    path('otp/send/', views.customer_otp_send, name='otp_send'),
    path('otp/verify/', views.customer_otp_verify, name='otp_verify'),
]
