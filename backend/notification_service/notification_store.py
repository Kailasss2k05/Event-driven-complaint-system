import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class NotificationStore:
    """In-memory notification storage. In production, use Redis or Database."""
    
    def __init__(self):
        # Store notifications: {user_id: [notifications]}
        self.notifications: Dict[int, List[dict]] = {}
        # Store user preferences: {user_id: preferences_dict}
        self.preferences: Dict[int, dict] = {}
        # Store notification by ID for quick lookup: {notification_id: notification}
        self.notification_lookup: Dict[str, dict] = {}
        
        # Default preferences
        self.default_preferences = {
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": True,
            "complaint_updates": True,
            "department_alerts": True,
            "marketing": False
        }
    
    def add_notification(self, user_id: int, notification_data: dict) -> str:
        """Add a notification for a user."""
        notification_id = str(uuid.uuid4())
        
        notification = {
            "id": notification_id,
            "user_id": user_id,
            "type": notification_data.get("type", "general"),
            "title": notification_data.get("title", "Notification"),
            "message": notification_data.get("message", ""),
            "complaint_id": notification_data.get("complaint_id"),
            "timestamp": notification_data.get("timestamp", datetime.now().isoformat()),
            "read": False,
            "metadata": notification_data.get("metadata", {})
        }
        
        # Add to user's notifications
        if user_id not in self.notifications:
            self.notifications[user_id] = []
        
        self.notifications[user_id].insert(0, notification)  # Most recent first
        
        # Add to lookup
        self.notification_lookup[notification_id] = notification
        
        # Limit notifications per user (keep last 100)
        if len(self.notifications[user_id]) > 100:
            old_notification = self.notifications[user_id].pop()
            if old_notification["id"] in self.notification_lookup:
                del self.notification_lookup[old_notification["id"]]
        
        logger.info(f"Added notification {notification_id} for user {user_id}")
        return notification_id
    
    def get_user_notifications(self, user_id: int, limit: int = 50, unread_only: bool = False) -> List[dict]:
        """Get notifications for a user."""
        if user_id not in self.notifications:
            return []
        
        notifications = self.notifications[user_id]
        
        if unread_only:
            notifications = [n for n in notifications if not n["read"]]
        
        return notifications[:limit]
    
    def mark_as_read(self, notification_id: str, user_id: int) -> bool:
        """Mark a notification as read."""
        if notification_id in self.notification_lookup:
            notification = self.notification_lookup[notification_id]
            if notification["user_id"] == user_id:
                notification["read"] = True
                logger.info(f"Marked notification {notification_id} as read for user {user_id}")
                return True
        
        logger.warning(f"Failed to mark notification {notification_id} as read for user {user_id}")
        return False
    
    def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user."""
        if user_id not in self.notifications:
            return 0
        
        count = 0
        for notification in self.notifications[user_id]:
            if not notification["read"]:
                notification["read"] = True
                count += 1
        
        logger.info(f"Marked {count} notifications as read for user {user_id}")
        return count
    
    def delete_notification(self, notification_id: str, user_id: int) -> bool:
        """Delete a notification."""
        if notification_id in self.notification_lookup:
            notification = self.notification_lookup[notification_id]
            if notification["user_id"] == user_id:
                # Remove from user's notifications
                if user_id in self.notifications:
                    self.notifications[user_id] = [
                        n for n in self.notifications[user_id] 
                        if n["id"] != notification_id
                    ]
                # Remove from lookup
                del self.notification_lookup[notification_id]
                logger.info(f"Deleted notification {notification_id} for user {user_id}")
                return True
        
        return False
    
    def get_unread_count(self, user_id: int) -> int:
        """Get unread notification count for a user."""
        if user_id not in self.notifications:
            return 0
        
        return sum(1 for n in self.notifications[user_id] if not n["read"])
    
    def update_preferences(self, user_id: int, preferences: dict):
        """Update notification preferences for a user."""
        if user_id not in self.preferences:
            self.preferences[user_id] = self.default_preferences.copy()
        
        self.preferences[user_id].update(preferences)
        logger.info(f"Updated preferences for user {user_id}")
    
    def get_preferences(self, user_id: int) -> dict:
        """Get notification preferences for a user."""
        if user_id not in self.preferences:
            self.preferences[user_id] = self.default_preferences.copy()
        
        return self.preferences[user_id]
    
    def cleanup_old_notifications(self, days: int = 30):
        """Clean up notifications older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        cleaned = 0
        
        for user_id in list(self.notifications.keys()):
            original_count = len(self.notifications[user_id])
            
            # Keep notifications newer than cutoff
            self.notifications[user_id] = [
                n for n in self.notifications[user_id]
                if datetime.fromisoformat(n["timestamp"]) > cutoff_date
            ]
            
            cleaned += original_count - len(self.notifications[user_id])
            
            # Clean up empty lists
            if not self.notifications[user_id]:
                del self.notifications[user_id]
        
        # Clean up lookup table
        valid_ids = set()
        for notifications in self.notifications.values():
            valid_ids.update(n["id"] for n in notifications)
        
        for notification_id in list(self.notification_lookup.keys()):
            if notification_id not in valid_ids:
                del self.notification_lookup[notification_id]
        
        logger.info(f"Cleaned up {cleaned} old notifications")
        return cleaned