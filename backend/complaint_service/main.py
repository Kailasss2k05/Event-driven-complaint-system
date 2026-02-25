import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid

from .kafka_producer import send_complaint_submitted, send_complaint_categorized
from backend.db.database import (
    insert_complaint,
    update_complaint_categorized,
    insert_event,
    get_complaint,
    get_all_complaints
)

load_dotenv()

app = FastAPI(title="Complaint Service", version="1.0.0")

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL")


# ===============================
# Request Model
# ===============================
class ComplaintRequest(BaseModel):
    description: str


# ===============================
# Submit Complaint
# ===============================
@app.post("/complaint")
def create_complaint(complaint: ComplaintRequest):

    text = complaint.description
    complaint_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()

    # Step 1: Save to database
    try:
        insert_complaint(complaint_id, text, status="SUBMITTED")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save complaint: {str(e)}"
        )

    # Step 2: Publish to complaint-submitted
    submitted_event = {
        "complaint_id": complaint_id,
        "description": text,
        "status": "SUBMITTED",
        "timestamp": timestamp
    }

    try:
        send_complaint_submitted(submitted_event)
        insert_event(complaint_id, "complaint-submitted", submitted_event, "SUBMITTED")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish submitted event: {str(e)}"
        )

    # Step 3: Call ML service for categorization
    try:
        response = httpx.post(
            f"{ML_SERVICE_URL}/predict",
            json={"complaint": text},
            timeout=30.0
        )
        response.raise_for_status()
        prediction = response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="ML Service is unavailable"
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"ML Service error: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prediction: {str(e)}"
        )

    category = prediction["category"]
    priority = prediction["priority"]
    department = prediction["department"]

    # Step 4: Update DB with categorization
    try:
        update_complaint_categorized(
            complaint_id, category, priority, None, department
        )
    except Exception as e:
        print(f"Warning: Failed to update DB: {e}")

    # Step 5: Publish to complaint-categorized
    categorized_event = {
        "complaint_id": complaint_id,
        "description": text,
        "category": category,
        "priority": priority,
        "department": department,
        "status": "CATEGORIZED",
        "timestamp": timestamp
    }

    try:
        send_complaint_categorized(categorized_event)
        insert_event(complaint_id, "complaint-categorized", categorized_event, "CATEGORIZED")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish categorized event: {str(e)}"
        )

    return {
        "message": "Complaint received and categorized",
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "department": department
    }


# ===============================
# Get Complaint by ID
# ===============================
@app.get("/complaint/{complaint_id}")
def get_complaint_by_id(complaint_id: str):
    complaint = get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return dict(complaint)


# ===============================
# Get All Complaints
# ===============================
@app.get("/complaints")
def list_complaints():
    complaints = get_all_complaints()
    return [dict(c) for c in complaints]