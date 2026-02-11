"""
Tests cho jobs API routes.
"""

# Standard library
import pytest
from unittest.mock import Mock

# Local
from backend.tests.conftest import client, mock_jobs_api


def test_list_jobs(client, mock_jobs_api):
    """Test GET /api/jobs."""
    mock_jobs_api.get_all_jobs.return_value = [
        {"job_id": "1", "account_id": "account_01", "status": "pending"}
    ]
    
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1


def test_get_job_by_id(client, mock_jobs_api):
    """Test GET /api/jobs/{job_id}."""
    mock_job = {"job_id": "1", "account_id": "account_01", "status": "pending"}
    mock_jobs_api.get_job_by_id.return_value = mock_job
    
    response = client.get("/api/jobs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["job_id"] == "1"


def test_get_job_not_found(client, mock_jobs_api):
    """Test GET /api/jobs/{job_id} với job không tồn tại."""
    mock_jobs_api.get_job_by_id.return_value = None
    
    response = client.get("/api/jobs/999")
    assert response.status_code == 404


def test_create_job(client, mock_jobs_api):
    """Test POST /api/jobs."""
    job_data = {
        "content": "Test content",
        "account_id": "account_01",
        "platform": "threads"
    }
    
    response = client.post("/api/jobs", json=job_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "job_id" in data["data"]


def test_delete_job(client, mock_jobs_api):
    """Test DELETE /api/jobs/{job_id}."""
    mock_jobs_api.get_job_by_id.return_value = {"job_id": "1"}
    
    response = client.delete("/api/jobs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
