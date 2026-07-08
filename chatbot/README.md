# Chatbot App — Live Chat Widget (Mock AI)

Provides a chat widget for the public site. Uses a mock AI bot with keyword matching — designed to be replaced with a real LLM later.

---

## Models

### ChatSession

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto |
| `lead` | FK -> Lead, nullable | Created once phone is captured |
| `phone` | VARCHAR(15), nullable | Customer's phone (if shared) |
| `started_at` | DATETIME, auto | Session start |
| `ended_at` | DATETIME, nullable | Session end |

### ChatMessage

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto |
| `session` | FK -> ChatSession (CASCADE) | Parent session |
| `sender` | ENUM('customer','bot','agent') | Who sent the message |
| `message` | TEXT | Message content |
| `created_at` | DATETIME, auto | Timestamp |

Ordered by `created_at` ascending.

---

## Mock Bot: `bot.py`

The `get_bot_reply(message: str) -> str` function uses simple keyword matching:

| Keyword | Response |
|---------|----------|
| hi, hello, hey, habari | Greeting + what we offer |
| price, cost, bei | Ask which make/model |
| toyota, nissan, bmw, etc. | Enthusiasm + suggest test drive |
| test drive, drive | Suggest booking |
| book, appointment, schedule | Offer test drive/call/visit |
| phone, call, contact | Share contact info |
| location, showroom, where | Share location info |
| thank, thanks, asante | You're welcome |
| help, support, assist | General help offer |
| Anything else | Generic "let me connect you" + suggest booking |

> **Replace this function with a real LLM call later — same input/output signature.**

---

## Chat Widget UI

**File:** `templates/chatbot/widget.html`

Included in landing and car detail pages via `{% include 'chatbot/widget.html' %}`.

Built with Alpine.js (loaded from CDN):
- Floating button (bottom-right), blue circle with chat icon
- Slide-up chat box (360x480px on desktop, full-width on mobile)
- Message history with customer/bot bubbles
- Input bar with Send button
- Enter key to send
- Auto-scroll to latest message
- CSRF token support
- Session persistence across page loads

---

## API Endpoint

### POST `/chatbot/message/`

**Request:**
```json
{
    "message": "How much is the Prado?",
    "phone": "+255712345678",
    "session_id": null
}
```

`session_id` is null for new conversations, then returned in the response.

**Response:**
```json
{
    "reply": "The Toyota Land Cruiser Prado (2022) is priced at TZS 180,000,000. Would you like to book a test drive?",
    "session_id": 1
}
```

### GET `/chatbot/history/<session_id>/`

Returns all messages for a session as JSON.

---

## Lead Creation from Chat

When a chat message contains booking keywords AND a phone number, a Lead is auto-created with `source='chatbot'`:

```python
booking_keywords = ['book', 'test drive', 'appointment', 'schedule', 'phone', 'call']
if any(kw in text.lower() for kw in booking_keywords):
    if phone:
        lead, _ = Lead.objects.get_or_create(phone=phone, defaults={'source': 'chatbot'})
```

---

## Admin

`ChatSessionAdmin`: List by ID, phone, lead, started_at. Inline ChatMessage display (read-only).

`ChatMessageAdmin`: List by session, sender, message preview. Filter by sender.

Support group has read-only access to these models.

---

## URL Endpoints

| URL | View | Methods | Auth |
|-----|------|---------|------|
| `/chatbot/message/` | `chat_message_view` | POST | None (public) |
| `/chatbot/history/<int:session_id>/` | `chat_session_history` | GET | None (public) |
