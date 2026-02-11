"""
Unit tests for JobsService.
"""

# Standard library
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Third-party
import pytest

# Local
from backend.app.modules.jobs.services.jobs_service import JobsService
from backend.app.modules.jobs.repositories.jobs_repository import JobsRepository
from backend.app.core.exceptions import ValidationError, NotFoundError
from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform


@pytest.fixture
def mock_repository():
    """Create mock repository."""
    return Mock(spec=JobsRepository)


@pytest.fixture
def jobs_service(mock_repository):
    """Create JobsService with mock repository."""
    return JobsService(repository=mock_repository)


@pytest.fixture
def sample_job():
    """Create sample ScheduledJob."""
    job = Mock(spec=ScheduledJob)
    job.job_id = "job_001"
    job.account_id = "account_001"
    job.status = JobStatus.PENDING
    job.scheduled_time = datetime.now() + timedelta(hours=1)
    return job


class TestJobsService:
    """Test JobsService."""
    
    def test_get_all_jobs_success(self, jobs_service, mock_repository, sample_job):
        """Test get_all_jobs success."""
        # Arrange
        mock_repository.get_all.return_value = [sample_job]
        with patch('backend.app.modules.jobs.services.jobs_service.serialize_job') as mock_serialize:
            mock_serialize.return_value = {"job_id": "job_001", "status": "pending"}
            
            # Act
            result = jobs_service.get_all_jobs(account_id="account_001", reload=False)
            
            # Assert
            assert len(result) == 1
            assert result[0]["job_id"] == "job_001"
            mock_repository.get_all.assert_called_once()
    
    def test_get_job_by_id_success(self, jobs_service, mock_repository, sample_job):
        """Test get_job_by_id success."""
        # Arrange
        mock_repository.get_by_id.return_value = sample_job
        with patch('backend.app.modules.jobs.services.jobs_service.serialize_job') as mock_serialize:
            mock_serialize.return_value = {"job_id": "job_001"}
            
            # Act
            result = jobs_service.get_job_by_id("job_001")
            
            # Assert
            assert result is not None
            assert result["job_id"] == "job_001"
            mock_repository.get_by_id.assert_called_once_with("job_001")
    
    def test_get_job_by_id_not_found(self, jobs_service, mock_repository):
        """Test get_job_by_id when job not found."""
        # Arrange
        mock_repository.get_by_id.return_value = None
        
        # Act
        result = jobs_service.get_job_by_id("job_001")
        
        # Assert
        assert result is None
    
    def test_create_job_validation_error(self, jobs_service):
        """Test create_job with validation error."""
        # Act & Assert
        with pytest.raises(ValidationError):
            jobs_service.create_job(
                account_id="",  # Invalid
                content="test",
                scheduled_time="2026-01-25T10:00:00",
                priority="NORMAL",
                platform="THREADS"
            )
    
    def test_create_job_success(self, jobs_service, mock_repository, sample_job):
        """Test create_job success."""
        # Arrange
        mock_repository.create.return_value = sample_job
        with patch.object(jobs_service, '_check_safety_guard'):
            with patch.object(jobs_service, '_sync_with_active_scheduler'):
                # Act
                result = jobs_service.create_job(
                    account_id="account_001",
                    content="test content",
                    scheduled_time="2026-01-25T10:00:00",
                    priority="NORMAL",
                    platform="THREADS"
                )
                
                # Assert
                assert result == "job_001"
                mock_repository.create.assert_called_once()
    
    def test_delete_job_success(self, jobs_service, mock_repository):
        """Test delete_job success."""
        # Arrange
        mock_repository.delete.return_value = True
        
        # Act
        result = jobs_service.delete_job("job_001")
        
        # Assert
        assert result is True
        mock_repository.delete.assert_called_once_with("job_001")
    
    def test_delete_job_not_found(self, jobs_service, mock_repository):
        """Test delete_job when job not found."""
        # Arrange
        mock_repository.delete.return_value = False
        
        # Act
        result = jobs_service.delete_job("job_001")
        
        # Assert
        assert result is False
    
    def test_get_stats(self, jobs_service, mock_repository, sample_job):
        """Test get_stats."""
        # Arrange
        completed_job = Mock(spec=ScheduledJob)
        completed_job.status = JobStatus.COMPLETED
        completed_job.completed_at = datetime.now()
        completed_job.account_id = "account_001"
        
        mock_repository.get_all.return_value = [sample_job, completed_job]
        
        # Act
        result = jobs_service.get_stats(account_id="account_001")
        
        # Assert
        assert result["total"] == 2
        assert result["completed"] == 1
        assert "success_rate" in result
