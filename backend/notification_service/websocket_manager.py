from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio
import logging

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        # Store active connections: {user_id: [websocket_connections]}
        self.active_connections: Dict[int, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        
        self.active_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected for user {user_id}. Total connections: {len(self.active_connections[user_id])}")
    
    def disconnect(self, user_id: int, websocket: WebSocket = None):
        """Remove a WebSocket connection."""
        if user_id in self.active_connections:
            if websocket:
                # Remove specific websocket
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)
            else:
                # Remove all connections for user
                self.active_connections[user_id] = []
            
            # Clean up empty connection lists
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
            
            logger.info(f"WebSocket disconnected for user {user_id}")
    
    async def send_notification(self, user_id: int, notification: dict):
        """Send notification to a specific user."""
        if user_id in self.active_connections:
            message = json.dumps(notification)
            disconnected_sockets = []
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(message)
                    logger.info(f"Notification sent to user {user_id}")
                except Exception as e:
                    logger.error(f"Failed to send notification to user {user_id}: {e}")
                    disconnected_sockets.append(websocket)
            
            # Remove disconnected sockets
            for socket in disconnected_sockets:
                self.disconnect(user_id, socket)
        else:
            logger.info(f"No active connections for user {user_id}")
    
    async def broadcast_notification(self, notification: dict, exclude_users: List[int] = None):
        """Broadcast notification to all connected users."""
        exclude_users = exclude_users or []
        message = json.dumps(notification)
        
        for user_id, connections in self.active_connections.items():
            if user_id not in exclude_users:
                disconnected_sockets = []
                
                for websocket in connections:
                    try:
                        await websocket.send_text(message)
                    except Exception as e:
                        logger.error(f"Failed to broadcast to user {user_id}: {e}")
                        disconnected_sockets.append(websocket)
                
                # Remove disconnected sockets
                for socket in disconnected_sockets:
                    self.disconnect(user_id, socket)
        
        logger.info(f"Broadcast sent to {len(self.active_connections)} users")
    
    async def send_department_notification(self, department_name: str, notification: dict):
        """Send notification to all users in a specific department (department admins)."""
        # This would require database integration to find users by department
        # For now, we'll broadcast to all admins
        await self.broadcast_notification(notification)
    
    def get_connection_count(self, user_id: int = None) -> int:
        """Get connection count for specific user or total."""
        if user_id:
            return len(self.active_connections.get(user_id, []))
        else:
            return sum(len(connections) for connections in self.active_connections.values())
    
    def get_connected_users(self) -> List[int]:
        """Get list of currently connected user IDs."""
        return list(self.active_connections.keys())