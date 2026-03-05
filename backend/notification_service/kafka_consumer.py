import os
import json
import asyncio
from dotenv import load_dotenv
from kafka import KafkaConsumer
from datetime import datetime
import logging

load_dotenv()

# Add project root to path for imports
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.db.database import get_user_by_id, get_complaint

KAFKA_BROKER = os.getenv("KAFKA_BROKER")

# All topics to listen to
TOPICS = [
    os.getenv("TOPIC_COMPLAINT_SUBMITTED"),
    os.getenv("TOPIC_COMPLAINT_VALIDATED"),
    os.getenv("TOPIC_COMPLAINT_CATEGORIZED"),
    os.getenv("TOPIC_COMPLAINT_ASSIGNED"),
    os.getenv("TOPIC_COMPLAINT_STATUS_UPDATED"),
]

# Filter out None values
TOPICS = [topic for topic in TOPICS if topic]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start_kafka_consumers(email_service, websocket_manager, notification_store):
    """Start Kafka consumers for all complaint events."""
    logger.info(f"Starting Kafka consumers for topics: {TOPICS}")
    
    loop = asyncio.get_event_loop()
    
    consumer = KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="latest",
        enable_auto_commit=True,
        group_id="notification-group"
    )
    
    try:
        while True:
            # poll() is non-blocking with a short timeout — won't freeze the event loop
            msg_pack = await loop.run_in_executor(
                None, lambda: consumer.poll(timeout_ms=500, max_records=10)
            )
            for tp, messages in msg_pack.items():
                for message in messages:
                    await process_event(message, email_service, websocket_manager, notification_store)
            # Yield control back to the event loop
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logger.info("Kafka consumer cancelled, shutting down...")
    except Exception as e:
        logger.error(f"Kafka consumer error: {e}")
    finally:
        consumer.close()
        logger.info("Kafka consumer closed.")

async def process_event(message, email_service, websocket_manager, notification_store):
    """Process incoming Kafka events and send appropriate notifications."""
    try:
        topic = message.topic
        event_data = message.value
        
        logger.info(f"Processing event from topic: {topic}")
        logger.info(f"Event data: {event_data}")
        
        complaint_id = event_data.get("complaint_id")
        if not complaint_id:
            logger.warning("No complaint_id in event data")
            return
        
        # Get complaint details
        complaint = get_complaint(complaint_id)
        if not complaint:
            logger.warning(f"Complaint {complaint_id} not found")
            return
            
        user_id = complaint.get("user_id")
        if not user_id:
            logger.warning(f"No user_id for complaint {complaint_id}")
            return
            
        # Get user details
        user = get_user_by_id(user_id)
        if not user:
            logger.warning(f"User {user_id} not found")
            return
        
        # Process based on topic
        if topic == os.getenv("TOPIC_COMPLAINT_SUBMITTED"):
            await handle_complaint_submitted(event_data, user, email_service, websocket_manager, notification_store)
        elif topic == os.getenv("TOPIC_COMPLAINT_ASSIGNED"):
            await handle_complaint_assigned(event_data, user, complaint, email_service, websocket_manager, notification_store)
        elif topic == os.getenv("TOPIC_COMPLAINT_STATUS_UPDATED"):
            await handle_status_updated(event_data, user, complaint, email_service, websocket_manager, notification_store)
            
    except Exception as e:
        logger.error(f"Error processing event: {e}")

async def handle_complaint_submitted(event_data, user, email_service, websocket_manager, notification_store):
    """Handle new complaint submission — send confirmation email to user."""
    complaint_id = event_data.get("complaint_id")
    description = event_data.get("description", "N/A")
    short_desc = (description[:120] + "...") if len(description) > 120 else description

    # Notify user via email
    await email_service.send_email(
        to_email=user["email"],
        subject=f"Complaint Submitted Successfully - #{complaint_id}",
        template_type="complaint_submitted",
        template_data={
            "user_name": user["username"],
            "complaint_id": complaint_id,
            "description": short_desc
        }
    )
    
    # Send real-time notification
    await websocket_manager.send_notification(user["id"], {
        "type": "complaint_submitted",
        "message": f"Your complaint {complaint_id} has been submitted successfully",
        "complaint_id": complaint_id,
        "timestamp": datetime.now().isoformat()
    })
    
    # Store notification
    notification_store.add_notification(user["id"], {
        "type": "complaint_submitted",
        "title": "Complaint Submitted",
        "message": f"Your complaint {complaint_id} has been received and is being processed",
        "complaint_id": complaint_id,
        "timestamp": datetime.now().isoformat()
    })

async def handle_complaint_categorized(event_data, user, complaint, email_service, websocket_manager, notification_store):
    """Handle complaint categorization."""
    complaint_id = event_data.get("complaint_id")
    category = event_data.get("category")
    priority = event_data.get("priority")
    department = event_data.get("department")
    
    # Notify user via email
    await email_service.send_email(
        to_email=user["email"],
        subject="Complaint Processed and Categorized",
        template_type="complaint_categorized",
        template_data={
            "user_name": user["username"],
            "complaint_id": complaint_id,
            "category": category,
            "priority": priority,
            "department": department
        }
    )
    
    # Send real-time notification
    await websocket_manager.send_notification(user["id"], {
        "type": "complaint_categorized",
        "message": f"Your complaint has been categorized as '{category}' with '{priority}' priority",
        "complaint_id": complaint_id,
        "category": category,
        "priority": priority,
        "department": department,
        "timestamp": datetime.now().isoformat()
    })

async def handle_complaint_assigned(event_data, user, complaint, email_service, websocket_manager, notification_store):
    """Handle complaint assignment or re-routing — SEND EMAIL."""
    complaint_id = event_data.get("complaint_id")
    is_reroute = event_data.get("is_reroute", False)
    department = event_data.get("department") or complaint.get("department", "Unknown Department")
    category = event_data.get("category") or complaint.get("category", "Unknown")
    priority = event_data.get("priority") or complaint.get("priority", "Normal")
    notes = event_data.get("notes", "")

    if is_reroute:
        from_dept = event_data.get("from_department", "Previous Department")
        to_dept = event_data.get("to_department", department)
        subject = f"Complaint Re-routed to {to_dept} - #{complaint_id}"
        body = f"""Dear {user['username']},

Your complaint has been reviewed by {from_dept} and re-routed to {to_dept} for further action.

--------------------------------------------------
Complaint ID   : {complaint_id}
Previous Dept  : {from_dept}
New Department : {to_dept}
Category       : {category}
Priority       : {priority}
{f'Notes          : {notes}' if notes else ''}
--------------------------------------------------

The new department will begin reviewing your complaint shortly.

Best regards,
Municipal Complaint System"""
        ws_message = f"Your complaint has been re-routed from {from_dept} to {to_dept}"
        store_title = "Complaint Re-routed"
        store_message = f"Complaint {complaint_id} re-routed from {from_dept} to {to_dept}"
    else:
        assigned_to = event_data.get("assigned_to") or complaint.get("assigned_to", "N/A")
        subject = f"Complaint Assigned to {department} - #{complaint_id}"
        body = f"""Dear {user['username']},

Your complaint has been assigned to a department officer for resolution.

--------------------------------------------------
Complaint ID   : {complaint_id}
Department     : {department}
Assigned To    : {assigned_to}
Category       : {category}
Priority       : {priority}
--------------------------------------------------

The team will begin reviewing your complaint shortly.
You will receive further updates as the status progresses.

Best regards,
Municipal Complaint System"""
        ws_message = f"Your complaint has been assigned to {department}"
        store_title = "Complaint Assigned"
        store_message = f"Complaint {complaint_id} assigned to {department} department"

    await email_service.send_email(
        to_email=user["email"],
        subject=subject,
        body=body
    )

    await websocket_manager.send_notification(user["id"], {
        "type": "complaint_rerouted" if is_reroute else "complaint_assigned",
        "message": ws_message,
        "complaint_id": complaint_id,
        "department": department,
        "timestamp": datetime.now().isoformat()
    })

    notification_store.add_notification(user["id"], {
        "type": "complaint_rerouted" if is_reroute else "complaint_assigned",
        "title": store_title,
        "message": store_message,
        "complaint_id": complaint_id,
        "timestamp": datetime.now().isoformat()
    })

async def handle_status_updated(event_data, user, complaint, email_service, websocket_manager, notification_store):
    """Handle complaint status updates - SEND EMAIL for important status changes."""
    complaint_id = event_data.get("complaint_id")
    # new_status is the key used by the status update endpoint
    new_status = event_data.get("new_status") or event_data.get("status", "UPDATED")
    
    # Determine email subject and message based on status (keys match IN_PROGRESS.lower() = in_progress)
    email_subjects = {
        "in_progress": "Your Complaint is Now Being Processed",
        "resolved": "✅ Your Complaint Has Been Resolved",
        "dumped": "Complaint Update - Unable to Process",
        "closed": "Your Complaint Has Been Closed",
        "assigned": "Your Complaint Has Been Assigned",
    }

    email_messages = {
        "in_progress": "Great news! Your complaint is now being actively worked on by the department team.",
        "resolved": "Your complaint has been successfully resolved. Thank you for your patience.",
        "dumped": "We were unable to process your complaint at this time. Please contact us for more details or re-submit.",
        "closed": "Your complaint has been officially closed. Thank you for helping us improve our services.",
        "assigned": "Your complaint has been assigned to a department officer and will be reviewed shortly.",
    }

    status_key = new_status.lower()
    subject = email_subjects.get(status_key, f"Complaint Status Update — {new_status}")
    custom_message = email_messages.get(status_key, f"Your complaint status has been updated to: {new_status}")
    
    # Send email notification
    await email_service.send_email(
        to_email=user["email"],
        subject=subject,
        template_type="status_updated",
        template_data={
            "user_name": user["username"],
            "complaint_id": complaint_id,
            "status": new_status,
            "custom_message": custom_message
        }
    )
    
    # Send real-time notification
    await websocket_manager.send_notification(user["id"], {
        "type": "status_updated",
        "message": custom_message,
        "complaint_id": complaint_id,
        "status": new_status,
        "timestamp": datetime.now().isoformat()
    })
    
    # Store notification
    notification_store.add_notification(user["id"], {
        "type": "status_updated",
        "title": f"Status: {new_status.title()}",
        "message": custom_message,
        "complaint_id": complaint_id,
        "timestamp": datetime.now().isoformat()
    })