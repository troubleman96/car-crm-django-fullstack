# AGENT.md — Build Prompt for Car CRM (Tanzania)

Paste everything below into your coding agent (Claude Code, etc.) as the
task. It already assumes `schema.md` sits next to it in the repo — the
agent should read that file first.

---

## Prompt to give the agent

```
You are building a simple Django CRM for a car dealership in Tanzania.
This is a student group project — prioritize SIMPLE and READABLE over
clever. No unnecessary abstraction, no extra packages unless listed here.

Read schema.md in this repo first. It is the source of truth for every
model and field. Translate it into Django models exactly, one app per
section of that file.

STACK
- Django (latest LTS), Django Rest Framework only if needed for the chat
  widget's AJAX calls — otherwise plain Django views + templates.
- Database: MySQL (use `mysqlclient` in requirements.txt).
- SMS: SendAfrica API (https://api.sendafrica.online). Full API docs are
  in sendafrica-docs.md — read it before writing the notifications app.
- No frontend framework required — server-rendered Django templates +
  a bit of vanilla JS for the chat widget is enough.

APPS (create each as its own Django app, matching schema.md):
1. accounts   — CustomUser, OTP model, login flows
2. vehicles   — Car, CarImage
3. leads      — Lead, Appointment
4. chatbot    — ChatSession, ChatMessage, mock AI reply
5. notifications — thin wrapper around SendAfrica, used by every other app
6. campaigns  — Campaign, CampaignRecipient

AUTH — there are two separate login flows, don't mix them:

1. CUSTOMERS (public site):
   - Enter phone number only.
   - Backend calls notifications.send_sms() to send a 6-digit code via
     SendAfrica (see sendafrica-docs.md section 3 "Send an SMS").
   - Code is stored in accounts_otp with a 5-minute expiry.
   - Customer enters the code -> if valid, get_or_create a CustomUser
     with is_customer=True and an UNUSABLE password
     (user.set_unusable_password()), then log them in with Django's
     session auth. No password field is ever shown to a customer.

2. STAFF (Admin / Marketing / Sales / Support), for /admin only:
   - Normal Django login: phone number + password.
   - Set CustomUser.USERNAME_FIELD = "phone".
   - Roles = Django Groups ("Admin", "Marketing", "Sales", "Support").
     Do NOT build a custom roles table — use the built-in auth_group.
   - Create these four groups in a data migration so classmates don't
     have to set them up by hand.

PUBLIC SITE (landing page + customer portal)
- Landing page: car listing (from vehicles.Car, status='available'),
  a chatbot widget (bottom-right, simple), and clear "Book a test drive
  / Book a call" buttons.
- Booking flow: pick a car (optional) -> pick type (test_drive /
  call_back / showroom_visit) -> enter phone -> OTP screen -> confirm.
  On confirm: create/find a Lead (source='website'), create an
  Appointment, send a confirmation SMS via notifications.send_sms().
- Chatbot widget: plain HTML/JS chat box that POSTs messages to a
  chatbot view. The "AI" is MOCKED for now — a simple keyword-matching
  function in chatbot/bot.py (e.g. if "price" in message -> canned
  reply; else -> generic fallback + "would you like to book a call?").
  Leave one clear docstring saying: "Replace this function with a real
  LLM call later — same input/output signature."
- Every inbound chat message that looks like a lead (shares a phone
  number or says something like "book me") should create a
  leads.Lead with source='chatbot'.

NOTIFICATIONS APP (keep this the ONLY place that calls SendAfrica)
- One function: notifications.services.send_sms(phone, message) -> bool
- It should: normalize the phone number (see sendafrica-docs.md section
  4 for accepted Tanzania formats), POST to /v1/sms/, log the result
  (success or failure) into notifications_smslog, and return True/False.
  Never raise — log the error and return False so the calling code
  (booking, OTP, campaigns) doesn't crash if SMS fails.
- Read the API key from an environment variable SENDAFRICA_API_KEY.
  Never hardcode it.
- Use these SMS moments to start:
  - OTP code (both customer login and staff... no, staff don't use OTP)
  - OTP code (customer login only)
  - Booking confirmation ("Your test drive for Toyota Hilux is booked
    for ...")
  - Campaign blast messages

CAMPAIGNS APP (marketing, from /admin)
- A Campaign has a name + message_template (plain text, can include
  {full_name} for basic personalization).
- Marketing staff picks a filtered list of leads (e.g. by status or
  interested car) in /admin, hits "Send Campaign" (a Django admin
  action), which creates one CampaignRecipient per lead and sends the
  SMS via notifications.send_sms(), 1 every ~150ms to respect
  SendAfrica's rate limit (see sendafrica-docs.md section 9).
- Keep this simple: no Celery/background worker required for the
  student version — sending 50-200 SMS synchronously inside the admin
  action is fine. Note in a comment that a real production version
  would use a task queue.

/admin
- Register CustomUser, Lead, Appointment, Car, Campaign,
  CampaignRecipient, ChatSession/ChatMessage (read-only) in Django admin.
- Use Django Groups + permissions so:
  - Admin group: sees everything.
  - Marketing group: sees Leads, Campaigns, CampaignRecipients.
  - Sales group: sees Leads, Appointments.
  - Support group: sees ChatSession/ChatMessage, Leads (read-only ok).
- This is the ONLY dashboard needed — do not build a separate custom
  staff dashboard, /admin is enough for this project.

BUILD ORDER (do it in this order, commit after each step)
1. Django project skeleton + settings (MySQL config from env vars).
2. accounts app: CustomUser model + migration, OTP model, four Groups
   data migration, staff login view (phone+password), customer OTP
   login views.
3. vehicles app: Car, CarImage models + admin registration + a simple
   landing page template listing available cars.
4. notifications app: send_sms() service + SmsLog model. Wire it into
   the OTP flow from step 2 so login sends real OTPs. Write one test
   that mocks the SendAfrica HTTP call.
5. leads app: Lead, Appointment models. Build the booking flow
   (car -> type -> phone -> OTP -> confirm) and confirmation SMS.
6. chatbot app: ChatSession, ChatMessage models, mock bot.py, chat
   widget template + view, and lead creation from chat.
7. campaigns app: Campaign, CampaignRecipient models + admin action
   to send a campaign.
8. Wire everything into /admin with groups/permissions from step 2.

KEEP IT SIMPLE — explicit rules
- No microservices, no Celery, no Redis, no DRF unless the chat widget
  really needs an API endpoint (a plain Django view returning JSON is
  fine).
- One app = one job. Don't let apps import each other's models directly
  in ways that create circular imports — notifications should never
  import from leads/campaigns; leads/campaigns import notifications.
- Every model field name must match schema.md exactly so classmates can
  cross-reference the SQL and the Django models side by side.
- Comment generously — this is a learning project, not a production
  system. Prefer obvious code over abstraction.
```

---

## Files to keep alongside this prompt

- `schema.md` — the DB schema (already written).
- `sendafrica-docs.md` — paste in the SendAfrica developer guide you
  already have; the agent needs it to build the `notifications` app
  correctly (auth header, phone formats, error codes, rate limits).

## One thing to decide as a team before you start

SendAfrica's `/v1/sms/` only accepts Tanzania numbers (07xx/06xx or
+255...). If any of your test data uses other-country numbers, SMS
sending will fail with `invalid_phone` — worth mentioning in your
group so nobody wastes time debugging that.
