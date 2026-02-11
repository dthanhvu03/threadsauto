"""
Unit tests for Excel storage.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from services.storage.excel_storage import ExcelStorage
from services.exceptions import StorageError


class TestExcelStorage:
    """Test Excel storage operations."""
    
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
        return ExcelStorage(
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
        assert storage.database == mysql_config["database"]
        assert storage.lock_timeout_minutes == 10
    
    def test_save_processed_file(self, storage, mock_logger):
        """Test saving processed file."""
        try:
            storage.save_processed_file(
                file_hash="test_hash_001",
                file_name="test_file.xlsx",
                account_id="account_01",
                total_jobs=10,
                scheduled_jobs=8,
                immediate_jobs=2,
                success_count=10,
                failed_count=0
            )
            
            # Verify save
            files = storage.load_processed_files()
            assert "test_hash_001" in files
            assert files["test_hash_001"]["file_name"] == "test_file.xlsx"
            assert files["test_hash_001"]["total_jobs"] == 10
            
            # Cleanup
            storage.remove_processed_file("test_hash_001")
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_save_processed_file_invalid_input(self, storage):
        """Test saving with invalid input."""
        with pytest.raises(ValueError, match="Invalid file_hash"):
            storage.save_processed_file(
                file_hash="",  # Empty
                file_name="test.xlsx",
                account_id="account_01",
                total_jobs=10,
                scheduled_jobs=8,
                immediate_jobs=2,
                success_count=10,
                failed_count=0
            )
        
        with pytest.raises(ValueError, match="Invalid total_jobs"):
            storage.save_processed_file(
                file_hash="test_hash",
                file_name="test.xlsx",
                account_id="account_01",
                total_jobs=-1,  # Negative
                scheduled_jobs=8,
                immediate_jobs=2,
                success_count=10,
                failed_count=0
            )
    
    def test_load_processed_files(self, storage, mock_logger):
        """Test loading processed files."""
        try:
            # Save a test file
            storage.save_processed_file(
                file_hash="test_hash_002",
                file_name="test_file2.xlsx",
                account_id="account_01",
                total_jobs=5,
                scheduled_jobs=3,
                immediate_jobs=2,
                success_count=5,
                failed_count=0
            )
            
            # Load files
            files = storage.load_processed_files()
            assert isinstance(files, dict)
            assert "test_hash_002" in files
            
            # Cleanup
            storage.remove_processed_file("test_hash_002")
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_remove_processed_file(self, storage, mock_logger):
        """Test removing processed file."""
        try:
            # Save file
            storage.save_processed_file(
                file_hash="test_hash_003",
                file_name="test_file3.xlsx",
                account_id="account_01",
                total_jobs=5,
                scheduled_jobs=3,
                immediate_jobs=2,
                success_count=5,
                failed_count=0
            )
            
            # Remove file
            removed = storage.remove_processed_file("test_hash_003")
            assert removed is True
            
            # Verify removal
            files = storage.load_processed_files()
            assert "test_hash_003" not in files
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_set_processing_lock(self, storage, mock_logger):
        """Test setting processing lock."""
        try:
            # Set lock
            locked = storage.set_processing_lock(
                file_hash="test_lock_001",
                file_name="test_file.xlsx"
            )
            assert locked is True
            
            # Try to lock again (should fail)
            locked_again = storage.set_processing_lock(
                file_hash="test_lock_001",
                file_name="test_file.xlsx"
            )
            assert locked_again is False
            
            # Release lock
            storage.release_processing_lock("test_lock_001")
            
            # Now should be able to lock again
            locked_after_release = storage.set_processing_lock(
                file_hash="test_lock_001",
                file_name="test_file.xlsx"
            )
            assert locked_after_release is True
            
            # Cleanup
            storage.release_processing_lock("test_lock_001")
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_set_processing_lock_invalid_input(self, storage):
        """Test setting lock with invalid input."""
        with pytest.raises(ValueError, match="Invalid file_hash"):
            storage.set_processing_lock(
                file_hash="",  # Empty
                file_name="test.xlsx"
            )
    
    def test_get_processing_files(self, storage, mock_logger):
        """Test getting processing files."""
        try:
            # Set a lock
            storage.set_processing_lock(
                file_hash="test_lock_002",
                file_name="test_file2.xlsx"
            )
            
            # Get processing files
            processing = storage.get_processing_files()
            assert isinstance(processing, dict)
            assert "test_lock_002" in processing
            
            # Cleanup
            storage.release_processing_lock("test_lock_002")
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_cleanup_expired_locks(self, storage, mock_logger):
        """Test cleanup of expired locks."""
        try:
            # Create an expired lock (by setting timeout to 0)
            storage.lock_timeout_minutes = 0
            
            # Set lock
            storage.set_processing_lock(
                file_hash="test_expired_lock",
                file_name="test_file.xlsx"
            )
            
            # Wait a moment
            import time
            time.sleep(1)
            
            # Cleanup should remove expired lock
            storage._cleanup_expired_locks()
            
            # Lock should be gone
            processing = storage.get_processing_files()
            assert "test_expired_lock" not in processing
            
            # Reset timeout
            storage.lock_timeout_minutes = 10
        except StorageError as e:
            pytest.skip(f"Database not available: {e}")
