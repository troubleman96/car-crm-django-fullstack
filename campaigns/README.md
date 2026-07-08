# Campaigns App — Bulk SMS Marketing

## Overview

The `campaigns` app enables the marketing team to create and send **bulk SMS campaigns** to leads. A campaign consists of a message template (with personalisation placeholders) and a list of recipients linked to leads. When triggered from the Django admin, the campaign iterates over each recipient, personalises the message (replacing `{full_name}` and `{phone}`), sends the SMS via the `notifications` service, and tracks the result for each recipient. Rate limiting (150ms delay between sends) keeps the system within the SendAfrica API limits.

---

## Models

### Campaign

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `name` | `CharField(max_length=150)` | Required | Human-readable campaign name (e.g. "March Promo") |
| `message_template` | `TextField` | Required | SMS body with `{full_name}` and `{phone}` placeholders |
| `created_by` | `ForeignKey(settings.AUTH_USER_MODEL)` | `on_delete=SET_NULL, null=True, blank=True` | The staff member who created the campaign |
| `status` | `CharField(max_length=10)` | `choices=STATUS_CHOICES, default='draft'` | One of: `draft`, `sending`, `sent` |
| `scheduled_at` | `DateTimeField` | `null=True, blank=True` | Reserved for future scheduled sending |
| `created_at` | `DateTimeField` | `auto_now_add=True` | Created timestamp |

**Status lifecycle:** `draft` → `sending` → `sent`

### CampaignRecipient

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `campaign` | `ForeignKey(Campaign)` | `on_delete=CASCADE, related_name='recipients'` | The campaign this recipient belongs to |
| `lead` | `ForeignKey('leads.Lead')` | `on_delete=SET_NULL, null=True, blank=True` | The linked lead (nullable to preserve data if lead is deleted) |
| `phone` | `CharField(max_length=15)` | Required | Phone number stored **directly** on the recipient (survives lead deletion) |
| `status` | `CharField(max_length=10)` | `choices=STATUS_CHOICES, default='pending'` | One of: `pending`, `sent`, `failed` |
| `sms_log` | `ForeignKey('notifications.SmsLog')` | `on_delete=SET_NULL, null=True, blank=True` | Link to the SmsLog record created when the SMS was sent |

**Why is `phone` stored directly on CampaignRecipient?**
So the recipient record is self-contained and survives even if the linked `Lead` is deleted. The SMS can still be sent because we have the phone number.

**Status lifecycle:** `pending` → `sent` / `failed`

---

## How to Create and Send a Campaign

### Step-by-Step Guide

```
Step 1: Create a Campaign
─────────────────────────
  In Django admin (/admin/campaigns/campaign/add/):
    1. Name:         "End of Year Sale"
    2. Template:     "Hello {full_name}! Visit our showroom
                     this weekend for special discounts on
                     all Toyota models. Call us for details."
    3. Created by:   <select a staff user>
    4. Status:       Draft (default)
    5. Click "Save"

Step 2: Add Recipients
─────────────────────────
  On the Campaign change form, scroll to "Campaign Recipients":
    1. Lead:     <select a lead from the dropdown>
    2. Phone:    <auto-filled or enter manually>
    3. Click "Save" (repeat for each recipient)

  OR create CampaignRecipient records directly from
  /admin/campaigns/campaignrecipient/add/

Step 3: Send the Campaign
─────────────────────────
  1. Go to the Campaign list view (/admin/campaigns/campaign/)
  2. Check the checkbox next to your campaign
  3. Select "Send selected campaigns now" from the action
     dropdown
  4. Click "Go"

  The admin action will:
    ├─ Check campaign is in 'draft' status
    ├─ Set status to 'sending'
    ├─ Loop over all pending recipients:
    │     ├─ Personalise template (replace {full_name}, {phone})
    │     ├─ Call send_sms() via notifications service
    │     ├─ Update recipient status (sent/failed)
    │     └─ Sleep 150ms (rate limiting)
    ├─ Set status to 'sent'
    └─ Show summary: "sent: 12, failed: 1"
```

---

## How the Admin Action Works

The `send_campaign_now` function in `campaigns/admin.py` is a **custom admin action** registered via the `@admin.action` decorator.

```
send_campaign_now(modeladmin, request, queryset)
    │
    for each campaign in queryset:
    │
    ├─ Skip if campaign.status != 'draft'
    │     → Warning message
    │
    ├─ Set campaign.status = 'sending' → save
    │
    ├─ Get pending recipients:
    │     recipients = campaign.recipients.filter(status='pending')
    │
    ├─ If no recipients:
    │     → Reset to 'draft'
    │     → Warning message
    │     → Continue (skip to next campaign)
    │
    ├─ For each recipient:
    │     ├─ Personalise message:
    │     │     full_name = lead.full_name or 'Valued Customer'
    │     │     personalized = template.format(
    │     │         full_name=full_name,
    │     │         phone=recipient.phone
    │     │     )
    │     │
    │     ├─ Send: success = send_sms(recipient.phone, personalized)
    │     │
    │     ├─ Update recipient:
    │     │     success=True  → status='sent',   sent_count++
    │     │     success=False → status='failed', fail_count++
    │     │     recipient.save()
    │     │
    │     └─ Sleep 0.15 seconds (rate limiting)
    │
    └─ Set campaign.status = 'sent' → save
    │
    └─ Message: "sent: X, failed: Y"
```

### Rate Limiting

The 150ms delay between sends limits throughput to ~400 SMS per minute, comfortably under SendAfrica's Pro plan limit of 600 requests/minute. The formula:
```
sleep_time = 1000ms / max_requests_per_second
For 600/min: 600/60 = 10/sec → 1000/10 = 100ms minimum
We use 150ms for safety margin → ~400/min
```

---

## Personalisation

The message template supports these placeholders:

| Placeholder | Source | Example Value |
|-------------|--------|---------------|
| `{full_name}` | `lead.full_name` or "Valued Customer" | "Juma Mwangi" |
| `{phone}` | `recipient.phone` | "+255712345678" |

**Example template:**
```
Hello {full_name}! Visit our showroom this weekend for special
discounts on all Toyota models. Call us for details.
```

**Rendered for a specific recipient:**
```
Hello Juma Mwangi! Visit our showroom this weekend for special
discounts on all Toyota models. Call us for details.
```

---

## URLs

The campaigns app has **no public URLs**. It is managed entirely through the Django admin interface.

---

## Admin

Registered in `campaigns/admin.py`:

### CampaignAdmin
- **List columns:** `name`, `status`, `created_by`, `scheduled_at`, `created_at`
- **Filter:** `status`
- **Search:** `name`
- **Inline:** `CampaignRecipientInline` — shows recipients on the campaign edit page
- **Action:** `send_campaign_now` — the custom admin action for sending

### CampaignRecipientAdmin
- **List columns:** `campaign`, `phone`, `status`, `lead`, `sms_log`
- **Filter:** `status`, `campaign`
- **Search:** `phone`, `campaign__name`

### CampaignRecipientInline (TabularInline)
- Shown on the Campaign edit page
- `extra = 0` — no blank rows
- `readonly_fields = ['phone', 'status', 'sms_log']`
- `can_delete = False`

---

## Dependencies

- **`notifications/services.py`** — imports `send_sms()` for sending each personalized message.
- **`notifications/models.py`** — `CampaignRecipient.sms_log` is a ForeignKey to `SmsLog`.
- **`leads/models.py`** — `CampaignRecipient.lead` is a ForeignKey to `Lead`. The lead provides `full_name` for template personalization.
- **`accounts/models.py`** — `Campaign.created_by` is a ForeignKey to `CustomUser`.
