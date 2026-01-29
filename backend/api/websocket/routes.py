"""
WebSocket routes.

WebSocket endpoints cho real-time updates.
"""

# Standard library
from fastapi import WebSocket, WebSocketDisconnect, Query
from typing import Optional

# Local
from backend.api.websocket.connection_manager import manager
from backend.api.websocket.messages import create_message, EVENT_PING, EVENT_PONG
from services.logger import StructuredLogger

logger = StructuredLogger(name="websocket_routes")


async def websocket_endpoint(
    websocket: WebSocket,
    room: str = Query("default", description="Room name (scheduler, dashboard, jobs)"),
    account_id: Optional[str] = Query(None, description="Account ID filter")
):
    """
    WebSocket endpoint for real-time updates.
    
    Args:
        websocket: WebSocket connection
        room: Room name for message filtering
        account_id: Optional account ID for filtering
    """
    await manager.connect(websocket, room=room, account_id=account_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle ping/pong for keepalive
            if data.get("type") == EVENT_PING:
                await manager.send_personal_message(
                    create_message(EVENT_PONG, {"message": "pong"}),
                    websocket
                )
                continue
            
            # Log received message
            logger.log_step(
                step="WEBSOCKET_MESSAGE_RECEIVED",
                result="SUCCESS",
                room=room,
                message_type=data.get("type")
            )
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.log_step(
            step="WEBSOCKET_DISCONNECT",
            result="SUCCESS",
            room=room
        )
    except Exception as e:
        logger.log_step(
            step="WEBSOCKET_ERROR",
            result="ERROR",
            error=str(e),
            error_type=type(e).__name__,
            room=room
        )
        manager.disconnect(websocket)
