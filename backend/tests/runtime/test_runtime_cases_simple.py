#!/usr/bin/env python3
"""
Test cases đơn giản cho các scenarios runtime thường gặp.

Covers:
- Thêm job khi scheduler đang chạy
- Stop/Start scheduler
- Excel upload scenarios
"""

import sys
from pathlib import Path

# Add project root to path (two levels up from backend/tests/runtime/)
_project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_project_root))

import tempfile
import shutil
from datetime import datetime, timedelta

from services.scheduler import Scheduler, JobPriority, JobStatus
from services.scheduler.models import Platform
from services.logger import StructuredLogger


class TestRuntimeCasesSimple:
    """Test cases đơn giản cho runtime scenarios."""
    
    def __init__(self):
        """Initialize test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_runtime_"))
        self.logger = StructuredLogger(name="test_runtime_simple")
        self.scheduler = None
        self._init_scheduler()
        print(f"📁 Test directory: {self.test_dir}")
        print()
    
    def _init_scheduler(self):
        """Initialize fresh scheduler."""
        if self.scheduler:
            try:
                if self.scheduler.running:
                    # Just set running to False for cleanup
                    self.scheduler.running = False
            except:
                pass
        
        # Clean test directory
        if self.test_dir.exists():
            for f in self.test_dir.glob("*.json"):
                f.unlink()
        
        self.scheduler = Scheduler(storage_dir=self.test_dir, logger=self.logger)
    
    def cleanup(self):
        """Cleanup test directory."""
        if self.scheduler and self.scheduler.running:
            try:
                self.scheduler.running = False
            except:
                pass
        
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print(f"🧹 Cleaned up: {self.test_dir}")
    
    def run_all_tests(self):
        """Run tất cả test cases."""
        tests = [
            ("1. Thêm job khi scheduler chưa chạy", self.test_add_job_before_start),
            ("2. Thêm nhiều jobs (simulate Excel upload)", self.test_add_multiple_jobs_excel),
            ("3. Thêm job với scheduled_time trong quá khứ (ready)", self.test_add_ready_job),
            ("4. Thêm job với scheduled_time trong tương lai (not ready)", self.test_add_future_job),
            ("5. Thêm job duplicate khi scheduler chưa chạy", self.test_duplicate_before_start),
            ("6. Thêm job sau khi đã có jobs (simulate thêm Excel sau khi có jobs)", self.test_add_job_after_existing),
            ("7. Thêm job với priority khác nhau", self.test_add_jobs_different_priorities),
            ("8. Thêm job với platform khác nhau", self.test_add_jobs_different_platforms),
            ("9. Load jobs từ storage và thêm job mới", self.test_load_and_add),
            ("10. Thêm job, xóa job, thêm job mới", self.test_add_delete_add),
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
                import traceback
                traceback.print_exc()
                failed += 1
            finally:
                # Cleanup after each test
                self._init_scheduler()
            print()
        
        print("=" * 60)
        print(f"📊 KẾT QUẢ: {passed} passed, {failed} failed")
        print("=" * 60)
        
        return failed == 0
    
    # Test Cases
    
    def test_add_job_before_start(self):
        """Test thêm job trước khi start scheduler."""
        self._init_scheduler()
        
        # Thêm job khi scheduler chưa chạy
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Job before start",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert job_id is not None
        assert self.scheduler.running is False
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].job_id == job_id
        assert jobs[0].status == JobStatus.SCHEDULED
    
    def test_add_multiple_jobs_excel(self):
        """Test thêm nhiều jobs (simulate Excel upload)."""
        self._init_scheduler()
        
        # Simulate Excel upload - thêm nhiều jobs
        job_ids = []
        for i in range(10):
            job_id = self.scheduler.add_job(
                account_id="account_01",
                content=f"Excel job {i} {datetime.now().isoformat()}",
                scheduled_time=datetime.now() + timedelta(hours=i+1),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            job_ids.append(job_id)
        
        assert len(job_ids) == 10
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 10
        
        # Verify all unique
        assert len(set(job_ids)) == 10
    
    def test_add_ready_job(self):
        """Test thêm job với scheduled_time trong quá khứ (ready ngay)."""
        self._init_scheduler()
        
        # Thêm job ready ngay
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Ready job",
            scheduled_time=datetime.now() - timedelta(minutes=5),  # 5 phút trước
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 1
        
        # Check ready jobs
        ready_jobs = self.scheduler.get_ready_jobs()
        assert len(ready_jobs) == 1
        assert ready_jobs[0].job_id == job_id
    
    def test_add_future_job(self):
        """Test thêm job với scheduled_time trong tương lai (not ready)."""
        self._init_scheduler()
        
        # Thêm job chưa ready
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Future job",
            scheduled_time=datetime.now() + timedelta(hours=2),  # 2 giờ sau
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 1
        
        # Check ready jobs (should be empty)
        ready_jobs = self.scheduler.get_ready_jobs()
        assert len(ready_jobs) == 0  # Not ready yet
    
    def test_duplicate_before_start(self):
        """Test duplicate content khi scheduler chưa chạy."""
        self._init_scheduler()
        
        content = "Duplicate test content"
        
        # Tạo job đầu tiên
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content=content,
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Thử tạo duplicate
        try:
            self.scheduler.add_job(
                account_id="account_01",
                content=content,
                scheduled_time=datetime.now() + timedelta(hours=2),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            assert False, "Should raise ValueError for duplicate"
        except ValueError as e:
            assert "duplicate" in str(e).lower() or "đã tồn tại" in str(e).lower()
    
    def test_add_job_after_existing(self):
        """Test thêm job sau khi đã có jobs (simulate thêm Excel sau khi có jobs)."""
        self._init_scheduler()
        
        # Thêm jobs ban đầu
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content="Existing job 1",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        job_id2 = self.scheduler.add_job(
            account_id="account_01",
            content="Existing job 2",
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert len(self.scheduler.list_jobs()) == 2
        
        # Simulate thêm Excel sau đó
        excel_job_ids = []
        for i in range(5):
            job_id = self.scheduler.add_job(
                account_id="account_01",
                content=f"Excel job after {i} {datetime.now().isoformat()}",
                scheduled_time=datetime.now() + timedelta(hours=3+i),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            excel_job_ids.append(job_id)
        
        # Verify all jobs exist
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 7  # 2 existing + 5 new
        
        all_job_ids = [j.job_id for j in jobs]
        assert job_id1 in all_job_ids
        assert job_id2 in all_job_ids
        for excel_id in excel_job_ids:
            assert excel_id in all_job_ids
    
    def test_add_jobs_different_priorities(self):
        """Test thêm jobs với priority khác nhau."""
        self._init_scheduler()
        
        priorities = [JobPriority.LOW, JobPriority.NORMAL, JobPriority.HIGH, JobPriority.URGENT]
        job_ids = []
        
        for priority in priorities:
            job_id = self.scheduler.add_job(
                account_id="account_01",
                content=f"Priority {priority.value} {datetime.now().isoformat()}",
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
    
    def test_add_jobs_different_platforms(self):
        """Test thêm jobs với platform khác nhau."""
        self._init_scheduler()
        
        platforms = [Platform.THREADS, Platform.FACEBOOK]
        job_ids = []
        
        for platform in platforms:
            job_id = self.scheduler.add_job(
                account_id="account_01",
                content=f"Platform {platform.value} {datetime.now().isoformat()}",
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
    
    def test_load_and_add(self):
        """Test load jobs từ storage và thêm job mới."""
        self._init_scheduler()
        
        # Thêm jobs ban đầu
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content="Job 1",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Tạo scheduler mới (load từ storage)
        new_scheduler = Scheduler(storage_dir=self.test_dir, logger=self.logger)
        new_jobs = new_scheduler.list_jobs()
        
        assert len(new_jobs) == 1
        assert new_jobs[0].job_id == job_id1
        
        # Thêm job mới vào scheduler mới
        job_id2 = new_scheduler.add_job(
            account_id="account_01",
            content="Job 2 after load",
            scheduled_time=datetime.now() + timedelta(hours=2),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Verify both jobs exist
        final_jobs = new_scheduler.list_jobs()
        assert len(final_jobs) == 2
        job_ids = [j.job_id for j in final_jobs]
        assert job_id1 in job_ids
        assert job_id2 in job_ids
    
    def test_add_delete_add(self):
        """Test thêm job, xóa job, thêm job mới."""
        self._init_scheduler()
        
        # Thêm job 1
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content="Job 1",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert len(self.scheduler.list_jobs()) == 1
        
        # Xóa job 1
        self.scheduler.remove_job(job_id1)
        assert len(self.scheduler.list_jobs()) == 0
        
        # Thêm job 2
        job_id2 = self.scheduler.add_job(
            account_id="account_01",
            content="Job 2 after delete",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].job_id == job_id2
        assert job_id1 != job_id2


def main():
    """Main function."""
    tester = TestRuntimeCasesSimple()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main())
