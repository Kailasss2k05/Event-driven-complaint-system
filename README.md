# Event-Driven Complaint Management System

A backend platform for municipal complaint handling where complaints are validated, translated, summarized, categorized by ML, auto-assigned to departments, and tracked through Kafka-driven events.

## What This Project Does

- Accepts complaint submissions through a FastAPI service
- Runs inline safety checks before saving
- Calls ML service for translation, summarization, category, and priority prediction
- Publishes lifecycle events to Kafka topics
- Assigns complaints to departments automatically
- Sends notification updates by email and WebSocket
- Logs all events to an audit table
- Enforces JWT auth and role-based access control

## Architecture

User -> Complaint Service -> Kafka topics -> Consumer services

Consumer services:
- Validation Service (secondary async validation)
- Assignment Service (department routing)
- Notification Service (email + websocket)
- Audit Service (event history)

Core storage and ML:
- PostgreSQL (NeonDB) for users, complaints, and events
- SentenceTransformer embeddings + scikit-learn models for category and priority

## Services

| Service | Port | Type | Responsibility |
|---|---:|---|---|
| Complaint Service | 8000 | FastAPI | Main API: submit/view/update complaints |
| ML Service | 8001 | FastAPI | Translation, summarization, category, priority prediction |
| Notification Service | 8002 | FastAPI + Kafka | Email notifications + WebSocket updates |
| Validation Service | - | Kafka Consumer | Async validation and rejection handling |
| Assignment Service | - | Kafka Consumer | Auto-assign by predicted department |
| Audit Service | - | Kafka Consumer | Writes all events to audit table |

## Kafka Topics

- complaint-submitted
- complaint-validated
- complaint-categorized
- complaint-assigned
- complaint-status-updated

## ML Stack (Current)

- Embeddings: SentenceTransformers model all-mpnet-base-v2
- Category model: LogisticRegression
- Priority model: RandomForestClassifier with class_weight="balanced"
- Priority model upgrade: changed from LogisticRegression to RandomForest after imbalance issues

Model artifacts:
- ml_model/saved_models/Category/category_model.pkl
- ml_model/saved_models/Priority/priority_model.pkl
- ml_model/saved_models/*/embedding.txt

Training scripts:
- ml_model/training/train_category_model.py
- ml_model/training/train_priority_model.py

## Validation Layers

Inline validation in Complaint Service:
- Length check: 10 to 5000 characters
- Profanity check
- Spam pattern check
- Excessive capitalization and punctuation checks
- Duplicate similarity check within recent user complaints

Async validation in Validation Service:
- Re-checks complaint content from complaint-submitted events
- Rejects invalid complaints and updates status to REJECTED
- Forwards valid complaints to complaint-validated

## Authentication and RBAC

Auth endpoints are exposed under /auth:
- POST /auth/signup
- POST /auth/token
- GET /auth/me

Roles:
- user: submit and view own complaints
- department_admin: manage complaints within department scope
- super_admin: global visibility, can assign but status updates are department_admin-only in complaint service rules

## Main API Endpoints

Complaint Service (8000):
- POST /complaint/upload-image
- POST /complaint
- GET /complaint/{complaint_id}
- GET /complaints/me
- GET /admin/complaints/department
- GET /admin/complaints/all
- PUT /admin/complaint/{complaint_id}/assign
- PUT /complaint/{complaint_id}/status

ML Service (8001):
- GET /
- POST /predict
- POST /translate
- POST /summarize

Notification Service (8002):
- GET /
- WebSocket /ws/{user_id}
- POST /send-notification
- GET /notifications/{user_id}
- PUT /notifications/{notification_id}/mark-read
- PUT /notifications/{user_id}/mark-all-read
- GET /notifications/{user_id}/unread-count
- DELETE /notifications/{notification_id}
- POST /preferences
- GET /preferences

## Complaint Lifecycle

SUBMITTED -> CATEGORIZED -> ASSIGNED -> IN_PROGRESS -> RESOLVED / CLOSED / DUMPED

Validation failures can move the complaint to REJECTED.

## Technology Stack

Backend and APIs:
- FastAPI, Uvicorn, Pydantic
- httpx, python-dotenv

Messaging:
- Apache Kafka (Confluent images)
- kafka-python
- Zookeeper

Database:
- PostgreSQL (NeonDB)
- psycopg2-binary

Security:
- python-jose (JWT)
- bcrypt and passlib

ML and NLP:
- sentence-transformers
- scikit-learn
- pandas, numpy
- deep-translator
- langdetect

Notifications and media:
- smtplib (Gmail SMTP)
- FastAPI WebSocket
- Cloudinary

## Run Locally

Prerequisites:
- Python 3.11+
- Docker Desktop
- PostgreSQL/NeonDB connection string configured in .env

1) Install dependencies

pip install -r requirements.txt

2) Start Kafka and topic initializer

docker-compose up -d zookeeper kafka kafka-init

3) Start ML service

python -m uvicorn backend.ml_service.main:app --host 0.0.0.0 --port 8001 --reload

4) Start Complaint service

python -m uvicorn backend.complaint_service.main:app --host 0.0.0.0 --port 8000 --reload

5) Start Notification service

python -m uvicorn backend.notification_service.main:app --host 0.0.0.0 --port 8002 --reload

6) Start Kafka consumers

python backend/assignment_service/kafka_consumer.py
python backend/validation_service/kafka_consumer.py
python backend/audit_service/kafka_consumer.py

API docs:
- http://localhost:8000/docs
- http://localhost:8001/docs
- http://localhost:8002/docs

## Repository Structure

- backend/
  - complaint_service/
  - ml_service/
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
