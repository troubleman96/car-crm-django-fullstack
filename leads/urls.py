from django.urls import path
from . import views

app_name = 'leads'

urlpatterns = [
    path('book/', views.book_appointment, name='book'),
]
