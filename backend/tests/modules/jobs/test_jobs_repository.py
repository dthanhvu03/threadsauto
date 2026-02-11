"""
Integration tests for JobsRepository.
"""

# Standard library
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta

# Third-party
import pytest

# Local
from backend.app.modules.jobs.repositories.jobs_repository import JobsRepository
from services.scheduler import Scheduler
from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform
from services.exceptions import JobNotFoundError


@pytest.fixture
def mock_scheduler():
    """Create mock scheduler."""
    scheduler = Mock(spec=Scheduler)
    scheduler.jobs = {}
    scheduler.list_jobs = Mock(return_value=[])
    scheduler.add_job = Mock(return_value="job_001")
    scheduler.remove_job = Mock()
    scheduler.reload_jobs = Mock()
    scheduler._load_jobs = Mock()
    scheduler.storage = Mock()
    scheduler.storage.load_jobs = Mock(return_value={})
    return scheduler


@pytest.fixture
def jobs_repository(mock_scheduler):
    """Create JobsRepository with mock scheduler."""
    return JobsRepository(scheduler=mock_scheduler)


class TestJobsRepository:
    """Test JobsRepository."""
    
    def test_get_by_id_found(self, jobs_repository, mock_scheduler):
        """Test get_by_id when job found."""
        # Arrange
        job = Mock(spec=ScheduledJob)
        job.job_id = "job_001"
        mock_scheduler.jobs = {"job_001": job}
        
        # Act
        result = jobs_repository.get_by_id("job_001")
        
        # Assert
        assert result is not None
        assert result.job_id == "job_001"
    
    def test_get_by_id_not_found(self, jobs_repository, mock_scheduler):
        """Test get_by_id when job not found."""
        # Arrange
        mock_scheduler.jobs = {}
        
        # Act
        result = jobs_repository.get_by_id("job_001")
        
        # Assert
        assert result is None
    
    def test_get_all_with_filters(self, jobs_repository, mock_scheduler):
        """Test get_all with filters."""
        # Arrange
        job1 = Mock(spec=ScheduledJob)
        job1.account_id = "account_001"
        job1.status = JobStatus.PENDING
        
        job2 = Mock(spec=ScheduledJob)
        job2.account_id = "account_002"
        job2.status = JobStatus.PENDING
        
        mock_scheduler.list_jobs.return_value = [job1, job2]
        
        # Act
        result = jobs_repository.get_all(filters={"account_id": "account_001"})
        
        # Assert
        assert len(result) == 2  # list_jobs returns both, filtering happens after
        mock_scheduler.list_jobs.assert_called_once_with(account_id="account_001")
    
    def test_create_job(self, jobs_repository, mock_scheduler):
        """Test create job."""
        # Arrange
        created_job = Mock(spec=ScheduledJob)
        created_job.job_id = "job_001"
        mock_scheduler.add_job.return_value = "job_001"
        mock_scheduler.jobs = {"job_001": created_job}
        
        # Act
        result = jobs_repository.create({
            "account_id": "account_001",
            "content": "test",
            "scheduled_time": datetime.now(),
            "priority": JobPriority.NORMAL,
            "platform": Platform.THREADS
        })
        
        # Assert
        assert result is not None
        assert result.job_id == "job_001"
        mock_scheduler.add_job.assert_called_once()
    
    def test_delete_job_success(self, jobs_repository, mock_scheduler):
        """Test delete job success."""
        # Arrange
        mock_scheduler.remove_job.return_value = None  # Doesn't raise
        
        # Act
        result = jobs_repository.delete("job_001")
        
        # Assert
        assert result is True
        mock_scheduler.remove_job.assert_called_once_with("job_001")
    
    def test_delete_job_not_found(self, jobs_repository, mock_scheduler):
        """Test delete job when not found."""
        # Arrange
        mock_scheduler.remove_job.side_effect = JobNotFoundError("Job not found")
        
        # Act
        result = jobs_repository.delete("job_001")
        
        # Assert
        assert result is False
