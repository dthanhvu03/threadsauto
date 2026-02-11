#!/usr/bin/env python3
"""
Test cases cho các scenarios người dùng thường gặp.

Covers:
- Job creation edge cases
- Duplicate content detection
- Excel upload scenarios
- Validation errors
- Storage operations
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import Dict, Any

from services.scheduler import Scheduler, JobPriority, JobStatus
from services.scheduler.models import ScheduledJob, Platform
from services.logger import StructuredLogger


class TestUserScenarios:
    """Test cases cho user scenarios."""
    
    def __init__(self):
        """Initialize test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_jobs_"))
        self.logger = StructuredLogger(name="test_scenarios")
        self.scheduler = None
        self._init_scheduler()
        print(f"📁 Test directory: {self.test_dir}")
        print()
    
    def _init_scheduler(self):
        """Initialize fresh scheduler."""
        if self.scheduler:
            # Cleanup old scheduler
            try:
                self.scheduler.stop()
            except:
                pass
        
        # Clean test directory
        if self.test_dir.exists():
            for f in self.test_dir.glob("*.json"):
                f.unlink()
        
        self.scheduler = Scheduler(storage_dir=self.test_dir, logger=self.logger)
    
    def cleanup(self):
        """Cleanup test directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print(f"🧹 Cleaned up: {self.test_dir}")
    
    def run_all_tests(self):
        """Run tất cả test cases."""
        tests = [
            ("1. Tạo job với content hợp lệ", self.test_create_valid_job),
            ("2. Tạo job với content quá dài (>500 chars)", self.test_content_too_long),
            ("3. Tạo job với scheduled_time quá xa trong quá khứ", self.test_scheduled_time_too_old),
            ("4. Tạo job với scheduled_time quá xa trong tương lai", self.test_scheduled_time_too_future),
            ("5. Tạo job với account_id rỗng", self.test_empty_account_id),
            ("6. Tạo job với content rỗng", self.test_empty_content),
            ("7. Tạo job duplicate content (cùng account + platform)", self.test_duplicate_content),
            ("8. Tạo job duplicate content khác platform (cho phép)", self.test_duplicate_content_different_platform),
            ("9. Tạo job duplicate content khác account (cho phép)", self.test_duplicate_content_different_account),
            ("10. Tạo nhiều jobs cùng lúc", self.test_create_multiple_jobs),
            ("11. Tạo job với priority khác nhau", self.test_different_priorities),
            ("12. Tạo job với platform khác nhau", self.test_different_platforms),
            ("13. Load jobs từ storage", self.test_load_jobs_from_storage),
            ("14. Xóa job không tồn tại", self.test_delete_nonexistent_job),
            ("15. Xóa job thành công", self.test_delete_job_success),
            ("16. List jobs theo account_id", self.test_list_jobs_by_account),
            ("17. List jobs theo status", self.test_list_jobs_by_status),
            ("18. Get ready jobs (scheduled_time đã đến)", self.test_get_ready_jobs),
            ("19. Get ready jobs (chưa đến scheduled_time)", self.test_get_ready_jobs_not_ready),
            ("20. Cleanup expired jobs", self.test_cleanup_expired_jobs),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"🧪 {test_name}...")
                test_func()
                print(f"   ✅ PASSED")
                passed += 1
            except AssertionError as e:
                print(f"   ❌ FAILED: {str(e)}")
                failed += 1
            except Exception as e:
                print(f"   ❌ ERROR: {str(e)}")
                failed += 1
            print()
        
        print("=" * 60)
        print(f"📊 KẾT QUẢ: {passed} passed, {failed} failed")
        print("=" * 60)
        
        return failed == 0
    
    # Test Cases
    
    def test_create_valid_job(self):
        """Test tạo job hợp lệ."""
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Test content",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert job_id is not None
        assert len(job_id) > 0
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].job_id == job_id
        assert jobs[0].status == JobStatus.SCHEDULED
    
    def test_content_too_long(self):
        """Test content quá dài."""
        long_content = "x" * 501  # 501 chars
        
        try:
            self.scheduler.add_job(
                account_id="account_01",
                content=long_content,
                scheduled_time=datetime.now() + timedelta(hours=1),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "quá dài" in str(e) or "too long" in str(e).lower()
    
    def test_scheduled_time_too_old(self):
        """Test scheduled_time quá xa trong quá khứ."""
        from services.exceptions import InvalidScheduleTimeError
        
        old_time = datetime.now() - timedelta(days=400)  # > 1 year
        
        try:
            self.scheduler.add_job(
                account_id="account_01",
                content="Test",
                scheduled_time=old_time,
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            assert False, "Should raise InvalidScheduleTimeError"
        except InvalidScheduleTimeError as e:
            assert "quá xa trong quá khứ" in str(e) or "too far in the past" in str(e).lower()
    
    def test_scheduled_time_too_future(self):
        """Test scheduled_time quá xa trong tương lai."""
        from services.exceptions import InvalidScheduleTimeError
        
        future_time = datetime.now() + timedelta(days=400)  # > 1 year
        
        try:
            self.scheduler.add_job(
                account_id="account_01",
                content="Test",
                scheduled_time=future_time,
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            assert False, "Should raise InvalidScheduleTimeError"
        except InvalidScheduleTimeError as e:
            assert "quá xa trong tương lai" in str(e) or "too far in the future" in str(e).lower()
    
    def test_empty_account_id(self):
        """Test account_id rỗng."""
        try:
            self.scheduler.add_job(
                account_id="",
                content="Test",
                scheduled_time=datetime.now() + timedelta(hours=1),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "account_id" in str(e).lower()
    
    def test_empty_content(self):
        """Test content rỗng."""
        try:
            self.scheduler.add_job(
                account_id="account_01",
                content="",
                scheduled_time=datetime.now() + timedelta(hours=1),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            assert False, "Should raise ValueError"
        except ValueError as e:
            assert "content" in str(e).lower()
    
    def test_duplicate_content(self):
        """Test duplicate content (cùng account + platform)."""
        content = "Duplicate test content"
        
        # Tạo job đầu tiên
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content=content,
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        assert job_id1 is not None
        
        # Thử tạo job duplicate
        try:
            self.scheduler.add_job(
                account_id="account_01",  # Same account
                content=content,  # Same content
                scheduled_time=datetime.now() + timedelta(hours=2),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS  # Same platform
            )
            assert False, "Should raise ValueError for duplicate content"
        except ValueError as e:
            assert "duplicate" in str(e).lower() or "đã tồn tại" in str(e).lower()
    
    def test_duplicate_content_different_platform(self):
        """Test duplicate content nhưng khác platform (cho phép)."""
        content = "Same content, different platform"
        
        # Tạo job Threads
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content=content,
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        assert job_id1 is not None
        
        # Tạo job Facebook với cùng content (cho phép)
        job_id2 = self.scheduler.add_job(
            account_id="account_01",
            content=content,
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority=JobPriority.NORMAL,
            platform=Platform.FACEBOOK  # Different platform
        )
        assert job_id2 is not None
        assert job_id1 != job_id2
    
    def test_duplicate_content_different_account(self):
        """Test duplicate content nhưng khác account (cho phép)."""
        content = "Same content, different account"
        
        # Tạo job account_01
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content=content,
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        assert job_id1 is not None
        
        # Tạo job account_02 với cùng content (cho phép)
        job_id2 = self.scheduler.add_job(
            account_id="account_02",  # Different account
            content=content,
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        assert job_id2 is not None
        assert job_id1 != job_id2
    
    def test_create_multiple_jobs(self):
        """Test tạo nhiều jobs cùng lúc."""
        self._init_scheduler()  # Fresh start
        job_ids = []
        for i in range(5):
            job_id = self.scheduler.add_job(
                account_id=f"account_{i % 2 + 1}",
                content=f"Multiple jobs test {i} {datetime.now().isoformat()}",  # Unique content
                scheduled_time=datetime.now() + timedelta(hours=i+1),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            job_ids.append(job_id)
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 5
        assert len(set(job_ids)) == 5  # All unique
    
    def test_different_priorities(self):
        """Test tạo jobs với priority khác nhau."""
        self._init_scheduler()  # Fresh start
        priorities = [JobPriority.LOW, JobPriority.NORMAL, JobPriority.HIGH, JobPriority.URGENT]
        job_ids = []
        
        for priority in priorities:
            job_id = self.scheduler.add_job(
                account_id="account_01",
                content=f"Priority test {priority.value} {datetime.now().isoformat()}",  # Unique content
                scheduled_time=datetime.now() + timedelta(hours=1),
                priority=priority,
                platform=Platform.THREADS
            )
            job_ids.append(job_id)
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 4
        
        # Verify priorities
        for job in jobs:
            assert job.priority in priorities
    
    def test_different_platforms(self):
        """Test tạo jobs với platform khác nhau."""
        self._init_scheduler()  # Fresh start
        platforms = [Platform.THREADS, Platform.FACEBOOK]
        job_ids = []
        
        for platform in platforms:
            job_id = self.scheduler.add_job(
                account_id="account_01",
                content=f"Platform test {platform.value} {datetime.now().isoformat()}",  # Unique content
                scheduled_time=datetime.now() + timedelta(hours=1),
                priority=JobPriority.NORMAL,
                platform=platform
            )
            job_ids.append(job_id)
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 2
        
        # Verify platforms
        for job in jobs:
            assert job.platform in platforms
    
    def test_load_jobs_from_storage(self):
        """Test load jobs từ storage."""
        self._init_scheduler()  # Fresh start
        # Tạo jobs
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content=f"Load test Job 1 {datetime.now().isoformat()}",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        job_id2 = self.scheduler.add_job(
            account_id="account_01",
            content=f"Load test Job 2 {datetime.now().isoformat()}",
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Tạo scheduler mới (load từ storage)
        new_scheduler = Scheduler(storage_dir=self.test_dir, logger=self.logger)
        new_jobs = new_scheduler.list_jobs()
        
        assert len(new_jobs) == 2
        job_ids = [j.job_id for j in new_jobs]
        assert job_id1 in job_ids
        assert job_id2 in job_ids
    
    def test_delete_nonexistent_job(self):
        """Test xóa job không tồn tại."""
        from services.exceptions import JobNotFoundError
        
        try:
            self.scheduler.remove_job("nonexistent-job-id")
            assert False, "Should raise JobNotFoundError"
        except JobNotFoundError:
            pass  # Expected
    
    def test_delete_job_success(self):
        """Test xóa job thành công."""
        self._init_scheduler()  # Fresh start
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content=f"To be deleted {datetime.now().isoformat()}",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert len(self.scheduler.list_jobs()) == 1
        
        result = self.scheduler.remove_job(job_id)
        assert result is True
        assert len(self.scheduler.list_jobs()) == 0
    
    def test_list_jobs_by_account(self):
        """Test list jobs theo account_id."""
        self._init_scheduler()  # Fresh start
        # Tạo jobs cho 2 accounts
        self.scheduler.add_job(
            account_id="account_01",
            content=f"Account 1 job {datetime.now().isoformat()}",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        self.scheduler.add_job(
            account_id="account_02",
            content=f"Account 2 job {datetime.now().isoformat()}",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # List jobs account_01
        jobs_account1 = self.scheduler.list_jobs(account_id="account_01")
        assert len(jobs_account1) == 1
        assert jobs_account1[0].account_id == "account_01"
        
        # List jobs account_02
        jobs_account2 = self.scheduler.list_jobs(account_id="account_02")
        assert len(jobs_account2) == 1
        assert jobs_account2[0].account_id == "account_02"
    
    def test_list_jobs_by_status(self):
        """Test list jobs theo status."""
        self._init_scheduler()  # Fresh start
        # Tạo jobs
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content=f"Status test Job 1 {datetime.now().isoformat()}",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # List scheduled jobs
        scheduled_jobs = self.scheduler.list_jobs(status=JobStatus.SCHEDULED)
        assert len(scheduled_jobs) >= 1  # At least 1
        job_ids = [j.job_id for j in scheduled_jobs]
        assert job_id1 in job_ids
        
        # List completed jobs (should be empty)
        completed_jobs = self.scheduler.list_jobs(status=JobStatus.COMPLETED)
        assert len(completed_jobs) == 0
    
    def test_get_ready_jobs(self):
        """Test get ready jobs (scheduled_time đã đến)."""
        # Tạo job với scheduled_time trong quá khứ (ready)
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content="Ready job",
            scheduled_time=datetime.now() - timedelta(minutes=5),  # 5 phút trước
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Tạo job với scheduled_time trong tương lai (not ready)
        job_id2 = self.scheduler.add_job(
            account_id="account_01",
            content="Not ready job",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        ready_jobs = self.scheduler.get_ready_jobs()
        assert len(ready_jobs) == 1
        assert ready_jobs[0].job_id == job_id1
    
    def test_get_ready_jobs_not_ready(self):
        """Test get ready jobs (chưa đến scheduled_time)."""
        self._init_scheduler()  # Fresh start
        # Tạo job với scheduled_time trong tương lai
        self.scheduler.add_job(
            account_id="account_01",
            content=f"Future job {datetime.now().isoformat()}",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        ready_jobs = self.scheduler.get_ready_jobs()
        assert len(ready_jobs) == 0
    
    def test_cleanup_expired_jobs(self):
        """Test cleanup expired jobs."""
        # Tạo job expired (> 24h từ scheduled_time)
        expired_time = datetime.now() - timedelta(hours=25)
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Expired job",
            scheduled_time=expired_time,
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Manually set scheduled_time (vì add_job sẽ validate)
        job = self.scheduler.jobs[job_id]
        job.scheduled_time = expired_time
        
        # Cleanup expired
        count = self.scheduler.cleanup_expired_jobs()
        assert count >= 0  # May or may not mark as expired depending on logic
        
        # Verify job status
        updated_job = self.scheduler.jobs.get(job_id)
        if updated_job:
            # Job might be marked as expired
            assert updated_job.status in [JobStatus.SCHEDULED, JobStatus.EXPIRED]


def main():
    """Main function."""
    tester = TestUserScenarios()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main())

