# Campaigns App — Marketing SMS Blasts

Allows marketing staff to send bulk SMS campaigns to leads from the Django admin panel.

---

## Models

### Campaign

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto |
| `name` | VARCHAR(150) | Campaign name (e.g. "End of Year Sale") |
| `message_template` | TEXT | SMS template with `{full_name}` and `{phone}` placeholders |
| `created_by` | FK -> CustomUser (staff), nullable | Who created it |
| `status` | ENUM('draft','sending','sent') | Campaign state |
| `scheduled_at` | DATETIME, nullable | When to send (future use) |
| `created_at` | DATETIME, auto | Created |

### CampaignRecipient

| Field | Type | Description |
|-------|------|-------------|
| `id` | BIGINT, PK | Auto |
| `campaign` | FK -> Campaign (CASCADE) | Parent campaign |
| `lead` | FK -> Lead, nullable | The lead this recipient came from |
| `phone` | VARCHAR(15) | Phone number to send to |
| `status` | ENUM('pending','sent','failed') | Delivery state |
| `sms_log` | FK -> SmsLog, nullable | Reference to the sent SMS log |

---

## Admin Action: Send Campaign

**File:** `campaigns/admin.py`

The `send_campaign_now` admin action sends SMS to all pending recipients:

```
1. Admin selects campaign(s) in list view
2. Chooses "Send selected campaigns now" action
3. For each campaign:
   a. Sets status to 'sending'
   b. Iterates pending recipients
   c. Personalizes template with {full_name} and {phone}
   d. Calls send_sms() for each recipient
   e. Updates recipient status (sent/failed)
   f. Waits 150ms between sends (rate limit safety)
   g. Sets campaign status to 'sent'
4. Reports: "{name}: 45 sent, 2 failed"
```

### Performance Notes

- Runs synchronously in the admin HTTP request
- Suitable for 50-200 recipients (typical for student project)
- 150ms delay = ~400 SMS/minute, under SendAfrica's 600/min Pro limit
- **Production upgrade:** Replace with Celery task queue

---

## Personalization

The `message_template` supports two placeholders:

```
Hello {full_name}! Visit our showroom this weekend for special discounts
on all Toyota models. Call us for details.
```

| Placeholder | Replaced With |
|-------------|---------------|
| `{full_name}` | Lead's full_name, or "Valued Customer" if null |
| `{phone}` | Recipient's phone number |

---

## Creating a Campaign

1. Go to /admin/campaigns/campaign/
2. Click "Add Campaign"
3. Enter name (e.g. "End of Year Sale")
4. Write message template with {full_name}
5. Click "Save"
6. From the campaign detail page, add recipients via the inline form
7. Or go to Campaign Recipients and add them individually
8. Select the campaign in list view → Actions → "Send selected campaigns now"

---

## Admin

- `CampaignAdmin` with inline `CampaignRecipient`, plus "Send selected campaigns now" action
- `CampaignRecipientAdmin` — list by campaign, phone, status

Marketing group has full CRUD access to campaigns.
