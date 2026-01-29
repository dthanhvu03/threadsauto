"""
Module: services/websocket_logger.py

WebSocket logger wrapper cho realtime automation logging.

Wraps StructuredLogger và broadcast logs qua WebSocket để frontend
có thể hiển thị realtime automation steps.
"""

# Standard library
from typing import Optional, Dict, Any
from datetime import datetime

# Local
from services.logger import StructuredLogger
from utils.sanitize import (
    sanitize_data,
    sanitize_error,
    sanitize_kwargs,
    sanitize_status_message
)


class WebSocketLogger:
    """
    WebSocket logger wrapper cho realtime automation logging.
    
    Wraps StructuredLogger và broadcast logs qua WebSocket để
    frontend có thể hiển thị realtime automation steps.
    
    Attributes:
        logger: Underlying StructuredLogger instance
        room: WebSocket room name (default: "scheduler")
        account_id: Optional account ID for filtering
    """
    
    def __init__(
        self,
        logger: Optional[StructuredLogger] = None,
        room: str = "scheduler",
        account_id: Optional[str] = None
    ):
        """
        Khởi tạo WebSocket logger.
        
        Args:
            logger: StructuredLogger instance (tạo mới nếu None)
            room: WebSocket room name (default: "scheduler")
            account_id: Optional account ID for filtering
        """
        self.logger = logger or StructuredLogger(name="websocket_logger")
        self.room = room
        self.account_id = account_id
    
    def _get_manager(self):
        """Lazy import WebSocket manager to avoid circular dependencies."""
        try:
            from backend.api.websocket.connection_manager import manager
            return manager
        except ImportError:
            return None
    
    def _create_message(self, event_type: str, data: Any, account_id: Optional[str] = None) -> Dict:
        """Create WebSocket message."""
        try:
            from backend.api.websocket.messages import create_message
            return create_message(event_type, data, account_id)
        except ImportError:
            # Fallback if backend not available
            return {
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
                "account_id": account_id
            }
    
    async def _broadcast(
        self,
        event_type: str,
        data: Dict[str, Any],
        account_id: Optional[str] = None
    ) -> None:
        """
        Broadcast message qua WebSocket.
        
        Args:
            event_type: Event type (automation.step, automation.action, etc.)
            data: Message data
            account_id: Optional account ID (uses self.account_id if None)
        """
        try:
            manager = self._get_manager()
            if manager is None:
                # WebSocket not available, skip broadcast
                return
            
            # Use provided account_id or fallback to instance account_id
            target_account_id = account_id or self.account_id
            
            # Sanitize data trước khi tạo message
            sanitized_data = sanitize_data(data)
            
            # Create message với sanitized data
            message = self._create_message(
                event_type=event_type,
                data=sanitized_data,
                account_id=target_account_id
            )
            
            # Broadcast to room
            await manager.broadcast_to_room(
                message=message,
                room=self.room,
                account_id=target_account_id
            )
        except Exception as e:
            # Log error but don't break automation flow
            # Only log critical errors, not connection issues
            try:
                self.logger.log_step(
                    step="WEBSOCKET_BROADCAST",
                    result="WARNING",
                    error=f"Failed to broadcast: {str(e)}",
                    error_type=type(e).__name__
                )
            except Exception:
                pass  # Don't break if logging fails
    
    def log_step(
        self,
        step: str,
        result: str = "SUCCESS",
        time_ms: Optional[float] = None,
        error: Optional[str] = None,
        account_id: Optional[str] = None,
        job_id: Optional[str] = None,
        thread_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log automation step và broadcast qua WebSocket.
        
        Args:
            step: Step name (e.g., "CLICK_POST_BUTTON", "TYPE_CONTENT")
            result: Result (SUCCESS, FAILED, ERROR, WARNING, etc.)
            time_ms: Execution time in milliseconds
            error: Error message if failed
            account_id: Account ID (overrides instance account_id)
            job_id: Job ID
            thread_id: Thread ID
            **kwargs: Additional log fields
        """
        # Log to file via StructuredLogger
        self.logger.log_step(
            step=step,
            result=result,
            time_ms=time_ms,
            error=error,
            account_id=account_id or self.account_id,
            job_id=job_id,
            thread_id=thread_id,
            **kwargs
        )
        
        # Broadcast via WebSocket (async, but we can't await in sync method)
        # Strategy: Check if WebSocket connections exist, then try to schedule broadcast
        import asyncio
        try:
            from backend.api.websocket.messages import EVENT_AUTOMATION_STEP
        except ImportError:
            EVENT_AUTOMATION_STEP = "automation.step"
        
        # Sanitize kwargs trước khi thêm vào message_data
        sanitized_kwargs = sanitize_kwargs(kwargs) if kwargs else {}
        
        # Special sanitization for sensitive fields
        if "status_message" in sanitized_kwargs and isinstance(sanitized_kwargs["status_message"], str):
            sanitized_kwargs["status_message"] = sanitize_status_message(sanitized_kwargs["status_message"])
        if "metadata" in sanitized_kwargs and isinstance(sanitized_kwargs["metadata"], dict):
            sanitized_kwargs["metadata"] = sanitize_data(sanitized_kwargs["metadata"])
        
        # Sanitize error nếu có
        sanitized_error = sanitize_error(error) if error else None
        
        # Prepare message data với sanitized values
        message_data = {
            "step": step,
            "result": result,
            "time_ms": time_ms,
            "error": sanitized_error,
            "account_id": account_id or self.account_id,
            "job_id": job_id,
            "thread_id": thread_id,
            "timestamp": datetime.utcnow().isoformat(),
            **sanitized_kwargs
        }
        
        # Sanitize toàn bộ message_data trước khi broadcast
        message_data = sanitize_data(message_data)
        
        # Check if WebSocket manager has connections before trying to broadcast
        manager = self._get_manager()
        if manager is None:
            # WebSocket not available, skip silently
            return
        
        # Check if there are connections in the room
        try:
            room_count = manager.get_room_count(self.room)
            if room_count == 0:
                # No connections, skip broadcast
                return
        except Exception as e:
            # If get_room_count fails, still try to broadcast
            pass
        
        # Try to schedule broadcast in running event loop
        try:
            # Try to get running loop
            try:
                loop = asyncio.get_running_loop()
                # We're in async context - schedule as task
                asyncio.create_task(self._broadcast(
                    event_type=EVENT_AUTOMATION_STEP,
                    data=message_data,
                    account_id=account_id or self.account_id
                ))
                return  # Successfully scheduled
            except RuntimeError as e:
                # No running loop, try get_event_loop
                pass
            
            # Fallback: try get_event_loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Loop is running, schedule as task
                    asyncio.create_task(self._broadcast(
                        event_type=EVENT_AUTOMATION_STEP,
                        data=message_data,
                        account_id=account_id or self.account_id
                    ))
                    return  # Successfully scheduled
                else:
                    # Loop not running, try run_until_complete
                    loop.run_until_complete(self._broadcast(
                        event_type=EVENT_AUTOMATION_STEP,
                        data=message_data,
                        account_id=account_id or self.account_id
                    ))
                    return  # Successfully completed
            except RuntimeError:
                # No event loop available, skip WebSocket broadcast
                pass
                
        except Exception as e:
            # Log error but don't break automation flow
            # Only log if it's not a RuntimeError (expected when no loop)
            if not isinstance(e, RuntimeError):
                try:
                    self.logger.log_step(
                        step="WEBSOCKET_LOG_STEP",
                        result="WARNING",
                        error=f"Failed to schedule broadcast: {str(e)}",
                        error_type=type(e).__name__
                    )
                except Exception:
                    pass  # Don't break if logging fails
    
    async def log_action(
        self,
        action: str,
        status: str = "IN_PROGRESS",
        details: Optional[Dict[str, Any]] = None,
        account_id: Optional[str] = None,
        job_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log automation action và broadcast qua WebSocket.
        
        Args:
            action: Action name (e.g., "clicking_post_button", "typing_content")
            status: Status (IN_PROGRESS, COMPLETED, FAILED)
            details: Additional action details
            account_id: Account ID (overrides instance account_id)
            job_id: Job ID
            **kwargs: Additional log fields
        """
        # Log to file via StructuredLogger
        self.logger.log_step(
            step=f"ACTION_{action}",
            result=status,
            account_id=account_id or self.account_id,
            job_id=job_id,
            **kwargs
        )
        
        # Broadcast via WebSocket
        try:
            from backend.api.websocket.messages import EVENT_AUTOMATION_ACTION
        except ImportError:
            EVENT_AUTOMATION_ACTION = "automation.action"
        
        # Sanitize kwargs và details
        sanitized_kwargs = sanitize_kwargs(kwargs) if kwargs else {}
        sanitized_details = sanitize_data(details) if details else {}
        
        # Special sanitization for sensitive fields in details
        if "status_message" in sanitized_details and isinstance(sanitized_details["status_message"], str):
            sanitized_details["status_message"] = sanitize_status_message(sanitized_details["status_message"])
        
        await self._broadcast(
            event_type=EVENT_AUTOMATION_ACTION,
            data={
                "action": action,
                "status": status,
                "details": sanitized_details,
                "account_id": account_id or self.account_id,
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat(),
                **sanitized_kwargs
            },
            account_id=account_id or self.account_id
        )
    
    async def log_start(
        self,
        operation: str,
        account_id: Optional[str] = None,
        job_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log automation start và broadcast qua WebSocket.
        
        Args:
            operation: Operation name (e.g., "post_thread", "run_job")
            account_id: Account ID (overrides instance account_id)
            job_id: Job ID
            **kwargs: Additional log fields
        """
        try:
            from backend.api.websocket.messages import EVENT_AUTOMATION_START
        except ImportError:
            EVENT_AUTOMATION_START = "automation.start"
        
        await self._broadcast(
            event_type=EVENT_AUTOMATION_START,
            data={
                "operation": operation,
                "account_id": account_id or self.account_id,
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat(),
                **kwargs
            },
            account_id=account_id or self.account_id
        )
    
    async def log_complete(
        self,
        operation: str,
        success: bool = True,
        result: Optional[Dict[str, Any]] = None,
        account_id: Optional[str] = None,
        job_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log automation completion và broadcast qua WebSocket.
        
        Args:
            operation: Operation name
            success: Whether operation succeeded
            result: Result data
            account_id: Account ID (overrides instance account_id)
            job_id: Job ID
            **kwargs: Additional log fields
        """
        try:
            from backend.api.websocket.messages import EVENT_AUTOMATION_COMPLETE
        except ImportError:
            EVENT_AUTOMATION_COMPLETE = "automation.complete"
        
        # Sanitize kwargs và result
        sanitized_kwargs = sanitize_kwargs(kwargs) if kwargs else {}
        sanitized_result = sanitize_data(result) if result else {}
        
        await self._broadcast(
            event_type=EVENT_AUTOMATION_COMPLETE,
            data={
                "operation": operation,
                "success": success,
                "result": sanitized_result,
                "account_id": account_id or self.account_id,
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat(),
                **sanitized_kwargs
            },
            account_id=account_id or self.account_id
        )
    
    async def log_error(
        self,
        operation: str,
        error: str,
        error_type: Optional[str] = None,
        account_id: Optional[str] = None,
        job_id: Optional[str] = None,
        **kwargs
    ) -> None:
        """
        Log automation error và broadcast qua WebSocket.
        
        Args:
            operation: Operation name
            error: Error message
            error_type: Error type
            account_id: Account ID (overrides instance account_id)
            job_id: Job ID
            **kwargs: Additional log fields
        """
        try:
            from backend.api.websocket.messages import EVENT_AUTOMATION_ERROR
        except ImportError:
            EVENT_AUTOMATION_ERROR = "automation.error"
        
        # Sanitize kwargs và error
        sanitized_kwargs = sanitize_kwargs(kwargs) if kwargs else {}
        sanitized_error = sanitize_error(error) if error else None
        
        await self._broadcast(
            event_type=EVENT_AUTOMATION_ERROR,
            data={
                "operation": operation,
                "error": sanitized_error,
                "error_type": error_type,
                "account_id": account_id or self.account_id,
                "job_id": job_id,
                "timestamp": datetime.utcnow().isoformat(),
                **sanitized_kwargs
            },
            account_id=account_id or self.account_id
        )
    
    # Delegate other StructuredLogger methods
    def debug(self, message: str, **kwargs) -> None:
        """Delegate to StructuredLogger."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Delegate to StructuredLogger."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Delegate to StructuredLogger."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Delegate to StructuredLogger."""
        self.logger.error(message, error=error, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Delegate to StructuredLogger."""
        self.logger.critical(message, error=error, **kwargs)
