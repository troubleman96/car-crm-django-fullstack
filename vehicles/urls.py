from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.landing_page, name='landing'),
    path('car/<int:car_id>/', views.car_detail, name='car_detail'),
]
