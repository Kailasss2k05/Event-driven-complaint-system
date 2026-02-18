from fastapi import FastAPI
from pydantic import BaseModel
import uuid

from .kafka_producer import send_complaint_event
from ml_service.model_loader import load_models,predict_complaint

app = FastAPI()

def startup_event():
    load_models()

# ===============================
# Request Model
# ===============================
class ComplaintRequest(BaseModel):
    description: str


# ===============================
# API Endpoint
# ===============================
@app.post("/complaint")
def create_complaint(complaint: ComplaintRequest):

    text = complaint.description

    prediction = predict_complaint(text)

    category = prediction["category"]
    priority = prediction["priority"]
    department = prediction["department"]

    event = {
        "complaint_id": str(uuid.uuid4()),
        "description": text,
        "category": category,
        "priority": priority,
        "department":department,
        "status": "RECEIVED"
    }

    send_complaint_event(event)

    return {
        "message": "Complaint received",
        "category": category,
        "priority": priority,
        "department":department
    }