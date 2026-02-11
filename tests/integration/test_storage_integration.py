"""
Integration tests for storage operations.
"""

import pytest
from datetime import datetime, timedelta

from services.scheduler.storage.mysql_storage import MySQLJobStorage
from services.scheduler.models import ScheduledJob, JobStatus, JobPriority, Platform
from services.storage.excel_storage import ExcelStorage
from services.storage.accounts_storage import AccountStorage
from services.exceptions import StorageError


class TestStorageIntegration:
    """Integration tests for storage operations."""
    
    @pytest.fixture
    def mysql_config(self, mysql_config):
        """MySQL configuration."""
        return mysql_config
    
    def test_job_storage_workflow(self, mysql_config):
        """Test complete job storage workflow."""
        try:
            storage = MySQLJobStorage(
                host=mysql_config["host"],
                port=mysql_config["port"],
                user=mysql_config["user"],
                password=mysql_config["password"],
                database=mysql_config["database"]
            )
            
            # Create job
            job = ScheduledJob(
                job_id="integration_test_001",
                account_id="account_01",
                content="Integration test content",
                scheduled_time=datetime.now() + timedelta(hours=1),
                priority=JobPriority.NORMAL,
                status=JobStatus.SCHEDULED,
                platform=Platform.THREADS
            )
            
            # Save job
            storage.save_job(job)
            
            # Load job
            loaded_job = storage.get_job(job.job_id)
            assert loaded_job is not None
            assert loaded_job.job_id == job.job_id
            
            # Update job
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            storage.update_job(job)
            
            # Verify update
            updated_job = storage.get_job(job.job_id)
            assert updated_job.status == JobStatus.RUNNING
            
            # Complete job
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.thread_id = "thread_123"
            storage.update_job(job)
            
            # Verify completion
            completed_job = storage.get_job(job.job_id)
            assert completed_job.status == JobStatus.COMPLETED
            assert completed_job.thread_id == "thread_123"
            
            # Cleanup
            storage.delete_job(job.job_id)
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_excel_storage_workflow(self, mysql_config):
        """Test complete Excel storage workflow."""
        try:
            storage = ExcelStorage(
                host=mysql_config["host"],
                port=mysql_config["port"],
                user=mysql_config["user"],
                password=mysql_config["password"],
                database=mysql_config["database"]
            )
            
            file_hash = "integration_test_file"
            
            # Save processed file
            storage.save_processed_file(
                file_hash=file_hash,
                file_name="integration_test.xlsx",
                account_id="account_01",
                total_jobs=10,
                scheduled_jobs=8,
                immediate_jobs=2,
                success_count=10,
                failed_count=0
            )
            
            # Load processed files
            files = storage.load_processed_files()
            assert file_hash in files
            
            # Set processing lock
            locked = storage.set_processing_lock(file_hash, "integration_test.xlsx")
            assert locked is False  # Already exists as processed
            
            # Remove file
            removed = storage.remove_processed_file(file_hash)
            assert removed is True
            
            # Verify removal
            files_after = storage.load_processed_files()
            assert file_hash not in files_after
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
