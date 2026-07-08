
import json

from django.http import JsonResponse

from django.views.decorators.csrf import csrf_exempt

from django.utils import timezone

from .models import ChatSession, ChatMessage

from .bot import get_bot_reply

from leads.models import Lead


@csrf_exempt
def chat_message_view(request):

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    text = body.get('message', '').strip()
    phone = body.get('phone', '').strip()
    session_id = body.get('session_id')

    if not text:
        return JsonResponse({'error': 'Message is required'}, status=400)

    if session_id:
        session = ChatSession.objects.filter(id=session_id).first()
        if not session:
            return JsonResponse({'error': 'Session not found'}, status=404)
    else:
        session = ChatSession.objects.create(phone=phone or None)

    if phone and not session.lead:
        lead, created = Lead.objects.get_or_create(
            phone=phone,
            defaults={'source': 'chatbot'},
        )
        session.lead = lead
        session.phone = phone
        session.save()

    ChatMessage.objects.create(session=session, sender='customer', message=text)

    bot_reply = get_bot_reply(text)

    ChatMessage.objects.create(session=session, sender='bot', message=bot_reply)

    if not session.lead:
        booking_keywords = ['book', 'test drive', 'appointment', 'schedule', 'phone', 'call']
        if any(kw in text.lower() for kw in booking_keywords):
            if phone:
                lead, _ = Lead.objects.get_or_create(
                    phone=phone,
                    defaults={'source': 'chatbot'},
                )
                session.lead = lead
                session.phone = phone
                session.save()

    return JsonResponse({
        'reply': bot_reply,
        'session_id': session.id,
    })


def chat_session_history(request, session_id):

    session = ChatSession.objects.filter(id=session_id).first()
    if not session:
        return JsonResponse({'error': 'Session not found'}, status=404)

    messages = session.messages.values('sender', 'message', 'created_at')

    return JsonResponse({'messages': list(messages)})
