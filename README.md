# Event-Driven Complaint Management System

A backend system that lets citizens submit municipal complaints (potholes, broken streetlights, water issues, etc.) which are automatically **validated, categorized by AI, assigned to the right government department, and tracked** — all through an event-driven pipeline.

---

## Architecture Overview

```
User submits complaint
        ↓
  Complaint Service (REST API)
        ↓
  Inline Validation (blocks bad content instantly)
        ↓
  Translate → Summarize → Save to DB
        ↓
  Kafka Events flow through pipeline
        ↓
  ┌─────────────────────────────────────────┐
  │  Validation Service  →  rejections      │
  │  Assignment Service  →  auto-assign     │
  │  Notification Service → emails          │
  │  Audit Service       → full log trail   │
  └─────────────────────────────────────────┘
```

---

## Services

| Service | Port | Type | Role |
|---|---|---|---|
| **Complaint Service** | 8000 | FastAPI | Main REST API — submit, view, manage complaints |
| **ML Service** | 8001 | FastAPI | AI categorization, translation, summarization |
| **Notification Service** | 8002 | FastAPI + Kafka | Email alerts via Gmail SMTP |
| **Validation Service** | — | Kafka Consumer | Async content moderation |
| **Assignment Service** | — | Kafka Consumer | Auto-routes complaints to departments |
| **Audit Service** | — | Kafka Consumer | Logs every event to DB for full trail |

---

## Kafka Pipeline (5 Topics)

```
complaint-submitted
    → Validation Service (profanity/spam/duplicate check)
    → Notification Service (email: "submission received")
    → Audit Service (log)

complaint-validated
    → Audit Service (log)

complaint-categorized
    → Assignment Service (auto-assign to department)
    → Notification Service (email: "categorized")
    → Audit Service (log)

complaint-assigned
    → Notification Service (email: "assigned to dept")
    → Audit Service (log)

complaint-status-updated
    → Notification Service (email: "status changed")
    → Audit Service (log)
```

---

## ML Capabilities

- **Translation** — detects language, translates any complaint to English before processing
- **Summarization** — generates a 1-2 sentence summary of the complaint
- **Category prediction** — classifies into: Road Issues, Water Supply, Sanitation, Health, etc.
- **Priority prediction** — assigns: Low / Medium / High
- **Auto-department routing** — maps category → responsible department

---

## Validation (Two Layers)

**Layer 1 — Inline (complaint service, before DB save):**
- Length check (10–5000 characters)
- Profanity detection (88 words, Base64-encoded in `validation_rules.json`)
- Spam pattern detection (118 patterns)
- Duplicate detection (same user, same/similar complaint within 12 hours)

**Layer 2 — Async (validation service, after Kafka event):**
- Same checks as a secondary safety net
- Can `REJECT` complaints that slipped through and update DB status

---

## Authentication & RBAC

JWT-based auth (HS256, 30-min tokens) with 3 roles:

| Role | Permissions |
|---|---|
| `user` | Submit complaints, view own complaints |
| `department_admin` | View/update status of own department's complaints, re-route to other departments |
| `super_admin` | View all complaints across all departments (read-only) |

---

## Database (NeonDB PostgreSQL)

Key tables:
- `users` — accounts with role + department
- `complaints` — full complaint record (description, translation, summary, category, priority, department, status, rejection_reason)
- `complaint_events` — full audit trail of every Kafka event

---

## Complaint Lifecycle

```
SUBMITTED → (validation passes) → CATEGORIZED → ASSIGNED → IN_PROGRESS → RESOLVED / CLOSED
                                                                        ↘ DUMPED (invalid)
         → (validation fails)  → REJECTED
```

---

## Tools & Technologies

### AI / ML

| Feature | Tool |
|---|---|
| **Translation** | Ollama (local LLM — `llama3.2` model) via HTTP API |
| **Summarization** | Ollama (same model, different prompt) |
| **Category classification** | Sentence Transformers (`all-MiniLM-L6-v2`) + scikit-learn (`SGDClassifier`) |
| **Priority classification** | Sentence Transformers (`all-MiniLM-L6-v2`) + scikit-learn (`SGDClassifier`) |
| **Model training** | pandas + scikit-learn, trained on `municipal_complaints.csv` |
| **Model storage** | joblib `.pkl` files (`category_model.pkl`, `priority_model.pkl`) |

### Backend

| Tool | Purpose |
|---|---|
| **FastAPI** | REST API framework for all 3 HTTP services |
| **uvicorn** | ASGI server to run FastAPI apps |
| **kafka-python** | Kafka producer + consumer for all services |
| **Apache Kafka** | Message broker (event bus between services) |
| **Zookeeper** | Kafka coordinator (runs alongside Kafka in Docker) |
| **Docker Compose** | Runs Kafka + Zookeeper containers |

### Database & Auth

| Tool | Purpose |
|---|---|
| **NeonDB** | Cloud-hosted PostgreSQL database |
| **psycopg2** | Python PostgreSQL driver |
| **python-jose** | JWT token generation + verification |
| **passlib + bcrypt** | Password hashing |
| **python-multipart** | OAuth2 form data parsing |

### Other

| Tool | Purpose |
|---|---|
| **python-dotenv** | Load environment variables from `.env` |
| **httpx** | Async HTTP calls from complaint service → ML service |
| **smtplib** | Email sending (Gmail SMTP) |
| **Base64** (stdlib) | Encoding profanity words in config file |
| **pydantic** | Request/response validation models |
| **Cloudinary** | Cloud image storage for complaint photo attachments |

---

## Image Upload

Users can optionally attach a photo to their complaint (e.g. a pothole photo).

**Step 1 — Upload the image:**
```
POST /complaint/upload-image
Authorization: Bearer <token>
Content-Type: multipart/form-data

**Constraints:**
- Allowed formats: JPG, PNG, WebP
- Max size: 5 MB
- Image is stored on Cloudinary and the URL is saved in the database
- Department admins can view the image when reviewing the complaint

---

## Running the System

```bash
# 1. Start Kafka + Zookeeper
docker-compose up -d zookeeper kafka

# 2. Start ML Service (wait for "Application startup complete")
python -m uvicorn backend.ml_service.main:app --host 0.0.0.0 --port 8001 --reload

# 3. Start Complaint Service
python -m uvicorn backend.complaint_service.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start Notification Service
python -m uvicorn backend.notification_service.main:app --host 0.0.0.0 --port 8002 --reload

# 5. Start Assignment Service
python backend/assignment_service/kafka_consumer.py

# 6. Start Validation Service
python backend/validation_service/kafka_consumer.py

# 7. Start Audit Service
python backend/audit_service/kafka_consumer.py
```

API docs available at: `http://localhost:8000/docs`

---

## Frontend API Reference

All requests to the Complaint Service (`http://localhost:8000`) and Notification Service (`http://localhost:8002`) must include the `Authorization: Bearer <token>` header except for `/auth/token` and `/auth/signup`.

### Base URLs
| Service | URL |
|---|---|
| Complaint Service | `http://localhost:8000` |
| Notification Service | `http://localhost:8002` |
| ML Service (internal) | `http://localhost:8001` |

---

### Authentication — `/auth`
Served by both the Complaint Service (port 8000) and Notification Service (port 8002).

#### `POST /auth/token`
Login and obtain a JWT access token.

- **Auth:** None
- **Content-Type:** `application/x-www-form-urlencoded`
- **Body fields:** `username`, `password`
- **Response:**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

#### `POST /auth/signup`
Register a new user account.

- **Auth:** None
- **Body:**
```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "role": "user",
  "department_name": null
}
```
- **Roles:** `"user"` (default), `"department_admin"`, `"super_admin"`
- **Response:** `201 Created` with user object

#### `GET /auth/me`
Get the currently logged-in user's profile.

- **Auth:** Required (any role)
- **Response:**
```json
{
  "id": 1,
  "username": "john_doe",
  "email": "john@example.com",
  "role": "user",
  "department_name": null
}
```

---

### Complaint Service — port 8000

#### `POST /complaint/upload-image`
Upload an image before submitting a complaint. Returns a URL to attach to the complaint.

- **Auth:** Required (any role)
- **Content-Type:** `multipart/form-data`
- **Body:** `file` (image file — JPG, PNG, or WebP, max 5 MB)
- **Response:**
```json
{ "image_url": "https://res.cloudinary.com/..." }
```

#### `POST /complaint`
Submit a new complaint. Triggers automatic translation (if non-English), summarization, ML categorization, and Kafka event pipeline.

- **Auth:** Required (any role)
- **Body:**
```json
{
  "description": "There is a large pothole on Main Street near the school.",
  "image_url": "https://res.cloudinary.com/..."
}
```
- `image_url` is optional — pass the URL returned from `/complaint/upload-image`
- **Response:**
```json
{
  "message": "Complaint received and categorized",
  "complaint_id": "AA001",
  "original_language": "en",
  "was_translated": false,
  "summary": "Pothole on Main Street near the school.",
  "category": "Roads and Infrastructure",
  "priority": "HIGH",
  "department": "Engineering"
}
```
- **Errors:**
  - `400` — description too short/long, profanity, spam, duplicate, excessive caps/punctuation
  - `503` — ML Service unavailable

#### `GET /complaint/{complaint_id}`
Get a single complaint by ID.

- **Auth:** Required
- **Access:** Users see only their own; `department_admin` sees complaints in their dept; `super_admin` sees all
- **Response:** Full complaint object (see DB schema below)
- **Errors:** `404` not found, `403` forbidden

#### `GET /complaints/me`
Get all complaints submitted by the currently logged-in user.

- **Auth:** Required (any role)
- **Response:** Array of complaint objects ordered by newest first

#### `GET /admin/complaints/department`
Get complaints for the admin's department.

- **Auth:** Required (`department_admin` or `super_admin`)
- `department_admin` sees only their department's complaints
- `super_admin` sees all complaints
- **Response:** Array of complaint objects

#### `GET /admin/complaints/all`
Get all complaints across all departments.

- **Auth:** Required (`super_admin` only)
- **Response:** Array of complaint objects

#### `PUT /admin/complaint/{complaint_id}/assign`
Assign a complaint to an officer, or re-route it to a different department.

- **Auth:** Required (`department_admin` or `super_admin`)
- `department_admin` can only act on complaints currently in their department
- **Body:**
```json
{
  "assigned_to": "officer_name",
  "target_department": null,
  "notes": "Assigning to field officer"
}
```
- For **re-routing**: set `target_department` to the new department name. `assigned_to` is ignored.
- For **initial assignment**: set `assigned_to`, leave `target_department` null.
- **Response (assignment):** `{ "message": "Complaint assigned successfully", "complaint_id": "AA001" }`
- **Response (re-route):** `{ "message": "Complaint re-routed from Engineering to Health", "complaint_id": "AA001", "from_department": "Engineering", "to_department": "Health" }`

#### `PUT /complaint/{complaint_id}/status`
Update the status of a complaint.

- **Auth:** Required (`department_admin` only — `super_admin` is read-only)
- `department_admin` can only update complaints in their department
- **Body:**
```json
{
  "status": "IN_PROGRESS",
  "notes": "Assigned crew to fix the pothole"
}
```
- **Valid statuses:** `IN_PROGRESS`, `RESOLVED`, `DUMPED`, `CLOSED`
- **Response:** `{ "message": "Complaint status updated successfully", "complaint_id": "AA001", "new_status": "IN_PROGRESS" }`

#### `GET /`
Health check.
- **Response:** `{ "status": "healthy", "service": "complaint_service" }`

---

### Complaint Object Schema
Fields returned by complaint endpoints:

| Field | Type | Description |
|---|---|---|
| `complaint_id` | string | e.g. `"AA001"` |
| `description` | string | Original complaint text |
| `translated_description` | string \| null | English translation (if text was non-English) |
| `summary` | string \| null | AI-generated 1–2 sentence summary |
| `original_language` | string | Detected language code e.g. `"fr"` |
| `user_id` | int | ID of the submitting user |
| `status` | string | `SUBMITTED` → `CATEGORIZED` → `ASSIGNED` → `IN_PROGRESS` → `RESOLVED` / `CLOSED` / `DUMPED` |
| `category` | string \| null | ML-predicted category e.g. `"Roads and Infrastructure"` |
| `priority` | string \| null | `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `severity` | string \| null | Additional severity rating |
| `department` | string \| null | Assigned department |
| `assigned_to` | string \| null | Name of assigned officer |
| `rejection_reason` | string \| null | Set if validation service rejects the complaint |
| `image_url` | string \| null | Cloudinary image URL |
| `created_at` | datetime | Submission timestamp |
| `updated_at` | datetime | Last update timestamp |

---

### Notification Service — port 8002

#### `WebSocket /ws/{user_id}`
Real-time notification stream for a user. Connect once after login and keep alive.

- **URL:** `ws://localhost:8002/ws/{user_id}`
- **No auth header on the WS connection itself** — identify by `user_id` in the path
- **Incoming message types:**
  - `complaint_submitted` — confirmation of new complaint
  - `complaint_categorized` — ML categorization complete
  - `complaint_assigned` — complaint assigned/re-routed
  - `complaint_rerouted` — complaint re-routed to another dept
  - `status_updated` — status changed by department admin
- **Message shape:**
```json
{
  "type": "status_updated",
  "message": "Your complaint has been resolved",
  "complaint_id": "AA001",
  "status": "RESOLVED",
  "timestamp": "2025-01-15T10:30:00"
}
```

#### `GET /notifications/{user_id}`
Get stored notifications for a user (survives page refresh, unlike WebSocket).

- **Auth:** Required
- **Access:** Users see only their own; admins see any
- **Response:**
```json
{
  "notifications": [
    {
      "id": "uuid",
      "user_id": 1,
      "type": "status_updated",
      "title": "Status: Resolved",
      "message": "Your complaint has been resolved",
      "complaint_id": "AA001",
      "timestamp": "2025-01-15T10:30:00",
      "read": false
    }
  ]
}
```

#### `PUT /notifications/{notification_id}/mark-read`
Mark a single notification as read.

- **Auth:** Required
- **Response:** `{ "message": "Notification marked as read" }`

#### `PUT /notifications/{user_id}/mark-all-read`
Mark all of a user's notifications as read.

- **Auth:** Required (own user or admin)
- **Response:** `{ "message": "Marked 5 notifications as read" }`

#### `GET /notifications/{user_id}/unread-count`
Get the count of unread notifications (use for badge indicator).

- **Auth:** Required (own user or admin)
- **Response:** `{ "unread_count": 3 }`

#### `DELETE /notifications/{notification_id}`
Delete a notification.

- **Auth:** Required (own notifications only)
- **Response:** `{ "message": "Notification deleted" }`
- **Errors:** `404` — not found or belongs to another user

#### `POST /send-notification`
Manually send an email notification (admin use only).

- **Auth:** Required (`department_admin` or `super_admin`)
- **Body:**
```json
{
  "recipient_email": "user@example.com",
  "subject": "Update on your complaint",
  "message": "Your complaint has been escalated.",
  "notification_type": "general"
}
```

#### `GET /preferences`
Get notification preferences for the logged-in user.

- **Auth:** Required
- **Response:**
```json
{
  "preferences": {
    "email_notifications": true,
    "sms_notifications": false,
    "push_notifications": true,
    "complaint_updates": true,
    "department_alerts": true
  }
}
```

#### `POST /preferences`
Update notification preferences.

- **Auth:** Required
- **Body:** Same shape as the preferences object above (all fields optional)

---

### ML Service — port 8001 (internal, but accessible)

#### `POST /predict`
Predict the category, priority, and department for a complaint.

- **Auth:** None (internal service)
- **Body:** `{ "complaint": "Pothole on Main Street" }`
- **Response:**
```json
{
  "category": "Roads and Infrastructure",
  "priority": "HIGH",
  "department": "Engineering"
}
```

#### `POST /translate`
Detect language and translate text to English.

- **Body:** `{ "text": "Il y a un nid de poule..." }`
- **Response:**
```json
{
  "translated": "There is a pothole...",
  "language": "fr",
  "was_translated": true
}
```

#### `POST /summarize`
Generate a 1–2 sentence extractive summary.

- **Body:** `{ "text": "Long complaint text...", "max_sentences": 2 }`
- **Response:**
```json
{
  "summary": "Pothole on Main Street near the school.",
  "original_length": 250,
  "summary_length": 45
}
```

---

### RBAC Summary

| Endpoint | `user` | `department_admin` | `super_admin` |
|---|---|---|---|
| `POST /complaint` | ✅ | ✅ | ✅ |
| `GET /complaints/me` | ✅ | ✅ | ✅ |
| `GET /complaint/{id}` | Own only | Own dept only | ✅ All |
| `GET /admin/complaints/department` | ❌ | Own dept | ✅ All |
| `GET /admin/complaints/all` | ❌ | ❌ | ✅ |
| `PUT /admin/complaint/{id}/assign` | ❌ | Own dept | ✅ |
| `PUT /complaint/{id}/status` | ❌ | Own dept | ❌ (read-only) |
| `POST /complaint/upload-image` | ✅ | ✅ | ✅ |

---

### Complaint Status Flow

```
SUBMITTED → CATEGORIZED → ASSIGNED → IN_PROGRESS → RESOLVED
                                                  → CLOSED
                                                  → DUMPED (could not process)
```

