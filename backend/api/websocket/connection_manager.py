"""
WebSocket connection manager.

Manages active WebSocket connections và broadcasting messages.
"""

# Standard library
from typing import Dict, Set, List
from fastapi import WebSocket
import json
import asyncio

# Local
from services.logger import StructuredLogger

logger = StructuredLogger(name="websocket_manager")


class ConnectionManager:
    """
    Manages WebSocket connections.
    
    Supports room-based messaging for different features/accounts.
    """
    
    def __init__(self):
        """Initialize connection manager."""
        # Active connections: {websocket: {room: set, account_id: str}}
        self.active_connections: Dict[WebSocket, Dict] = {}
        # Rooms: {room_name: set(websockets)}
        self.rooms: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, room: str = "default", account_id: str = None):
        """
        Connect a WebSocket client.
        
        Args:
            websocket: WebSocket connection
            room: Room name (e.g., "scheduler", "dashboard", "jobs")
            account_id: Optional account ID for filtering
        """
        await websocket.accept()
        self.active_connections[websocket] = {
            "room": room,
            "account_id": account_id
        }
        
        # Add to room
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(websocket)
        
        logger.log_step(
            step="WEBSOCKET_CONNECT",
            result="SUCCESS",
            room=room,
            account_id=account_id,
            total_connections=len(self.active_connections)
        )
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket client.
        
        Args:
            websocket: WebSocket connection to disconnect
        """
        if websocket in self.active_connections:
            room = self.active_connections[websocket].get("room")
            if room and room in self.rooms:
                self.rooms[room].discard(websocket)
                if not self.rooms[room]:
                    del self.rooms[room]
            
            del self.active_connections[websocket]
            
            logger.log_step(
                step="WEBSOCKET_DISCONNECT",
                result="SUCCESS",
                room=room,
                total_connections=len(self.active_connections)
            )
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """
        Send message to a specific client.
        
        Args:
            message: Message dict to send
            websocket: Target WebSocket connection
        """
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.log_step(
                step="WEBSOCKET_SEND_ERROR",
                result="ERROR",
                error=str(e),
                error_type=type(e).__name__
            )
            self.disconnect(websocket)
    
    async def broadcast_to_room(self, message: dict, room: str, account_id: str = None):
        """
        Broadcast message to all clients in a room.
        
        Args:
            message: Message dict to broadcast
            room: Room name
            account_id: Optional account ID filter
        """
        if room not in self.rooms:
            return
        
        disconnected = []
        websocket_count = 0
        for websocket in self.rooms[room]:
            # Filter by account_id if provided
            # If connection has no account_id (None), it receives all messages
            # If connection has account_id, it only receives messages for that account_id
            if account_id:
                conn_info = self.active_connections.get(websocket, {})
                conn_account_id = conn_info.get("account_id")
                # Skip only if connection has account_id and it doesn't match
                # If conn_account_id is None, connection receives all messages
                if conn_account_id is not None and conn_account_id != account_id:
                    continue
            
            websocket_count += 1
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.log_step(
                    step="WEBSOCKET_BROADCAST_ERROR",
                    result="ERROR",
                    error=str(e),
                    room=room
                )
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
    
    async def broadcast(self, message: dict):
        """
        Broadcast message to all connected clients.
        
        Args:
            message: Message dict to broadcast
        """
        disconnected = []
        for websocket in list(self.active_connections.keys()):
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.log_step(
                    step="WEBSOCKET_BROADCAST_ERROR",
                    result="ERROR",
                    error=str(e)
                )
                disconnected.append(websocket)
        
        # Clean up disconnected clients
        for ws in disconnected:
            self.disconnect(ws)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return len(self.active_connections)
    
    def get_room_count(self, room: str) -> int:
        """Get number of connections in a room."""
        return len(self.rooms.get(room, set()))


# Global connection manager instance
manager = ConnectionManager()
