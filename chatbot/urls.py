from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('message/', views.chat_message_view, name='message'),
    path('history/<int:session_id>/', views.chat_session_history, name='history'),
]
