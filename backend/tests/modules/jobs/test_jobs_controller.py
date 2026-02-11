"""
Unit tests for JobsController.
"""

# Standard library
from unittest.mock import Mock, patch

# Third-party
import pytest

# Local
from backend.app.modules.jobs.controllers import JobsController
from backend.app.modules.jobs.services.jobs_service import JobsService
from backend.app.modules.jobs.schemas import JobCreate
from backend.app.core.exceptions import NotFoundError, ValidationError


@pytest.fixture
def mock_service():
    """Create mock service."""
    return Mock(spec=JobsService)


@pytest.fixture
def jobs_controller(mock_service):
    """Create JobsController with mock service."""
    return JobsController(service=mock_service)


class TestJobsController:
    """Test JobsController."""
    
    @pytest.mark.asyncio
    async def test_list_jobs_success(self, jobs_controller, mock_service):
        """Test list_jobs success."""
        # Arrange
        mock_service.get_all_jobs.return_value = [
            {"job_id": "job_001", "status": "pending"}
        ]
        
        # Act
        result = await jobs_controller.list_jobs(account_id="account_001")
        
        # Assert
        assert result["success"] is True
        assert len(result["data"]) == 1
        mock_service.get_all_jobs.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_job_success(self, jobs_controller, mock_service):
        """Test get_job success."""
        # Arrange
        mock_service.get_job_by_id.return_value = {"job_id": "job_001"}
        
        # Act
        result = await jobs_controller.get_job("job_001")
        
        # Assert
        assert result["success"] is True
        assert result["data"]["job_id"] == "job_001"
    
    @pytest.mark.asyncio
    async def test_get_job_not_found(self, jobs_controller, mock_service):
        """Test get_job when not found."""
        # Arrange
        mock_service.get_job_by_id.return_value = None
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await jobs_controller.get_job("job_001")
    
    @pytest.mark.asyncio
    async def test_create_job_success(self, jobs_controller, mock_service):
        """Test create_job success."""
        # Arrange
        mock_service.create_job.return_value = "job_001"
        job_data = JobCreate(
            account_id="account_001",
            content="test",
            scheduled_time="2026-01-25T10:00:00"
        )
        
        # Act
        result = await jobs_controller.create_job(job_data)
        
        # Assert
        assert result["success"] is True
        assert result["data"]["job_id"] == "job_001"
        mock_service.create_job.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_job_success(self, jobs_controller, mock_service):
        """Test delete_job success."""
        # Arrange
        mock_service.delete_job.return_value = True
        
        # Act
        result = await jobs_controller.delete_job("job_001")
        
        # Assert
        assert result["success"] is True
        mock_service.delete_job.assert_called_once_with("job_001")
    
    @pytest.mark.asyncio
    async def test_delete_job_not_found(self, jobs_controller, mock_service):
        """Test delete_job when not found."""
        # Arrange
        mock_service.delete_job.return_value = False
        
        # Act & Assert
        with pytest.raises(NotFoundError):
            await jobs_controller.delete_job("job_001")
