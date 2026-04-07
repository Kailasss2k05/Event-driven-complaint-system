<div align="center">

# Event-Driven Complaint Management System

**A full-stack, event-driven municipal complaint handling platform with ML-powered routing and real-time notifications**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.x-61DAFB?logo=react)](https://react.dev)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-7.5-231F20?logo=apachekafka)](https://kafka.apache.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-NeonDB-336791?logo=postgresql)](https://neon.tech)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)](https://www.docker.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org)

</div>

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Components](#components)
   - [Complaint Service](#1-complaint-service)
   - [ML Service](#2-ml-service)
   - [Notification Service](#3-notification-service)
   - [Kafka Consumer Services](#4-kafka-consumer-services)
   - [Frontend (React)](#5-frontend-react)
4. [Key Features](#key-features)
5. [Tech Stack](#tech-stack)
6. [Complaint Lifecycle](#complaint-lifecycle)
7. [Kafka Topics](#kafka-topics)
8. [API Reference](#api-reference)
9. [Project Structure](#project-structure)
10. [Getting Started](#getting-started)
    - [Option A — Docker (Recommended)](#option-a--docker-recommended)
    - [Option B — Manual Setup](#option-b--manual-setup)
11. [Environment Variables](#environment-variables)

---

## Overview

The **Event-Driven Complaint Management System** is a backend platform for municipal complaint handling that combines a Kafka-driven microservices architecture with an ML-powered classification pipeline and a React-based frontend.

- Citizens submit complaints through a FastAPI service that performs **inline safety validation** before persisting anything.
- Complaints are processed asynchronously via **Kafka topics**, flowing through validation, ML classification, department assignment, notification dispatch, and audit logging — all as independent services.
- An **ML service** built on SentenceTransformers and scikit-learn automatically **translates**, **summarises**, **categorises**, and **prioritises** every complaint.
- Administrators manage complaint routing and status updates through role-based access controls, while citizens receive **real-time WebSocket notifications** and email updates as their complaint progresses.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                Event-Driven Complaint Platform                   │
│                                                                  │
│  ┌─────────────────┐              ┌──────────────────────────┐   │
│  │  React Frontend │              │    Complaint Service     │   │
│  │  (Vite + TW)    │◄────REST────►│    FastAPI  :8000        │   │
│  └─────────────────┘              └─────────────┬────────────┘   │
│                                                 │ Kafka          │
│                                       ┌─────────▼──────────┐    │
│                                       │   Apache Kafka     │    │
│                                       │   + Zookeeper      │    │
│                                       └──┬──┬──┬──┬────────┘    │
│                                          │  │  │  │             │
│             ┌────────────────────────────┘  │  │  └──────────┐  │
│             ▼                               │  │             ▼  │
│  ┌──────────────────┐               ┌───────▼──▼────┐  ┌──────────────────┐  │
│  │ Validation Svc   │               │ Assignment /  │  │  Audit Service   │  │
│  │ (Kafka Consumer) │               │ Notification  │  │ (Kafka Consumer) │  │
│  └──────────────────┘               │   Services    │  └──────────────────┘  │
│                                     └───────────────┘                        │
│                                                                  │
│              ┌────────────────────────────────────┐              │
│              │          ML Service  :8001          │              │
│              │  Translate · Summarise · Classify   │              │
│              └────────────────────────────────────┘              │
│              ┌────────────────────────────────────┐              │
│              │       Notification Service :8002    │              │
│              │       SMTP Email · WebSocket        │              │
│              └────────────────────────────────────┘              │
└──────────────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Complaint Service

The primary API gateway for the entire platform. All citizen-facing complaint operations flow through this service.

- **Inline Validation** — Before persistence, every submission is checked for profanity, spam patterns, excessive casing, excessive punctuation, and deduplication against recent user complaints.
- **ML Integration** — Calls the ML service synchronously to translate, summarise, categorise, and assign priority to complaint text before storing it.
- **Image Upload** — Cloudinary-backed image attachment support for complaint submissions.
- **RBAC** — Three-tier role system: `user`, `department_admin`, and `super_admin`, each with scoped endpoint access.
- **Kafka Publishing** — Emits lifecycle events to Kafka topics at every stage of the complaint pipeline.

### 2. ML Service

A standalone FastAPI service dedicated to natural language processing of complaint text.

- **Translation** — Detects language using `langdetect` and translates non-English text to English via `deep-translator`.
- **Extractive Summarisation** — Uses SentenceTransformer embeddings to select the most representative sentences from long descriptions.
- **Category Prediction** — Logistic Regression classifier trained on municipal complaint datasets, using `all-mpnet-base-v2` embeddings.
- **Priority Prediction** — Random Forest classifier with `class_weight="balanced"` to correct for class imbalance, outputting `Low`, `Normal`, `High`, or `Critical`.
- **Background Loading** — Models load in a background thread so the service starts immediately without blocking the API.

### 3. Notification Service

Handles all outbound communication with citizens and staff.

- **Email Notifications** — Gmail SMTP integration to send templated email updates at each complaint status change.
- **WebSocket Push** — Real-time in-browser notifications via persistent WebSocket connections keyed to `user_id`.
- **Notification Store** — In-memory store for unread/read notification state with per-user preferences.
- **Kafka Consumer** — Consumes all complaint lifecycle topics and triggers the appropriate email and WebSocket events.

### 4. Kafka Consumer Services

Three lightweight consumer processes that react to Kafka events asynchronously:

| Service | Listens To | Action |
|---|---|---|
| `validation-service` | `complaint-submitted` | Re-validates complaint content; rejects invalid submissions |
| `assignment-service` | `complaint-categorized` | Routes complaint to appropriate department; publishes `complaint-assigned` |
| `audit-service` | All topics | Writes every event to the audit log table in PostgreSQL |

### 5. Frontend (React)

A React 19 single-page application for citizens, department staff, and super admins.

- **Citizen Portal** — Submit complaints with image upload, track status, and receive real-time WebSocket notifications.
- **Staff Dashboard** — Department-scoped complaint management with status update controls.
- **Admin Dashboard** — Global complaint visibility, manual department assignment, and analytics.
- **Auth Flows** — JWT-based login and signup with persistent state via Zustand.
- **Real-Time Notifications** — WebSocket-backed notification panel with unread count and mark-read controls.

---

## Key Features

| Feature | Frontend | Backend | ML | Kafka |
|---|:---:|:---:|:---:|:---:|
| Citizen complaint submission | ✓ | ✓ | | |
| Inline safety validation | | ✓ | | |
| Language detection & translation | | | ✓ | |
| Extractive summarisation | | | ✓ | |
| Auto category prediction | | | ✓ | |
| Auto priority prediction | | | ✓ | |
| Image upload (Cloudinary) | ✓ | ✓ | | |
| Async validation pipeline | | | | ✓ |
| Auto department assignment | | | | ✓ |
| Email notifications | | ✓ | | ✓ |
| WebSocket real-time updates | ✓ | ✓ | | |
| Full audit event log | | ✓ | | ✓ |
| JWT + RBAC auth | ✓ | ✓ | | |
| Docker containerisation | ✓ | ✓ | ✓ | ✓ |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, Vite, Tailwind CSS 4, Zustand, Recharts, Framer Motion |
| API Services | Python 3.11, FastAPI, Uvicorn, Pydantic, httpx |
| Messaging | Apache Kafka 7.5, Zookeeper, kafka-python |
| Database | PostgreSQL (NeonDB), psycopg2-binary |
| ML / NLP | SentenceTransformers, scikit-learn, deep-translator, langdetect |
| Auth | python-jose (JWT), passlib, bcrypt |
| Media | Cloudinary |
| Email | Gmail SMTP (smtplib) |
| Containerisation | Docker, Docker Compose |

---

## Complaint Lifecycle

```
SUBMITTED ──► VALIDATED ──► CATEGORIZED ──► ASSIGNED ──► IN_PROGRESS ──► RESOLVED
                  │                                                          │
               REJECTED                                                   CLOSED
                                                                            │
                                                                          DUMPED
```

Each transition emits a Kafka event that triggers downstream services in parallel.

---

## Kafka Topics

| Topic | Publisher | Consumers |
|---|---|---|
| `complaint-submitted` | Complaint Service | Validation Service, Audit Service, Notification Service |
| `complaint-validated` | Validation Service | Audit Service, Notification Service |
| `complaint-categorized` | Complaint Service | Assignment Service, Audit Service, Notification Service |
| `complaint-assigned` | Assignment Service | Audit Service, Notification Service |
| `complaint-status-updated` | Complaint Service | Audit Service, Notification Service |

---

## API Reference

### Complaint Service — `localhost:8000`

| Method | Endpoint | Role | Description |
|---|---|---|---|
| `POST` | `/auth/signup` | Public | Register a new user |
| `POST` | `/auth/token` | Public | Obtain JWT access token |
| `GET` | `/auth/me` | Authenticated | Get current user info |
| `POST` | `/complaint/upload-image` | `user` | Upload complaint attachment |
| `POST` | `/complaint` | `user` | Submit a new complaint |
| `GET` | `/complaint/{id}` | Authenticated | Get complaint by ID |
| `GET` | `/complaints/me` | `user` | Get own complaints |
| `GET` | `/admin/complaints/department` | `department_admin` | Department-scoped complaints |
| `GET` | `/admin/complaints/all` | `super_admin` | All complaints |
| `PUT` | `/admin/complaint/{id}/assign` | `super_admin` | Manually assign complaint |
| `PUT` | `/complaint/{id}/status` | `department_admin` | Update complaint status |

### ML Service — `localhost:8001`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health / model readiness check |
| `POST` | `/predict` | Category + priority prediction |
| `POST` | `/translate` | Language detection + translation |
| `POST` | `/summarize` | Extractive summarisation |

### Notification Service — `localhost:8002`

| Method | Endpoint | Description |
|---|---|---|
| `WS` | `/ws/{user_id}` | Real-time WebSocket connection |
| `GET` | `/notifications/{user_id}` | Get user notifications |
| `PUT` | `/notifications/{id}/mark-read` | Mark single notification read |
| `PUT` | `/notifications/{user_id}/mark-all-read` | Mark all as read |
| `GET` | `/notifications/{user_id}/unread-count` | Get unread count |
| `DELETE` | `/notifications/{id}` | Delete a notification |
| `POST` | `/preferences` | Set notification preferences |

---

## Project Structure

```
Event-driven-complaint-system/
│
├── backend/
│   ├── complaint_service/       # Main API — submit, view, update complaints
│   ├── ml_service/              # Translation, summarisation, classification
│   ├── notification_service/    # Email + WebSocket notifications
│   ├── validation_service/      # Async content validation (Kafka consumer)
│   ├── assignment_service/      # Department routing (Kafka consumer)
│   ├── audit_service/           # Event audit log (Kafka consumer)
│   ├── auth/                    # JWT handler, OAuth2, router, schemas
│   └── db/                      # Database connection, schema, seed scripts
│
├── frontend/
│   └── src/
│       ├── admin/               # Admin dashboard
│       ├── citizen/             # Complaint submission and tracking
│       ├── staff/               # Staff complaint management
│       ├── auth/                # Login and signup
│       ├── components/          # Shared UI components
│       ├── hooks/               # Zustand store and WebSocket hooks
│       ├── api/                 # Axios API client
│       └── layout/              # Navbar, main layout
│
├── ml_model/
│   ├── dataset/                 # Training datasets
│   ├── saved_models/            # category_model.pkl, priority_model.pkl
│   └── training/                # Model training scripts
│
├── kafka/
│   └── create-topics.sh         # Topic initialisation script
│
├── Dockerfile                   # Shared Python container image
├── docker-compose.yml           # Full stack orchestration
└── .env.example                 # Environment variable template
```

---

## Getting Started

### Option A — Docker (Recommended)

Runs the entire backend stack in containers with a single command.

**Prerequisites:** Docker Desktop

```bash
# 1. Clone the repository
git clone https://github.com/Kailasss2k05/Event-driven-complaint-system.git
cd Event-driven-complaint-system

# 2. Set up environment variables
copy .env.example .env
# Edit .env and fill in all required values

# 3. Start the full stack
docker compose up --build -d

# 4. Watch logs
docker compose logs -f

# 5. Stop all services
docker compose down
```

Once running:
- Complaint API: `http://localhost:8000/docs`
- ML API: `http://localhost:8001/docs`
- Notification API: `http://localhost:8002/docs`

### Option B — Manual Setup

**Prerequisites:** Python 3.11+, Docker Desktop (for Kafka), Node.js 18+

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Start Kafka and Zookeeper
docker compose up -d zookeeper kafka kafka-init

# 3. Start backend services (separate terminals)
python -m uvicorn backend.complaint_service.main:app --host 0.0.0.0 --port 8000 --reload
python -m uvicorn backend.ml_service.main:app --host 0.0.0.0 --port 8001 --reload
python -m uvicorn backend.notification_service.main:app --host 0.0.0.0 --port 8002 --reload

# 4. Start Kafka consumers (separate terminals)
python backend/validation_service/kafka_consumer.py
python backend/assignment_service/kafka_consumer.py
python backend/audit_service/kafka_consumer.py

# 5. Start frontend
cd frontend
npm install
npm run dev
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the following:

```env
# Kafka
KAFKA_BROKER=kafka:9092          # Use localhost:9092 for manual setup

# Kafka Topics
TOPIC_COMPLAINT_SUBMITTED=complaint-submitted
TOPIC_COMPLAINT_VALIDATED=complaint-validated
TOPIC_COMPLAINT_CATEGORIZED=complaint-categorized
TOPIC_COMPLAINT_ASSIGNED=complaint-assigned
TOPIC_COMPLAINT_STATUS_UPDATED=complaint-status-updated

# Service URLs
ML_SERVICE_URL=http://ml-service:8001   # Use http://localhost:8001 for manual setup

# Database (NeonDB / PostgreSQL)
DATABASE_URL=postgresql://user:pass@host/dbname?sslmode=require

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ML
MODEL_DEVICE=cpu

# Email (Gmail SMTP)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password
SENDER_NAME=Municipal Complaint System

# Cloudinary
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
```

---

<div align="center">

Built for smarter and more transparent municipal governance.

</div>

  - auth/
  - db/
  - assignment_service/
  - audit_service/
  - notification_service/
  - validation_service/
- kafka/
- ml_model/
  - dataset/
  - training/
  - saved_models/
- docker-compose.yml
- requirements.txt

## Notes

- The weekly report file was not present in the workspace during this update.
- README was updated by reading actual implementation files and matching documentation to current code behavior.
