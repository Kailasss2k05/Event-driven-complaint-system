from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Dict, Optional
import json
import asyncio
from datetime import datetime

from .kafka_consumer import start_kafka_consumers
from .email_service import EmailService
from .websocket_manager import WebSocketManager
from .notification_store import NotificationStore
from backend.db.database import get_current_user
from backend.auth.router import router as auth_router

# Initialize services
email_service = EmailService()
websocket_manager = WebSocketManager()
notification_store = NotificationStore()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start Kafka consumers
    kafka_task = asyncio.create_task(start_kafka_consumers(email_service, websocket_manager, notification_store))
    yield
    # Shutdown: Cancel Kafka consumers
    kafka_task.cancel()
    try:
        await kafka_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="Notification Service", 
    version="1.0.0",
    lifespan=lifespan
)

# Include auth endpoints so Swagger /docs Authorize works on this port
app.include_router(auth_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class NotificationRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    message: str
    notification_type: str = "general"

class NotificationPreferences(BaseModel):
    email_notifications: bool = True
    sms_notifications: bool = False
    push_notifications: bool = True
    complaint_updates: bool = True
    department_alerts: bool = True

@app.get("/")
async def health_check():
    return {"status": "Notification Service Running", "timestamp": datetime.now()}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    await websocket_manager.connect(websocket, user_id)
    try:
        while True:
            # Keep connection alive and listen for messages
            await websocket.receive_text()
    except WebSocketDisconnect:
        websocket_manager.disconnect(user_id)

@app.post("/send-notification")
async def send_notification(notification: NotificationRequest, current_user: dict = Depends(get_current_user)):
    """Send a manual notification (admin only)."""
    if current_user["role"] not in ["department_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        await email_service.send_email(
            to_email=notification.recipient_email,
            subject=notification.subject,
            body=notification.message,
            template_type=notification.notification_type
        )
        return {"message": "Notification sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")

@app.get("/notifications/{user_id}")
async def get_user_notifications(user_id: int, current_user: dict = Depends(get_current_user)):
    """Get notifications for a user."""
    # Users can only see their own notifications, admins can see any
    if current_user["id"] != user_id and current_user["role"] not in ["department_admin", "super_admin"]:
        raise HTTPException(status_code=403, detail="Access denied")
    
    notifications = notification_store.get_user_notifications(user_id)
    return {"notifications": notifications}

@app.put("/notifications/{notification_id}/mark-read")
async def mark_notification_read(notification_id: str, current_user: dict = Depends(get_current_user)):
    """Mark a notification as read."""
    notification_store.mark_as_read(notification_id, current_user["id"])
    return {"message": "Notification marked as read"}

@app.post("/preferences")
async def update_notification_preferences(preferences: NotificationPreferences, current_user: dict = Depends(get_current_user)):
    """Update user notification preferences."""
    notification_store.update_preferences(current_user["id"], preferences.dict())
    return {"message": "Notification preferences updated"}

@app.get("/preferences")
async def get_notification_preferences(current_user: dict = Depends(get_current_user)):
    """Get user notification preferences."""
    preferences = notification_store.get_preferences(current_user["id"])
    return {"preferences": preferences}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)