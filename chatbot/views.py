"""
chatbot/views.py — JSON API views for the chatbot.

This module provides two endpoints (URLs) for the chatbot front-end:

  1. POST /chatbot/message/     — Send a message, get a bot reply.
  2. GET  /chatbot/history/<id>/ — Retrieve the full message history
                                   for a given session.

These are JSON APIs (not HTML views), meaning they return JSON responses.
The front-end chat widget (likely JavaScript) calls these endpoints.

====================================================================
               CHAT SESSION LIFECYCLE (STEP BY STEP)
====================================================================

  1. A visitor opens the chat widget on the website.
  2. They type their first message (e.g., "Hello") and click Send.
  3. The JS widget sends a POST request to /chatbot/message/ with:
       { "message": "Hello", "phone": "0712345678" }
     Note: No session_id is sent yet — this is a NEW conversation.
  4. The view:
       a. Creates a new ChatSession in the database.
       b. If the visitor provided a phone AND no lead is linked yet,
          finds or creates a Lead via get_or_create (linking chat to
          the sales pipeline).
       c. Saves the visitor's message as a ChatMessage (sender='customer').
       d. Calls get_bot_reply() to get an automated response.
       e. Saves the bot's reply as another ChatMessage (sender='bot').
       f. Checks if the message indicates "booking intent" — if so,
          creates a Lead even if one wasn't created earlier.
       g. Returns the bot's reply AND the new session_id to the front-end.
  5. The front-end stores the session_id and includes it in all
     subsequent messages, so the conversation continues in the
     same session.
  6. Future messages include session_id, so the view looks up the
     existing ChatSession instead of creating a new one.

====================================================================
                    LEAD CREATION FROM CHAT
====================================================================

Leads are created from chat in TWO different scenarios:

  Scenario A — Phone provided, no lead yet (line 36-42):
    If the visitor gives their phone number with any message, we
    immediately create a Lead (or find an existing one by phone).
    This happens regardless of the message content.

  Scenario B — Booking intent detected (line 50-60):
    Even if the visitor did NOT include a phone in the request,
    if their message contains booking-related keywords (book,
    test drive, appointment, etc.), we check if a phone was
    included. If yes, we create a Lead. This captures leads who
    signal purchase intent before explicitly giving their number.

    Note: This is checked AFTER processing the message, so the
    visitor has already received their bot reply.

====================================================================
"""

import json

# JsonResponse: A Django helper that converts a Python dict to a JSON
# HTTP response, setting the Content-Type header to application/json.
from django.http import JsonResponse

# csrf_exempt: A decorator that disables Django's CSRF (Cross-Site
# Request Forgery) protection for this view.
#
# Why disable CSRF for a JSON API? Because external clients (like a
# JavaScript chat widget on a different page) typically don't have
# access to the CSRF token. APIs accessed programmatically (not via
# browser forms) commonly use other auth methods (or no auth for
# public endpoints like a chat bot).
#
# IMPORTANT: In production, you should add rate-limiting and input
# validation to prevent abuse of an unprotected endpoint.
from django.views.decorators.csrf import csrf_exempt

# timezone utilities for working with dates/times in a timezone-aware
# manner (we use timezone.now() in bot.py).
from django.utils import timezone

# Our own models for storing chat conversations.
from .models import ChatSession, ChatMessage

# The keyword-matching bot engine (chatbot/bot.py).
from .bot import get_bot_reply

# The Lead model from the leads app — needed to create leads from chat.
from leads.models import Lead


@csrf_exempt
def chat_message_view(request):
    """
    Handle incoming chat messages (POST only).

    This is the main entry point for the chatbot. The front-end
    JavaScript sends a POST request with JSON body:
      {
        "message":    "user's text",
        "phone":      "optional phone number",
        "session_id":  optional session ID (None for new chats)
      }

    Returns JSON:
      {
        "reply":      "bot's response text",
        "session_id":  integer ID of the session (for subsequent messages)
      }
    """

    # ------------------------------------------------------------------
    # Method check: Only POST is allowed.
    #
    # If someone sends a GET, PUT, DELETE, etc., we immediately return
    # HTTP 405 Method Not Allowed. This is a simple form of
    # "method-based access control".
    # ------------------------------------------------------------------
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    # ------------------------------------------------------------------
    # Parse the JSON request body.
    #
    # request.body contains the raw bytes of the HTTP request body.
    # json.loads() converts a JSON string into a Python dictionary.
    #
    # If the body is empty, malformed, or not valid JSON, we catch
    # the json.JSONDecodeError and return HTTP 400 Bad Request.
    # ------------------------------------------------------------------
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    # --- Extract fields from the parsed JSON ---
    # .get('key', '') safely retrieves a key from the dict. If the key
    # doesn't exist, it returns the default value (empty string ''),
    # preventing a KeyError from crashing the view.
    text = body.get('message', '').strip()
    phone = body.get('phone', '').strip()
    session_id = body.get('session_id')  # This could be None (new chat)

    # --- Validate: message text is required ---
    if not text:
        return JsonResponse({'error': 'Message is required'}, status=400)

    # ------------------------------------------------------------------
    # Session resolution: find existing OR create new.
    #
    # If the client sent a session_id, we try to find that session in
    # the database. If it doesn't exist, we return 404.
    #
    # If NO session_id is sent, this is a new conversation, so we
    # CREATE a fresh ChatSession right away.
    # ------------------------------------------------------------------
    if session_id:
        # .filter(id=session_id).first() is used instead of
        # .get(id=session_id) because .get() raises an exception if
        # not found, whereas .first() returns None. This avoids a
        # try/except block.
        session = ChatSession.objects.filter(id=session_id).first()
        if not session:
            return JsonResponse({'error': 'Session not found'}, status=404)
    else:
        # Create a new session. phone might be '' or None — if it's
        # an empty string, we store None instead (phone or None).
        session = ChatSession.objects.create(phone=phone or None)

    # ------------------------------------------------------------------
    # LEAD CREATION — Scenario A: phone provided, no lead linked yet.
    #
    # If the visitor gave a phone number AND this session doesn't
    # already have a linked Lead, we try to find or create a Lead
    # using get_or_create. The 'source' is set to 'chatbot' so the
    # sales team knows where this lead came from.
    #
    # get_or_create returns (lead, was_created_bool). We store the
    # lead on the session and save the session to persist the link.
    # ------------------------------------------------------------------
    if phone and not session.lead:
        lead, created = Lead.objects.get_or_create(
            phone=phone,
            defaults={'source': 'chatbot'},
        )
        session.lead = lead
        session.phone = phone
        session.save()

    # ------------------------------------------------------------------
    # Store the visitor's message in the database.
    #
    # Every message is saved as a ChatMessage with sender='customer'.
    # This builds up a conversation history that can be reviewed
    # later in the admin panel.
    # ------------------------------------------------------------------
    ChatMessage.objects.create(session=session, sender='customer', message=text)

    # --- Get the bot's reply ---
    # This calls the keyword-matching engine in chatbot/bot.py.
    bot_reply = get_bot_reply(text)

    # --- Store the bot's reply in the database too ---
    # Saving both the user message and the bot reply ensures the
    # conversation history is complete.
    ChatMessage.objects.create(session=session, sender='bot', message=bot_reply)

    # ------------------------------------------------------------------
    # LEAD CREATION — Scenario B: Booking intent detected.
    #
    # This runs AFTER the bot has already replied, so the visitor
    # gets their answer immediately. We then check if the message
    # suggests the visitor wants to buy/order.
    #
    # The keyword list is intentionally broad to catch as many
    # booking intents as possible. If any keyword is found AND
    # the visitor provided a phone, we create a Lead.
    #
    # Why two separate lead-creation points?
    #   - Scenario A catches the case where the visitor gives their
    #     phone freely (e.g., "My number is 0712...").
    #   - Scenario B catches the case where the visitor says "I want
    #     to book" but haven't yet given their number — the bot reply
    #     asks for it, and if the phone was actually included in this
    #     same message, we still capture the lead.
    # ------------------------------------------------------------------
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

    # --- Return the bot reply and session_id to the front-end ---
    # The front-end JS receives this JSON, displays the bot reply
    # in the chat widget, and stores the session_id for future
    # messages in this conversation.
    return JsonResponse({
        'reply': bot_reply,
        'session_id': session.id,
    })


def chat_session_history(request, session_id):
    """
    Retrieve the full message history for a given chat session.

    This is useful for:
      - Displaying past conversations in the admin panel.
      - Letting the front-end reload the conversation if the
        user refreshes the page.
      - Allowing human agents to review chat history before
        taking over a conversation.

    Args:
        session_id: The ID from the URL (captured as <int:session_id>
                    in chatbot/urls.py).

    Returns:
        JSON with a "messages" list. Each message has:
          - sender:     "customer", "bot", or "agent"
          - message:    The text content
          - created_at: ISO-formatted timestamp
    """

    # Look up the session by ID. .filter().first() avoids exceptions
    # if the session doesn't exist.
    session = ChatSession.objects.filter(id=session_id).first()
    if not session:
        return JsonResponse({'error': 'Session not found'}, status=404)

    # ------------------------------------------------------------------
    # Query all messages for this session.
    #
    # session.messages is the reverse relation defined by
    # related_name='messages' on ChatMessage.session.
    # Django automatically creates this manager so we can do:
    #   session.messages.all()  — all messages
    #   session.messages.filter(sender='customer')  — only customer msgs
    #
    # .values('sender', 'message', 'created_at') returns a QuerySet
    # of dicts instead of model instances. This is more efficient
    # because we don't need the full model objects — just the data
    # to serialise into JSON.
    #
    # .values() respects the model's Meta.ordering, so messages
    # come back in chronological order (oldest first).
    # ------------------------------------------------------------------
    messages = session.messages.values('sender', 'message', 'created_at')

    # Convert the QuerySet to a list so it can be serialised as JSON.
    # JsonResponse expects a list, but a QuerySet is lazy — converting
    # to a list forces the database query to execute now.
    return JsonResponse({'messages': list(messages)})
