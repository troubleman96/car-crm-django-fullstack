# Chatbot App — Live Chat Widget

## Overview

The `chatbot` app provides a **real-time chat widget** for website visitors to engage with the dealership. It uses a keyword-matching bot engine (no AI/LLM) that supports both English and Swahili. The front-end is built with **Alpine.js** and communicates with the Django backend via a JSON API. Chat conversations are stored in the database, and leads are automatically created when visitors show interest or provide a phone number.

---

## Models

### ChatSession

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `lead` | `ForeignKey('leads.Lead')` | `on_delete=SET_NULL, null=True, blank=True` | The lead linked to this session (if phone was provided) |
| `phone` | `CharField(max_length=15)` | `null=True, blank=True` | The visitor's phone number (stored directly for quick access) |
| `started_at` | `DateTimeField` | `auto_now_add=True` | When the session started |
| `ended_at` | `DateTimeField` | `null=True, blank=True` | When the session ended (nullable for open sessions) |

### ChatMessage

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `session` | `ForeignKey(ChatSession)` | `on_delete=CASCADE, related_name='messages'` | The session this message belongs to |
| `sender` | `CharField(max_length=10)` | `choices=SENDER_CHOICES` | Who sent the message |
| `message` | `TextField` | Required | The message text content |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Timestamp of the message |

**SENDER_CHOICES:** `customer`, `bot`, `agent`

**Meta:** `ordering = ['created_at']` — oldest messages first (chronological order).

---

## Bot Engine — `bot.py`

The `get_bot_reply(message)` function uses **keyword matching with regular expressions** to generate responses. It checks patterns in a specific order, and the **first match wins**.

### Keyword Matching Order

| Priority | Keywords (English) | Keywords (Swahili) | Purpose |
|----------|-------------------|---------------------|---------|
| 1 | `hi`, `hello`, `hey` | `habari`, `mambo`, `jambo` | Greetings |
| 2 | `price`, `cost`, `how much` | `bei`, `gharama` | Price inquiries |
| 3 | `toyota`, `nissan`, `bmw`, `mercedes`, `honda`, `suzuki`, `mitsubishi`, `hyundai` | — | Specific car makes |
| 4 | `test drive`, `test`, `drive`, `trial` | — | Test drive requests |
| 5 | `book`, `appointment`, `schedule`, `reserve`, `order` | — | Booking intent |
| 6 | `phone`, `call`, `contact`, `reach`, `whatsapp` | — | Contact requests |
| 7 | `location`, `showroom`, `where`, `address`, `shop` | — | Location queries |
| 8 | `thank`, `thanks` | `asante`, `sawa` | Gratitude |
| 9 | `help`, `support`, `assist` | `saida` | Help requests |
| — | (fallback) | — | Generic response |

**Important:** Order matters! A message like "Hello, I want to book a Toyota" will match the **greeting** pattern first (priority 1), not the Toyota or booking pattern.

### Swahili Support

The bot is designed for a Tanzanian audience and recognises the following Swahili words:
- **habari / mambo / jambo** — greetings
- **bei / gharama** — price/cost
- **asante** — thank you
- **sawa** — okay
- **saida** — help

---

## API Endpoints

### POST /chatbot/message/

Send a message to the chatbot and receive an automated reply.

**Request body (JSON):**
```json
{
    "message": "How much is the Toyota Hilux?",
    "phone": "0712345678",
    "session_id": null
}
```

**Response (JSON):**
```json
{
    "reply": "We have a range of cars available at different prices...",
    "session_id": 42
}
```

**Parameters:**
- `message` (string, required) — The user's text
- `phone` (string, optional) — The visitor's phone number
- `session_id` (int, optional) — Existing session ID for continuing a conversation. `null` or omitted for new conversations.

**Errors:**
- `405` — Method not allowed (use POST)
- `400` — Invalid JSON or missing message
- `404` — Session not found

### GET /chatbot/history/<session_id>/

Retrieve the full message history for a session.

**Response (JSON):**
```json
{
    "messages": [
        {"sender": "customer", "message": "Hello!", "created_at": "2025-06-15T10:00:00+03:00"},
        {"sender": "bot", "message": "Hello! Welcome...", "created_at": "2025-06-15T10:00:01+03:00"}
    ]
}
```

---

## How the Chat Widget Works

### Front-End (Alpine.js)

The widget template (`templates/chatbot/widget.html`) is a self-contained Alpine.js component included on every page via `{% include 'chatbot/widget.html' %}`.

```
Widget HTML Structure:
  ┌─────────────────────────────────┐
  │  x-data="chatWidget()"          │
  │  ┌───────────────────────────┐  │
  │  │ Chat Box (hidden by default)│  │
  │  │ ┌─ Header "Chat with us" ─┐│  │
  │  │ └─────────────────────────┘│  │
  │  │ ┌─ Messages area ─────────┐│  │
  │  │ │  x-for="msg in messages" ││  │
  │  │ └─────────────────────────┘│  │
  │  │ ┌─ Input bar ─────────────┐│  │
  │  │ │ x-model="input"         ││  │
  │  │ │ @keydown.enter="send()" ││  │
  │  │ └─────────────────────────┘│  │
  │  └───────────────────────────┘  │
  │  ┌─ Chat button (floating) ──┐  │
  │  │  @click="toggle()"         │  │
  │  └───────────────────────────┘  │
  └─────────────────────────────────┘
```

**Component State (`chatWidget()` function):**
- `open` — whether the chat window is visible (default: `false`)
- `input` — the current text in the input field (two-way bound with `x-model`)
- `sessionId` — the session identifier returned by the backend (starts as `null`)
- `phone` — pre-populated from `{{ user.phone|default:"" }}` (Django template context)
- `messages` — array of `{id, sender, message}` objects, pre-loaded with a welcome message

**Send Flow (`send()` method):**
```
1. User types message + presses Enter
2. Immediately push user message to UI (optimistic update)
3. Clear input field, scroll to bottom
4. fetch() POST to /chatbot/message/:
     Headers:
       Content-Type: application/json
       X-CSRFToken: {{ csrf_token }}
     Body:
       { message, session_id, phone }
5. Receive JSON response:
     { reply: "...", session_id: 42 }
6. Store session_id for future messages
7. Push bot reply to UI
8. Scroll to bottom
```

**CSRF Handling:** The widget sends Django's CSRF token in the `X-CSRFToken` header. However, the view is decorated with `@csrf_exempt` (since external/JS clients may not have the token). In production, add proper authentication or rate-limiting.

---

## Lead Creation from Chat

The chat view (`chatbot/views.py`) creates leads in **two scenarios**:

### Scenario A — Phone Provided
When a visitor sends a message WITH a phone number AND the session has no linked lead yet:
```
if phone and not session.lead:
    lead, created = Lead.objects.get_or_create(
        phone=phone,
        defaults={'source': 'chatbot'},
    )
    session.lead = lead
    session.save()
```

### Scenario B — Booking Intent Detected
After the bot has already replied, if the message contains booking keywords AND a phone was provided:
```
booking_keywords = ['book', 'test drive', 'appointment', 'schedule', 'phone', 'call']
if any(kw in text.lower() for kw in booking_keywords):
    if phone:
        lead, _ = Lead.objects.get_or_create(
            phone=phone,
            defaults={'source': 'chatbot'},
        )
        session.lead = lead
        session.save()
```

This captures leads who express purchase intent even if they didn't provide their phone in the first message.

---

## URLs

| URL Pattern | View Function | Name | Method | Description |
|-------------|---------------|------|--------|-------------|
| `/chatbot/message/` | `chat_message_view` | `chatbot:message` | POST | Send/receive chat messages (JSON API) |
| `/chatbot/history/<int:session_id>/` | `chat_session_history` | `chatbot:history` | GET | Retrieve chat history for a session |

---

## Admin

Registered in `chatbot/admin.py`:

### ChatSessionAdmin
- **List columns:** `id`, `phone`, `lead`, `started_at`, `ended_at`
- **Filter:** `started_at`
- **Search:** `phone`, `lead__phone`
- **Inline:** `ChatMessageInline` — shows all messages on the session edit page

### ChatMessageAdmin
- **List columns:** `session`, `sender`, `message_preview`, `created_at`
- **Filter:** `sender`
- **Search:** `message`
- **Custom column:** `message_preview` — truncates long messages to 60 characters

### ChatMessageInline
- `can_delete = False` — prevents accidental deletion of individual messages
- `readonly_fields = ['sender', 'message', 'created_at']`

---

## Dependencies

- **`leads/models.py`** — Creates `Lead` records from chat conversations. `ChatSession.lead` is a ForeignKey to `Lead`.
- **`notifications/services.py`** — Not directly used here, but leads created from chat may later receive SMS via other apps.
- **`templates/base.html`** — The widget template is included via `{% include 'chatbot/widget.html' %}` in the base template (or landing page).
