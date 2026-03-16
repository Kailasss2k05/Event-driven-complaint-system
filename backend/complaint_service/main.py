import os
import json
import base64
import httpx
import cloudinary
import cloudinary.uploader
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional

from backend.complaint_service.kafka_producer import (
    send_complaint_submitted,
    send_complaint_validated,
    send_complaint_categorized,
    send_complaint_assigned,
    send_complaint_status_updated
)
from backend.db.database import (
    insert_complaint,
    update_complaint_categorized,
    get_complaint,
    get_all_complaints,
    get_complaints_by_user,
    get_recent_complaints_by_user,
    get_current_user,
    can_access_complaint,
    require_role,
    get_complaints_by_department,
    generate_complaint_id,
    update_complaint_status,
    update_complaint_assigned,
    update_complaint_rerouted
)
from fastapi.middleware.cors import CORSMiddleware
from backend.auth.router import router as auth_router

load_dotenv()

app = FastAPI(title="Complaint Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)


# ===============================
# INLINE VALIDATION HELPERS
# (load same rules as validation_service)
# ===============================
def _load_validation_rules():
    """Load profanity words and spam patterns from validation_rules.json"""
    config_path = os.path.join(
        os.path.dirname(__file__), '..', 'validation_service', 'validation_rules.json'
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        if 'profanity_words_encoded' in rules:
            profanity = set()
            for enc in rules.get('profanity_words_encoded', []):
                try:
                    profanity.add(base64.b64decode(enc).decode('utf-8'))
                except Exception:
                    pass
            return profanity, rules.get('spam_patterns', [])
        return set(rules.get('profanity_words', [])), rules.get('spam_patterns', [])
    except Exception:
        return set(), []


PROFANITY_WORDS, SPAM_PATTERNS = _load_validation_rules()


def _run_content_validation(description: str, user_id: int) -> tuple[bool, str]:
    """Run profanity, spam, and duplicate checks. Returns (is_valid, reason)."""
    desc_lower = description.lower()

    # Profanity check
    for word in PROFANITY_WORDS:
        if word in desc_lower:
            return False, "Complaint contains inappropriate language"

    # Spam pattern check
    for pattern in SPAM_PATTERNS:
        if pattern in desc_lower:
            return False, "Complaint flagged as potential spam"

    # Excessive capitalisation (>70%)
    if len(description) > 10:
        caps_ratio = sum(1 for c in description if c.isupper()) / len(description)
        if caps_ratio > 0.7:
            return False, "Complaint contains excessive capitalisation"

    # Excessive punctuation (>10%)
    punct_ratio = sum(1 for c in description if c in '!?.') / len(description)
    if len(description) > 10 and punct_ratio > 0.1:
        return False, "Complaint contains excessive punctuation"

    # Duplicate detection — same/similar complaint within 12 hours
    try:
        recent = get_recent_complaints_by_user(user_id, minutes=720)
        for complaint in recent:
            existing = complaint.get('description', '').lower().strip()
            if desc_lower == existing:
                return False, f"Duplicate complaint detected (ID: {complaint['complaint_id']})"
            if len(desc_lower) > 10 and len(existing) > 10:
                shorter = min(desc_lower, existing, key=len)
                longer  = max(desc_lower, existing, key=len)
                if shorter in longer:
                    return False, f"Similar complaint already submitted (ID: {complaint['complaint_id']})"
    except Exception:
        pass  # DB error — allow through

    return True, ""


# ===============================
# Request Models
# ===============================
class ComplaintRequest(BaseModel):
    description: str
    image_url: Optional[str] = None


class ComplaintAssignmentRequest(BaseModel):
    assigned_to: str = None          # Person/officer being assigned (optional for re-route)
    target_department: str = None    # New department to re-route to (for re-routing only)
    notes: str = None                # Reason for re-routing or assignment notes


class ComplaintStatusUpdateRequest(BaseModel):
    status: str  # Status to update to
    notes: str = None  # Optional notes about the status update


# ===============================
# AUTHENTICATION
# ===============================
# Include auth endpoints: POST /auth/token, GET /auth/me
app.include_router(auth_router)


@app.post("/complaint/upload-image", tags=["Complaints"])
async def upload_complaint_image(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload an image for a complaint. Returns the image URL to include when submitting."""
    allowed_types = {"image/jpeg", "image/jpg", "image/png", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPG, PNG, and WebP images are allowed")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image must be under 5 MB")

    try:
        result = cloudinary.uploader.upload(
            contents,
            folder="complaint_images",
            resource_type="image"
        )
        return {"image_url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")


# ===============================
# COMPLAINTS
# ===============================

@app.post("/complaint", tags=["Complaints"])
async def create_complaint(
    complaint: ComplaintRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit a new complaint. Automatically translates non-English text and generates a summary."""
    text = complaint.description
    
    # Step 0: Synchronous validation (blocks before anything is saved)
    text_stripped = text.strip()
    if len(text_stripped) < 10:
        raise HTTPException(status_code=400, detail="Complaint description too short (minimum 10 characters)")
    if len(text_stripped) > 5000:
        raise HTTPException(status_code=400, detail="Complaint description too long (maximum 5000 characters)")

    text = text_stripped
    user_id = current_user["id"]

    is_valid, rejection_reason = _run_content_validation(text, user_id)
    if not is_valid:
        raise HTTPException(status_code=400, detail=rejection_reason)

    complaint_id = generate_complaint_id()
    timestamp = datetime.now(timezone.utc).isoformat()

    # Step 1: Translate to English (if needed)
    translated_text = text
    original_language = "en"
    was_translated = False
    try:
        tr_response = httpx.post(
            f"{ML_SERVICE_URL}/translate",
            json={"text": text},
            timeout=15.0
        )
        tr_response.raise_for_status()
        tr_result = tr_response.json()
        translated_text = tr_result.get("translated", text)
        original_language = tr_result.get("language", "en")
        was_translated = tr_result.get("was_translated", False)
    except Exception as e:
        print(f"Warning: Translation failed, using original text: {e}")

    # Step 2: Summarize the (translated) complaint
    summary = None
    try:
        sm_response = httpx.post(
            f"{ML_SERVICE_URL}/summarize",
            json={"text": translated_text, "max_sentences": 2},
            timeout=10.0
        )
        sm_response.raise_for_status()
        summary = sm_response.json().get("summary")
    except Exception as e:
        print(f"Warning: Summarization failed: {e}")

    # Step 3: Save to database (with translation + summary)
    try:
        insert_complaint(
            complaint_id, text, user_id, status="SUBMITTED",
            translated_description=translated_text if was_translated else None,
            summary=summary,
            original_language=original_language,
            image_url=complaint.image_url
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save complaint: {str(e)}")

    # Step 4: Publish to complaint-submitted (notification + audit)
    submitted_event = {
        "complaint_id": complaint_id,
        "description": text,
        "user_id": user_id,
        "status": "SUBMITTED",
        "timestamp": timestamp
    }
    try:
        send_complaint_submitted(submitted_event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish submitted event: {str(e)}")

    # Step 4b: Publish to complaint-validated (validation passed inline)
    validated_event = submitted_event.copy()
    validated_event["validation_status"] = "PASSED"
    try:
        send_complaint_validated(validated_event)
    except Exception as e:
        print(f"Warning: Failed to publish validated event: {e}")

    # Step 5: Call ML service for categorization (on translated text)
    try:
        response = httpx.post(
            f"{ML_SERVICE_URL}/predict",
            json={"complaint": translated_text},
            timeout=30.0
        )
        response.raise_for_status()
        prediction = response.json()
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="ML Service is unavailable")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"ML Service error: {e.response.text}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get prediction: {str(e)}")

    category = prediction["category"]
    priority = prediction["priority"]
    severity = prediction.get("severity")
    department = prediction["department"]
    eisenhower_quadrant = prediction.get("eisenhower_quadrant")

    # Step 6: Update DB with categorization
    try:
        update_complaint_categorized(complaint_id, category, priority, severity, department)
    except Exception as e:
        print(f"Warning: Failed to update DB categorization: {e}")

    # Step 7: Publish to complaint-categorized
    categorized_event = {
        "complaint_id": complaint_id,
        "description": text,
        "category": category,
        "priority": priority,
        "severity": severity,
        "department": department,
        "eisenhower_quadrant": eisenhower_quadrant,
        "status": "CATEGORIZED",
        "timestamp": timestamp
    }
    try:
        send_complaint_categorized(categorized_event)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish categorized event: {str(e)}")

    return {
        "message": "Complaint received and categorized",
        "complaint_id": complaint_id,
        "original_language": original_language,
        "was_translated": was_translated,
        "summary": summary,
        "category": category,
        "priority": priority,
        "severity": severity,
        "department": department,
        "eisenhower_quadrant": eisenhower_quadrant
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


# ===============================
# COMPLAINT STATUS MANAGEMENT
# ===============================

@app.put("/admin/complaint/{complaint_id}/assign", tags=["Status Management"])
async def assign_complaint(
    complaint_id: str,
    assignment: ComplaintAssignmentRequest,
    admin_user: dict = Depends(require_role("department_admin", "super_admin"))
):
    """
    Assign or re-route a complaint.

    - Initial assignment: provide `assigned_to` (auto-assignment from assignment service also uses this).
    - Re-routing: provide `target_department` (and optionally `notes`) to hand off to another department.
      e.g. Health dept resolves mosquito issue → re-routes to Engineering for pothole fix.

    Department admin rules:
    - Can assign/re-route complaints currently belonging to their own department.
    - Can re-route to ANY department (not restricted to their own).
    Super admin can do everything.
    """
    complaint = get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Dept admin must own the complaint's current department to act on it
    if admin_user["role"] == "department_admin":
        if admin_user["department_name"] != complaint["department"]:
            raise HTTPException(
                status_code=403,
                detail=f"You can only assign or re-route complaints currently in your department ({admin_user['department_name']})."
            )

    is_reroute = bool(assignment.target_department and assignment.target_department != complaint["department"])

    try:
        if is_reroute:
            # Re-route: change department, clear assignee, reset to ASSIGNED
            update_complaint_rerouted(complaint_id, assignment.target_department)
            from_department = complaint["department"]
            to_department = assignment.target_department

            assignment_event = {
                "complaint_id": complaint_id,
                "is_reroute": True,
                "from_department": from_department,
                "to_department": to_department,
                "department": to_department,
                "category": complaint["category"],
                "priority": complaint["priority"],
                "notes": assignment.notes or "",
                "rerouted_by": admin_user["id"],
                "status": "ASSIGNED",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            send_complaint_assigned(assignment_event)

            return {
                "message": f"Complaint re-routed from {from_department} to {to_department}",
                "complaint_id": complaint_id,
                "from_department": from_department,
                "to_department": to_department
            }
        else:
            # Initial / within-department assignment
            if not assignment.assigned_to:
                raise HTTPException(status_code=400, detail="Provide either assigned_to (for assignment) or target_department (for re-routing).")

            update_complaint_assigned(complaint_id, assignment.assigned_to)

            assignment_event = {
                "complaint_id": complaint_id,
                "is_reroute": False,
                "assigned_to": assignment.assigned_to,
                "assigned_by": admin_user["id"],
                "department": complaint["department"],
                "category": complaint["category"],
                "priority": complaint["priority"],
                "notes": assignment.notes or "",
                "status": "ASSIGNED",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            send_complaint_assigned(assignment_event)

            return {"message": "Complaint assigned successfully", "complaint_id": complaint_id}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process assignment: {str(e)}")


@app.put("/complaint/{complaint_id}/status", tags=["Status Management"])
async def update_complaint_status_endpoint(
    complaint_id: str,
    status_update: ComplaintStatusUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update complaint status.
    - Department admin: can update status of complaints in their department.
    - Assignee (regular user): can update status of complaints assigned to them.
    - Super admin: view-only — cannot update status.
    """
    # Check if complaint exists
    complaint = get_complaint(complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Only department admins can update complaint status
    if current_user["role"] == "super_admin":
        raise HTTPException(
            status_code=403,
            detail="Super admin has view-only access. Only department admins can update complaint status."
        )

    if current_user["role"] != "department_admin":
        raise HTTPException(
            status_code=403,
            detail="Only department admins can update complaint status."
        )

    # Department admin can only update complaints in their own department
    if current_user["department_name"] != complaint["department"]:
        raise HTTPException(
            status_code=403,
            detail="You can only update complaints belonging to your department."
        )

    # Only actionable statuses are allowed via this endpoint
    valid_statuses = ["IN_PROGRESS", "RESOLVED", "DUMPED", "CLOSED"]
    if status_update.status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Department admins can set: {', '.join(valid_statuses)}"
        )
    
    try:
        # Update status in database  
        update_complaint_status(complaint_id, status_update.status)
        
        # Publish status update event to Kafka
        status_event = {
            "complaint_id": complaint_id,
            "old_status": complaint["status"],
            "new_status": status_update.status,
            "updated_by": current_user["id"],
            "notes": status_update.notes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        send_complaint_status_updated(status_event)
        
        return {
            "message": "Complaint status updated successfully",
            "complaint_id": complaint_id,
            "new_status": status_update.status
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update complaint status: {str(e)}"
        )


@app.get("/", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "complaint_service"}