import os
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel

from backend.complaint_service.kafka_producer import send_complaint_submitted, send_complaint_categorized
from backend.db.database import (
    insert_complaint,
    update_complaint_categorized,
    get_complaint,
    get_all_complaints,
    get_complaints_by_user,
    get_current_user,
    can_access_complaint,
    require_role,
    get_complaints_by_department,
    generate_complaint_id
)
from backend.auth.router import router as auth_router

load_dotenv()

app = FastAPI(title="Complaint Service", version="1.0.0")

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL")


# ===============================
# Request Models
# ===============================
class ComplaintRequest(BaseModel):
    description: str


# ===============================
# AUTHENTICATION
# ===============================
# Include auth endpoints: POST /auth/token, GET /auth/me
app.include_router(auth_router)


# ===============================
# COMPLAINTS
# ===============================

@app.post("/complaint", tags=["Complaints"])
async def create_complaint(
    complaint: ComplaintRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit a new complaint."""
    text = complaint.description
    complaint_id = generate_complaint_id()
    timestamp = datetime.now(timezone.utc).isoformat()
    user_id = current_user["id"]

    # Step 1: Save to database
    try:
        insert_complaint(complaint_id, text, user_id, status="SUBMITTED")
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
        # Note: Audit service will log this event from Kafka
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
        # Note: Audit service will log this event from Kafka
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


@app.get("/complaint/{complaint_id}", tags=["Complaints"])
async def get_complaint_by_id(
    complaint_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get specific complaint (with access control)."""
    complaint = get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    
    # Check role-based access
    if not can_access_complaint(current_user, complaint_id):
        raise HTTPException(
            status_code=403,
            detail="Access denied. You can only view complaints within your scope."
        )
    
    return dict(complaint)


# ===============================
# ROLE-SPECIFIC VIEWS
# ===============================

@app.get("/complaints/me", tags=["Role-Specific Views"])
async def get_my_complaints(current_user: dict = Depends(get_current_user)):
    """My complaints — get all complaints submitted by the current user."""
    complaints = get_complaints_by_user(current_user["id"])
    return [dict(c) for c in complaints]


@app.get("/admin/complaints/department", tags=["Role-Specific Views"])
async def get_department_complaints(
    admin_user: dict = Depends(require_role("department_admin", "super_admin"))
):
    """Department complaints — get all complaints for the admin's department. Super admins see all."""
    if admin_user["role"] == "super_admin":
        complaints = get_all_complaints()
    elif admin_user["role"] == "department_admin" and admin_user["department_name"]:
        complaints = get_complaints_by_department(admin_user["department_name"])
    else:
        raise HTTPException(
            status_code=403,
            detail="Access denied. Department admin role required."
        )
    
    return [dict(c) for c in complaints]


@app.get("/admin/complaints/all", tags=["Role-Specific Views"])
async def get_all_complaints_admin(
    super_admin: dict = Depends(require_role("super_admin"))
):
    """All complaints — get all complaints across all departments (super admin only)."""
    complaints = get_all_complaints()
    return [dict(c) for c in complaints]