"""
Pytest configuration và fixtures.
"""

# Standard library
import pytest
from unittest.mock import Mock, patch

# Third-party
from fastapi.testclient import TestClient

# Local
from backend.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_jobs_api():
    """Mock JobsAPI."""
    with patch('backend.api.dependencies.get_jobs_api') as mock:
        api = Mock()
        api.get_all_jobs.return_value = []
        api.get_job_by_id.return_value = None
        api.add_job.return_value = "job_123"
        api.delete_job.return_value = True
        mock.return_value = api
        yield api


@pytest.fixture
def mock_accounts_api():
    """Mock AccountsAPI."""
    with patch('backend.api.dependencies.get_accounts_api') as mock:
        api = Mock()
        api.get_all_accounts.return_value = []
        api.get_account_info.return_value = None
        mock.return_value = api
        yield api
