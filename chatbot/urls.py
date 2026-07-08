"""
chatbot/urls.py — URL configuration for the Chatbot app.

This module maps URL patterns to the two chatbot views:
  1. /chatbot/message/     — POST endpoint for sending/receiving messages.
  2. /chatbot/history/<id>/ — GET endpoint for retrieving chat history.

These are included from the project's root urls.py via:
    path('chatbot/', include('chatbot.urls'))
"""

from django.urls import path
from . import views

# Namespace for URL reversing. Usage:
#   {% url 'chatbot:message' %}  or  reverse('chatbot:history', args=[session_id])
app_name = 'chatbot'

urlpatterns = [
    # POST /chatbot/message/
    # Calls views.chat_message_view to handle a new chat message.
    # This is a JSON API — it expects JSON in the request body and
    # returns JSON in the response.
    path('message/', views.chat_message_view, name='message'),

    # GET /chatbot/history/42/
    # Calls views.chat_session_history to retrieve the message history
    # for session ID 42. The <int:session_id> is a URL parameter
    # captured from the path — Django converts it to a Python int
    # automatically and passes it to the view function as an argument.
    path('history/<int:session_id>/', views.chat_session_history, name='history'),
]
