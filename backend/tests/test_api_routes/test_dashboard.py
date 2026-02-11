"""
Tests cho dashboard API routes.
"""

# Standard library
import pytest

# Local
from backend.tests.conftest import client, mock_jobs_api


def test_get_dashboard_stats(client, mock_jobs_api):
    """Test GET /api/dashboard/stats."""
    mock_jobs_api.get_all_jobs.return_value = [
        {"job_id": "1", "status": "pending"},
        {"job_id": "2", "status": "completed"},
        {"job_id": "3", "status": "completed"}
    ]
    
    response = client.get("/api/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "total_jobs" in data["data"]
    assert data["data"]["total_jobs"] == 3
    assert data["data"]["pending_jobs"] == 1
    assert data["data"]["completed_jobs"] == 2


def test_get_dashboard_metrics(client, mock_jobs_api):
    """Test GET /api/dashboard/metrics."""
    mock_jobs_api.get_all_jobs.return_value = [
        {"job_id": "1", "platform": "threads", "status": "pending"},
        {"job_id": "2", "platform": "threads", "status": "completed"},
        {"job_id": "3", "platform": "facebook", "status": "completed"}
    ]
    
    response = client.get("/api/dashboard/metrics")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "jobs_by_status" in data["data"]
    assert "jobs_by_platform" in data["data"]
