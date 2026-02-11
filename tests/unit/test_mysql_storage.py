"""
Unit tests for MySQL job storage.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform
from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.exceptions import StorageError


class TestMySQLJobStorage:
    """Test MySQL job storage operations."""
    
    @pytest.fixture
    def mysql_config(self, mysql_config):
        """MySQL configuration."""
        return mysql_config
    
    @pytest.fixture
    def mock_logger(self, mock_logger):
        """Mock logger."""
        return mock_logger
    
    @pytest.fixture
    def storage(self, mysql_config, mock_logger):
        """Create storage instance."""
        return MySQLJobStorage(
            host=mysql_config["host"],
            port=mysql_config["port"],
            user=mysql_config["user"],
            password=mysql_config["password"],
            database=mysql_config["database"],
            charset=mysql_config["charset"],
            logger=mock_logger
        )
    
    def test_init(self, storage, mysql_config):
        """Test storage initialization."""
        assert storage.host == mysql_config["host"]
        assert storage.port == mysql_config["port"]
        assert storage.user == mysql_config["user"]
        assert storage.database == mysql_config["database"]
    
    def test_get_connection_success(self, storage):
        """Test successful connection."""
        with storage._get_connection() as conn:
            assert conn is not None
            # Test ping
            conn.ping(reconnect=False)
    
    def test_get_connection_failure(self):
        """Test connection failure handling."""
        storage = MySQLJobStorage(
            host="invalid_host",
            port=3306,
            user="invalid_user",
            password="invalid_pass",
            database="invalid_db"
        )
        
        with pytest.raises(StorageError):
            with storage._get_connection():
                pass
    
    def test_save_job(self, storage, mock_logger):
        """Test saving a job."""
        job = ScheduledJob(
            job_id="test_job_001",
            account_id="account_01",
            content="Test content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            status=JobStatus.SCHEDULED,
            platform=Platform.THREADS
        )
        
        try:
            storage.save_job(job)
            
            # Verify job was saved
            loaded_job = storage.get_job(job.job_id)
            assert loaded_job is not None
            assert loaded_job.job_id == job.job_id
            assert loaded_job.content == job.content
            assert loaded_job.account_id == job.account_id
            
            # Cleanup
            storage.delete_job(job.job_id)
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_get_job_not_found(self, storage):
        """Test getting non-existent job."""
        try:
            job = storage.get_job("non_existent_job")
            assert job is None
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_update_job_status(self, storage, mock_logger):
        """Test updating job status."""
        job = ScheduledJob(
            job_id="test_job_002",
            account_id="account_01",
            content="Test content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            status=JobStatus.SCHEDULED,
            platform=Platform.THREADS
        )
        
        try:
            # Save job
            storage.save_job(job)
            
            # Update status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            storage.update_job(job)
            
            # Verify update
            loaded_job = storage.get_job(job.job_id)
            assert loaded_job.status == JobStatus.RUNNING
            assert loaded_job.started_at is not None
            
            # Cleanup
            storage.delete_job(job.job_id)
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_load_jobs_by_status(self, storage, mock_logger):
        """Test loading jobs by status."""
        job = ScheduledJob(
            job_id="test_job_003",
            account_id="account_01",
            content="Test content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            status=JobStatus.SCHEDULED,
            platform=Platform.THREADS
        )
        
        try:
            # Save job
            storage.save_job(job)
            
            # Load scheduled jobs
            scheduled_jobs = storage.load_jobs_by_status(JobStatus.SCHEDULED)
            assert len(scheduled_jobs) > 0
            assert any(j.job_id == job.job_id for j in scheduled_jobs)
            
            # Cleanup
            storage.delete_job(job.job_id)
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_delete_job(self, storage, mock_logger):
        """Test deleting a job."""
        job = ScheduledJob(
            job_id="test_job_004",
            account_id="account_01",
            content="Test content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            status=JobStatus.SCHEDULED,
            platform=Platform.THREADS
        )
        
        try:
            # Save job
            storage.save_job(job)
            
            # Delete job
            deleted = storage.delete_job(job.job_id)
            assert deleted is True
            
            # Verify deletion
            loaded_job = storage.get_job(job.job_id)
            assert loaded_job is None
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_get_ready_jobs(self, storage, mock_logger):
        """Test getting ready jobs."""
        # Create job scheduled for past (ready)
        past_job = ScheduledJob(
            job_id="test_job_005",
            account_id="account_01",
            content="Test content",
            scheduled_time=datetime.now() - timedelta(minutes=5),
            priority=JobPriority.NORMAL,
            status=JobStatus.SCHEDULED,
            platform=Platform.THREADS
        )
        
        # Create job scheduled for future (not ready)
        future_job = ScheduledJob(
            job_id="test_job_006",
            account_id="account_01",
            content="Test content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            status=JobStatus.SCHEDULED,
            platform=Platform.THREADS
        )
        
        try:
            # Save both jobs
            storage.save_job(past_job)
            storage.save_job(future_job)
            
            # Get ready jobs
            ready_jobs = storage.get_ready_jobs()
            assert len(ready_jobs) > 0
            assert any(j.job_id == past_job.job_id for j in ready_jobs)
            assert not any(j.job_id == future_job.job_id for j in ready_jobs)
            
            # Cleanup
            storage.delete_job(past_job.job_id)
            storage.delete_job(future_job.job_id)
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
