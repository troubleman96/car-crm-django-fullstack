# Chatbot Templates

Location: `templates/chatbot/`

A single partial template that implements a floating AI chat widget using
Alpine.js. It is **not a standalone page** — it is included by other templates.

---

## Files

### `widget.html`
**Included by**: `landing.html`, `car_detail.html`, `book.html`
**Purpose**: Floating chat bubble + chat window that lets users ask questions
and get AI-powered responses.

**Context variables**:
| Variable | Description                                        |
|----------|----------------------------------------------------|
| `user.phone` | Pre-populated in the chat input for logged-in users |

**Architecture**:

```
widget.html
├── Alpine.js component (x-data="chatWidget()")
│   ├── Chat window (toggled via open/closed state)
│   │   ├── Header: "Chat with us" + close button
│   │   ├── Messages area: x-for loop over messages[]
│   │   └── Input bar: text input + send button
│   └── Floating button: chat bubble icon (Heroicons)
└── <script> function chatWidget() { ... } </script>
    ├── State: open, input, sessionId, phone, messages[]
    ├── toggle() — open/close with scroll-to-bottom
    ├── send() — fetch POST to /chatbot/message/
    ├── scrollDown() — auto-scroll to latest message
    └── init() — pre-fill phone from Django user
```

**Chat flow**:
1. User clicks the floating bubble → chat window opens
2. User types a message and presses Enter or clicks Send
3. JavaScript `send()` method:
   - Appends user message to UI immediately (optimistic update)
   - `fetch()` POSTs JSON to `/chatbot/message/`
   - Backend returns `{ "reply": "...", "session_id": "..." }`
   - Appends bot reply to UI
4. Session ID is stored client-side and sent with every message for
   conversation continuity

**API contract**:
```
POST /chatbot/message/
Headers: { Content-Type: application/json, X-CSRFToken: <token> }
Body: { "message": "...", "session_id": null|"abc", "phone": "+255..." }
Response: { "reply": "...", "session_id": "abc" }
```

**Key template features**:
- `x-data="chatWidget()"` — Alpine.js component initialization
- `x-init="init()"` — lifecycle hook to pre-fill phone
- `x-model="input"` — two-way data binding on input field
- `x-for="msg in messages"` — loops over conversation history
- `:class="{'open': open}"` — conditional class binding
- `@click`, `@keydown.enter` — event handlers
- `{{ csrf_token }}` — injected into JavaScript for fetch() auth
- `{{ user.phone|default:"" }}` — safe rendering of user phone

---

## Design Notes

- Fixed position bottom-right (`position: fixed; bottom: 24px; right: 24px`)
- Responsive: on mobile (<480px), chat box width adjusts to `calc(100vw - 48px)`
- Blue-themed: header and button use `bg-blue-600`, messages use blue/grey
- Smooth shadow: `box-shadow: 0 4px 20px rgba(0,0,0,0.15)`
- Alpine.js loaded from CDN with `defer` attribute

---

## Related

- [Root templates README](../README.md)
- [chatbot app README](../../chatbot/README.md) — for view logic and models
