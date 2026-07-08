# schema.md — Car CRM Database Schema (MySQL)

Simple, one table per model. `InnoDB` + `utf8mb4` everywhere so Swahili text
and emoji in chat/SMS work fine. Every table has `id`, `created_at`.

Group these tables in your head by app — that's literally how the Django
apps are split (see AGENT.md).

---

## 1. accounts — who can log in

```sql
CREATE TABLE accounts_customuser (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    phone         VARCHAR(15) NOT NULL UNIQUE,   -- e.g. +255712345678
    full_name     VARCHAR(150) NULL,
    password      VARCHAR(255) NULL,             -- NULL/unusable for customers, set for staff
    is_customer   BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff      BOOLEAN NOT NULL DEFAULT FALSE, -- can log into /admin
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

Staff roles (Admin / Marketing / Sales / Support) use Django's built-in
`auth_group` + `auth_user_groups` tables — no need to build your own roles
table, that's what keeps `/admin` simple.

```sql
CREATE TABLE accounts_otp (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    phone       VARCHAR(15) NOT NULL,
    code        VARCHAR(6) NOT NULL,
    expires_at  DATETIME NOT NULL,
    is_used     BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 2. vehicles — the car inventory

```sql
CREATE TABLE vehicles_car (
    id           BIGINT AUTO_INCREMENT PRIMARY KEY,
    make         VARCHAR(50) NOT NULL,          -- e.g. Toyota
    model        VARCHAR(50) NOT NULL,          -- e.g. Hilux
    year         SMALLINT NOT NULL,
    price        DECIMAL(12,2) NOT NULL,        -- TZS
    status       ENUM('available','reserved','sold') NOT NULL DEFAULT 'available',
    description  TEXT NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE vehicles_carimage (
    id         BIGINT AUTO_INCREMENT PRIMARY KEY,
    car_id     BIGINT NOT NULL,
    image_url  VARCHAR(255) NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT FALSE,
    FOREIGN KEY (car_id) REFERENCES vehicles_car(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 3. leads — the actual CRM part

```sql
CREATE TABLE leads_lead (
    id                 BIGINT AUTO_INCREMENT PRIMARY KEY,
    customer_id        BIGINT NULL,             -- linked once they OTP-verify
    phone              VARCHAR(15) NOT NULL,
    full_name          VARCHAR(150) NULL,
    source             ENUM('website','chatbot','campaign','walk_in') NOT NULL DEFAULT 'website',
    interested_car_id  BIGINT NULL,
    status             ENUM('new','contacted','qualified','won','lost') NOT NULL DEFAULT 'new',
    assigned_to_id     BIGINT NULL,             -- staff user
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES accounts_customuser(id) ON DELETE SET NULL,
    FOREIGN KEY (interested_car_id) REFERENCES vehicles_car(id) ON DELETE SET NULL,
    FOREIGN KEY (assigned_to_id) REFERENCES accounts_customuser(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE leads_appointment (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    lead_id       BIGINT NOT NULL,
    car_id        BIGINT NULL,
    type          ENUM('test_drive','call_back','showroom_visit') NOT NULL,
    scheduled_at  DATETIME NOT NULL,
    status        ENUM('pending','confirmed','completed','cancelled') NOT NULL DEFAULT 'pending',
    notes         TEXT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lead_id) REFERENCES leads_lead(id) ON DELETE CASCADE,
    FOREIGN KEY (car_id) REFERENCES vehicles_car(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 4. chatbot — landing page chat (mock AI)

```sql
CREATE TABLE chatbot_chatsession (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    lead_id     BIGINT NULL,                -- created once phone is captured
    phone       VARCHAR(15) NULL,
    started_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at    DATETIME NULL,
    FOREIGN KEY (lead_id) REFERENCES leads_lead(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE chatbot_chatmessage (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    session_id  BIGINT NOT NULL,
    sender      ENUM('customer','bot','agent') NOT NULL,
    message     TEXT NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES chatbot_chatsession(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 5. notifications — every SMS sent (via SendAfrica)

```sql
CREATE TABLE notifications_smslog (
    id                  BIGINT AUTO_INCREMENT PRIMARY KEY,
    phone               VARCHAR(15) NOT NULL,
    message             TEXT NOT NULL,
    status              ENUM('sent','delivered','failed') NOT NULL DEFAULT 'sent',
    provider_message_id VARCHAR(64) NULL,   -- SendAfrica's message_id
    created_at          DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 6. campaigns — marketing blasts

```sql
CREATE TABLE campaigns_campaign (
    id               BIGINT AUTO_INCREMENT PRIMARY KEY,
    name             VARCHAR(150) NOT NULL,
    message_template TEXT NOT NULL,
    created_by_id    BIGINT NULL,
    status           ENUM('draft','sending','sent') NOT NULL DEFAULT 'draft',
    scheduled_at     DATETIME NULL,
    created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by_id) REFERENCES accounts_customuser(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE campaigns_campaignrecipient (
    id            BIGINT AUTO_INCREMENT PRIMARY KEY,
    campaign_id   BIGINT NOT NULL,
    lead_id       BIGINT NULL,
    phone         VARCHAR(15) NOT NULL,
    status        ENUM('pending','sent','failed') NOT NULL DEFAULT 'pending',
    sms_log_id    BIGINT NULL,
    FOREIGN KEY (campaign_id) REFERENCES campaigns_campaign(id) ON DELETE CASCADE,
    FOREIGN KEY (lead_id) REFERENCES leads_lead(id) ON DELETE SET NULL,
    FOREIGN KEY (sms_log_id) REFERENCES notifications_smslog(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## How the pieces connect (in one sentence each)

- A visitor books/chats → a `leads_lead` row is created with just a phone number.
- They verify via `accounts_otp` → get an `accounts_customuser` (`is_customer=1`, no usable password) → linked to their lead.
- A booking (test drive / call / visit) → `leads_appointment`, tied to the lead.
- Every SMS Django sends (OTP, booking confirmation, campaign) → logged in `notifications_smslog`.
- Marketing creates a `campaigns_campaign`, picks leads, one `campaigns_campaignrecipient` row per phone number, each one turns into an SMS.
- Staff (Admin/Marketing/Sales) are just `accounts_customuser` rows with `is_staff=1`, a real password, and a Django Group — that's what controls what they see in `/admin`.
