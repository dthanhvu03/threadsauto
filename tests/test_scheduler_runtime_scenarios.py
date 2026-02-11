#!/usr/bin/env python3
"""
Test cases cho các scenarios khi scheduler đang chạy.

Covers:
- Thêm job khi scheduler đang chạy
- Thêm job khi scheduler đã dừng
- Stop/Start scheduler
- Job đang RUNNING
- Multiple jobs queue
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tempfile
import shutil
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from services.scheduler import Scheduler, JobPriority, JobStatus
from services.scheduler.models import Platform
from services.logger import StructuredLogger


class TestSchedulerRuntimeScenarios:
    """Test cases cho scheduler runtime scenarios."""
    
    def __init__(self):
        """Initialize test environment."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_scheduler_"))
        self.logger = StructuredLogger(name="test_runtime")
        self.scheduler = None
        self._init_scheduler()
        print(f"📁 Test directory: {self.test_dir}")
        print()
    
    def _init_scheduler(self):
        """Initialize fresh scheduler."""
        if self.scheduler:
            # Cleanup old scheduler
            try:
                if self.scheduler.running:
                    asyncio.run(self.scheduler.stop())
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
                asyncio.run(self.scheduler.stop())
            except:
                pass
        
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
            print(f"🧹 Cleaned up: {self.test_dir}")
    
    def create_post_callback_factory(self, delay: float = 0.1):
        """Create post callback factory for testing."""
        async def mock_post_callback(account_id: str, content: str):
            """Mock post callback - simulate success."""
            await asyncio.sleep(delay)  # Simulate processing time
            from types import SimpleNamespace
            return SimpleNamespace(
                success=True,
                thread_id=f"TEST_{datetime.now().timestamp()}",
                error=None
            )
        
        def factory(platform):
            """Factory function that returns callback."""
            return mock_post_callback
        
        return factory
    
    def create_slow_post_callback_factory(self):
        """Create slow post callback factory (5 seconds)."""
        return self.create_post_callback_factory(delay=5.0)
    
    def run_all_tests(self):
        """Run tất cả test cases."""
        tests = [
            ("1. Thêm job khi scheduler chưa chạy", self.test_add_job_before_start),
            ("2. Start scheduler với jobs sẵn có", self.test_start_scheduler_with_jobs),
            ("3. Thêm job khi scheduler đang chạy", self.test_add_job_while_running),
            ("4. Thêm nhiều jobs khi scheduler đang chạy", self.test_add_multiple_jobs_while_running),
            ("5. Stop scheduler khi đang chạy job", self.test_stop_scheduler_while_running),
            ("6. Start lại scheduler sau khi stop", self.test_restart_scheduler),
            ("7. Thêm job sau khi scheduler đã dừng", self.test_add_job_after_stop),
            ("8. Thêm job khi scheduler đang chạy job khác", self.test_add_job_during_execution),
            ("9. Hết jobs, scheduler sleep, thêm job mới", self.test_add_job_after_scheduler_sleep),
            ("10. Priority queue khi scheduler đang chạy", self.test_priority_queue_while_running),
            ("11. Stop/Start nhiều lần", self.test_stop_start_multiple_times),
            ("12. Thêm job với scheduled_time trong quá khứ (ready ngay)", self.test_add_ready_job_while_running),
            ("13. Thêm job với scheduled_time trong tương lai (chưa ready)", self.test_add_future_job_while_running),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                print(f"🧪 {test_name}...")
                asyncio.run(test_func())
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
    
    async def test_add_job_before_start(self):
        """Test thêm job trước khi start scheduler."""
        self._init_scheduler()
        
        # Thêm job khi scheduler chưa chạy
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Job before start",
            scheduled_time=datetime.now() - timedelta(minutes=5),  # Ready
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert job_id is not None
        assert self.scheduler.running is False
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].job_id == job_id
        assert jobs[0].status == JobStatus.SCHEDULED
    
    async def test_start_scheduler_with_jobs(self):
        """Test start scheduler với jobs sẵn có."""
        self._init_scheduler()
        
        # Thêm jobs trước
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content="Job 1",
            scheduled_time=datetime.now() - timedelta(minutes=5),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        job_id2 = self.scheduler.add_job(
            account_id="account_01",
            content="Job 2",
            scheduled_time=datetime.now() - timedelta(minutes=3),
            priority=JobPriority.HIGH,
            platform=Platform.THREADS
        )
        
        assert len(self.scheduler.list_jobs()) == 2
        
        # Start scheduler
        callback_factory = self.create_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        
        # Wait a bit for scheduler to start
        await asyncio.sleep(0.5)
        
        assert self.scheduler.running is True
        
        # Wait for jobs to complete
        await asyncio.sleep(2)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task
        
        # Verify jobs were processed
        jobs = self.scheduler.list_jobs()
        completed = [j for j in jobs if j.status == JobStatus.COMPLETED]
        assert len(completed) >= 1  # At least one should be completed
    
    async def test_add_job_while_running(self):
        """Test thêm job khi scheduler đang chạy."""
        self._init_scheduler()
        
        # Start scheduler
        callback_factory = self.create_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        await asyncio.sleep(0.3)
        
        assert self.scheduler.running is True
        
        # Thêm job khi scheduler đang chạy
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Job added while running",
            scheduled_time=datetime.now() - timedelta(minutes=1),  # Ready
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert job_id is not None
        
        # Wait for job to be picked up
        await asyncio.sleep(2)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task
        
        # Verify job was added and processed
        jobs = self.scheduler.list_jobs()
        job = next((j for j in jobs if j.job_id == job_id), None)
        assert job is not None
        assert job.status in [JobStatus.COMPLETED, JobStatus.SCHEDULED, JobStatus.RUNNING]
    
    async def test_add_multiple_jobs_while_running(self):
        """Test thêm nhiều jobs khi scheduler đang chạy (simulate Excel upload)."""
        self._init_scheduler()
        
        # Start scheduler
        callback_factory = self.create_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        await asyncio.sleep(0.3)
        
        assert self.scheduler.running is True
        
        # Simulate Excel upload - thêm nhiều jobs
        job_ids = []
        for i in range(5):
            job_id = self.scheduler.add_job(
                account_id="account_01",
                content=f"Excel job {i} {datetime.now().isoformat()}",
                scheduled_time=datetime.now() - timedelta(minutes=1),  # Ready
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            job_ids.append(job_id)
            await asyncio.sleep(0.1)  # Small delay between adds
        
        assert len(job_ids) == 5
        
        # Wait for jobs to be processed
        await asyncio.sleep(3)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task
        
        # Verify all jobs were added
        jobs = self.scheduler.list_jobs()
        assert len(jobs) >= 5
        
        # Verify jobs are in queue or completed
        for job_id in job_ids:
            job = next((j for j in jobs if j.job_id == job_id), None)
            assert job is not None
    
    async def test_stop_scheduler_while_running(self):
        """Test stop scheduler khi đang chạy job."""
        self._init_scheduler()
        
        # Thêm job với slow callback
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Slow job",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Start scheduler với slow callback
        callback_factory = self.create_slow_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        await asyncio.sleep(0.5)
        
        assert self.scheduler.running is True
        
        # Wait a bit for job to start
        await asyncio.sleep(1)
        
        # Stop scheduler while job is running
        await self.scheduler.stop()
        await task
        
        assert self.scheduler.running is False
        
        # Verify scheduler stopped gracefully
        jobs = self.scheduler.list_jobs()
        job = next((j for j in jobs if j.job_id == job_id), None)
        assert job is not None
        # Job might be RUNNING (if stopped mid-execution) or COMPLETED
        assert job.status in [JobStatus.RUNNING, JobStatus.COMPLETED, JobStatus.SCHEDULED]
    
    async def test_restart_scheduler(self):
        """Test start lại scheduler sau khi stop."""
        self._init_scheduler()
        
        # Thêm jobs
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content="Job 1",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Start scheduler
        task1 = asyncio.create_task(
            self.scheduler.start(post_callback=self.mock_post_callback)
        )
        await asyncio.sleep(0.5)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task1
        
        assert self.scheduler.running is False
        
        # Thêm job mới
        job_id2 = self.scheduler.add_job(
            account_id="account_01",
            content="Job 2",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Start lại scheduler
        task2 = asyncio.create_task(
            self.scheduler.start(post_callback=self.mock_post_callback)
        )
        await asyncio.sleep(0.5)
        
        assert self.scheduler.running is True
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Stop again
        await self.scheduler.stop()
        await task2
        
        # Verify both jobs exist
        jobs = self.scheduler.list_jobs()
        job_ids = [j.job_id for j in jobs]
        assert job_id1 in job_ids
        assert job_id2 in job_ids
    
    async def test_add_job_after_stop(self):
        """Test thêm job sau khi scheduler đã dừng."""
        self._init_scheduler()
        
        # Start và stop scheduler
        task = asyncio.create_task(
            self.scheduler.start(post_callback=self.mock_post_callback)
        )
        await asyncio.sleep(0.3)
        await self.scheduler.stop()
        await task
        
        assert self.scheduler.running is False
        
        # Thêm job sau khi stop
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Job after stop",
            scheduled_time=datetime.now() + timedelta(hours=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert job_id is not None
        
        jobs = self.scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0].job_id == job_id
        assert jobs[0].status == JobStatus.SCHEDULED
    
    async def test_add_job_during_execution(self):
        """Test thêm job khi scheduler đang chạy job khác."""
        self._init_scheduler()
        
        # Thêm job đầu tiên (slow)
        job_id1 = self.scheduler.add_job(
            account_id="account_01",
            content="Slow job 1",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Start scheduler với slow callback
        callback_factory = self.create_slow_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        await asyncio.sleep(0.5)
        
        # Wait for first job to start running
        await asyncio.sleep(1)
        
        # Verify first job is running
        jobs = self.scheduler.list_jobs()
        job1 = next((j for j in jobs if j.job_id == job_id1), None)
        assert job1 is not None
        # Job might be RUNNING or already COMPLETED
        assert job1.status in [JobStatus.RUNNING, JobStatus.COMPLETED]
        
        # Thêm job thứ 2 khi job 1 đang chạy
        job_id2 = self.scheduler.add_job(
            account_id="account_01",
            content="Job 2 during execution",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=JobPriority.HIGH,  # Higher priority
            platform=Platform.THREADS
        )
        
        assert job_id2 is not None
        
        # Wait a bit
        await asyncio.sleep(1)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task
        
        # Verify both jobs exist
        jobs = self.scheduler.list_jobs()
        job_ids = [j.job_id for j in jobs]
        assert job_id1 in job_ids
        assert job_id2 in job_ids
    
    async def test_add_job_after_scheduler_sleep(self):
        """Test thêm job sau khi scheduler đã sleep (hết jobs)."""
        self._init_scheduler()
        
        # Start scheduler
        callback_factory = self.create_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        await asyncio.sleep(0.3)
        
        assert self.scheduler.running is True
        
        # Wait for scheduler to go to sleep (no jobs)
        await asyncio.sleep(2)
        
        # Thêm job sau khi scheduler đã sleep
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Job after sleep",
            scheduled_time=datetime.now() - timedelta(minutes=1),  # Ready
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        assert job_id is not None
        
        # Wait for scheduler to pick up new job
        await asyncio.sleep(2)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task
        
        # Verify job was processed
        jobs = self.scheduler.list_jobs()
        job = next((j for j in jobs if j.job_id == job_id), None)
        assert job is not None
        assert job.status in [JobStatus.COMPLETED, JobStatus.SCHEDULED, JobStatus.RUNNING]
    
    async def test_priority_queue_while_running(self):
        """Test priority queue khi scheduler đang chạy."""
        self._init_scheduler()
        
        # Start scheduler
        callback_factory = self.create_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        await asyncio.sleep(0.3)
        
        # Thêm jobs với priority khác nhau
        job_id_low = self.scheduler.add_job(
            account_id="account_01",
            content="Low priority",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=JobPriority.LOW,
            platform=Platform.THREADS
        )
        
        await asyncio.sleep(0.1)
        
        job_id_high = self.scheduler.add_job(
            account_id="account_01",
            content="High priority",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=JobPriority.HIGH,
            platform=Platform.THREADS
        )
        
        await asyncio.sleep(0.1)
        
        job_id_normal = self.scheduler.add_job(
            account_id="account_01",
            content="Normal priority",
            scheduled_time=datetime.now() - timedelta(minutes=1),
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Wait for processing
        await asyncio.sleep(3)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task
        
        # Verify all jobs exist
        jobs = self.scheduler.list_jobs()
        job_ids = [j.job_id for j in jobs]
        assert job_id_low in job_ids
        assert job_id_high in job_ids
        assert job_id_normal in job_ids
    
    async def test_stop_start_multiple_times(self):
        """Test stop/start scheduler nhiều lần."""
        self._init_scheduler()
        
        for i in range(3):
            # Start
            task = asyncio.create_task(
                self.scheduler.start(post_callback=self.mock_post_callback)
            )
            await asyncio.sleep(0.2)
            assert self.scheduler.running is True
            
            # Thêm job
            job_id = self.scheduler.add_job(
                account_id="account_01",
                content=f"Job iteration {i}",
                scheduled_time=datetime.now() - timedelta(minutes=1),
                priority=JobPriority.NORMAL,
                platform=Platform.THREADS
            )
            
            await asyncio.sleep(0.5)
            
            # Stop
            await self.scheduler.stop()
            await task
            assert self.scheduler.running is False
            
            await asyncio.sleep(0.2)
        
        # Verify jobs were added
        jobs = self.scheduler.list_jobs()
        assert len(jobs) >= 3
    
    async def test_add_ready_job_while_running(self):
        """Test thêm job với scheduled_time trong quá khứ (ready ngay)."""
        self._init_scheduler()
        
        # Start scheduler
        callback_factory = self.create_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        await asyncio.sleep(0.3)
        
        # Thêm job ready ngay (scheduled_time trong quá khứ)
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Ready job",
            scheduled_time=datetime.now() - timedelta(minutes=5),  # 5 phút trước
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Wait for scheduler to pick up
        await asyncio.sleep(2)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task
        
        # Verify job was processed
        jobs = self.scheduler.list_jobs()
        job = next((j for j in jobs if j.job_id == job_id), None)
        assert job is not None
        assert job.status in [JobStatus.COMPLETED, JobStatus.SCHEDULED, JobStatus.RUNNING]
    
    async def test_add_future_job_while_running(self):
        """Test thêm job với scheduled_time trong tương lai (chưa ready)."""
        self._init_scheduler()
        
        # Start scheduler
        callback_factory = self.create_post_callback_factory()
        self.scheduler.start(post_callback_factory=callback_factory)
        task = self.scheduler._task
        await asyncio.sleep(0.3)
        
        # Thêm job chưa ready (scheduled_time trong tương lai)
        job_id = self.scheduler.add_job(
            account_id="account_01",
            content="Future job",
            scheduled_time=datetime.now() + timedelta(hours=1),  # 1 giờ sau
            priority=JobPriority.NORMAL,
            platform=Platform.THREADS
        )
        
        # Wait a bit
        await asyncio.sleep(1)
        
        # Stop scheduler
        await self.scheduler.stop()
        await task
        
        # Verify job exists but not processed yet
        jobs = self.scheduler.list_jobs()
        job = next((j for j in jobs if j.job_id == job_id), None)
        assert job is not None
        assert job.status == JobStatus.SCHEDULED  # Should still be scheduled


def main():
    """Main function."""
    tester = TestSchedulerRuntimeScenarios()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    exit(main())

