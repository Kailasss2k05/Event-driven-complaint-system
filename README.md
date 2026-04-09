<div align="center">

# 🚀 Event-Driven Complaint Management System

### ⚡ A full-stack, event-driven municipal complaint handling platform with ML-powered routing and real-time notifications

<img src="https://skillicons.dev/icons?i=python,fastapi,react,kafka,postgres,docker" />

<br/>

![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19.x-61DAFB?logo=react&logoColor=black)
![Kafka](https://img.shields.io/badge/Apache%20Kafka-7.5-231F20?logo=apachekafka&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-NeonDB-336791?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

</div>

---

## 📑 Table of Contents
1. 📌 Overview  
2. 🏗️ System Architecture  
3. 🧩 Components  
4. ✨ Key Features  
5. 🧰 Tech Stack  
6. 🔄 Complaint Lifecycle  
7. 📡 Kafka Topics  
8. 🔗 API Reference  
9. 📁 Project Structure  
10. 🚀 Getting Started  
11. ⚙️ Environment Variables  

---

## 📌 Overview

The **Event-Driven Complaint Management System** is a backend platform for municipal complaint handling that combines a Kafka-driven microservices architecture with an ML-powered classification pipeline and a React-based frontend.

- 🚀 Citizens submit complaints via FastAPI  
- 🔄 Processed asynchronously using Kafka  
- 🤖 ML handles classification & priority  
- 📡 Real-time updates via WebSockets & Email  

---

## 🏗️ System Architecture

<p align="center">
  <img src="diagram.png" width="600"/>
</p>

---

## 🧩 Components

### 🔹 1. Complaint Service
- ✅ Inline Validation  
- 🤖 ML Integration  
- 🖼️ Image Upload (Cloudinary)  
- 🔐 RBAC System  
- 📡 Kafka Event Publishing  

---

### 🔹 2. ML Service
- 🌐 Translation (langdetect + deep-translator)  
- 🧠 Summarisation (SentenceTransformers)  
- 📊 Category Prediction (Logistic Regression)  
- ⚡ Priority Prediction (Random Forest)  

---

### 🔹 3. Notification Service
- 📧 Email Notifications  
- 📡 WebSocket Real-Time Updates  
- 🗂️ Notification Store  
- 🔄 Kafka Consumer  

---

### 🔹 4. Kafka Consumer Services

| ⚙️ Service | 📡 Listens To | 🎯 Action |
|---|---|---|
| validation-service | complaint-submitted | Re-validates complaint |
| assignment-service | complaint-categorized | Routes complaint |
| audit-service | All topics | Logs events |

---

### 🔹 5. Frontend (React)
- 👤 Citizen Portal  
- 🧑‍💼 Staff Dashboard  
- 🛠️ Admin Dashboard  
- 🔐 JWT Authentication  
- 🔔 Real-Time Notifications  

---

## ✨ Key Features

| 🚀 Feature | 🌐 Frontend | ⚙️ Backend | 🧠 ML | 📡 Kafka |
|---|:---:|:---:|:---:|:---:|
| Complaint submission | ✓ | ✓ | | |
| Validation | | ✓ | | |
| Translation | | | ✓ | |
| Classification | | | ✓ | |
| Notifications | ✓ | ✓ | | ✓ |
| Audit logs | | ✓ | | ✓ |

---

## 🧰 Tech Stack

<p align="center">
<img src="https://skillicons.dev/icons?i=python,java,c,fastapi,flask,kafka,postgres,mysql,docker,pytorch" />
</p>

### 💻 Languages  
![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Java](https://img.shields.io/badge/Java-ED8B00?logo=openjdk&logoColor=white)
![C](https://img.shields.io/badge/C-00599C?logo=c&logoColor=white)

### ⚙️ Backend  
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)

### 📡 Messaging  
![Kafka](https://img.shields.io/badge/Kafka-231F20?logo=apachekafka&logoColor=white)

### 🧠 Machine Learning  
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E?logo=scikitlearn&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)

### 🗄️ Database  
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-336791?logo=postgresql&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-4479A1?logo=mysql&logoColor=white)

### 🐳 DevOps  
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)

---

## 🔄 Complaint Lifecycle

```
SUBMITTED ──► VALIDATED ──► CATEGORIZED ──► ASSIGNED ──► IN_PROGRESS ──► RESOLVED
                  │                                                          │
               REJECTED                                                   CLOSED
                                                                            │
                                                                          DUMPED
```

Each transition emits a Kafka event that triggers downstream services in parallel.

---


---

## 📡 Kafka Topics

| 🧵 Topic | 📤 Publisher | 📥 Consumers |
|---|---|---|
| complaint-submitted | Complaint Service | Validation, Audit, Notification |
| complaint-validated | Validation Service | Audit, Notification |
| complaint-categorized | Complaint Service | Assignment, Audit |
| complaint-assigned | Assignment Service | Audit, Notification |

---

## 🔗 API Reference


### ⚙️ Complaint Service — `localhost:8000`

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

### 🤖 ML Service — `localhost:8001`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health / model readiness check |
| `POST` | `/predict` | Category + priority prediction |
| `POST` | `/translate` | Language detection + translation |
| `POST` | `/summarize` | Extractive summarisation |

### 🔔 Notification Service — `localhost:8002`

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


---

## 🚀 Getting Started

### 🐳 Option A — Docker


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


---

### ⚙️ Option B — Manual Setup

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


---

## ⚙️ Environment Variables

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


---

<div align="center">

✨ Built for smarter and more transparent municipal governance ✨

</div>


