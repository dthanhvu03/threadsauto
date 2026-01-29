"""
WebSocket message types và helpers.
"""

# Standard library
from typing import Dict, Any, Optional
from datetime import datetime


def create_message(event_type: str, data: Any, account_id: Optional[str] = None) -> Dict:
    """
    Create a standardized WebSocket message.
    
    Args:
        event_type: Event type (e.g., "scheduler.status", "job.created")
        data: Message data
        account_id: Optional account ID
    
    Returns:
        Message dict
    """
    return {
        "type": event_type,
        "data": data,
        "timestamp": datetime.utcnow().isoformat(),
        "account_id": account_id
    }


# Event types
EVENT_SCHEDULER_STATUS = "scheduler.status"
EVENT_JOB_CREATED = "job.created"
EVENT_JOB_UPDATED = "job.updated"
EVENT_JOB_COMPLETED = "job.completed"
EVENT_DASHBOARD_STATS = "dashboard.stats"
EVENT_ERROR = "error"
EVENT_PING = "ping"
EVENT_PONG = "pong"

# Automation event types
EVENT_AUTOMATION_STEP = "automation.step"
EVENT_AUTOMATION_ACTION = "automation.action"
EVENT_AUTOMATION_START = "automation.start"
EVENT_AUTOMATION_COMPLETE = "automation.complete"
EVENT_AUTOMATION_ERROR = "automation.error"