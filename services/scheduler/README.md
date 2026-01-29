# Scheduler Module Documentation

## Cấu trúc Module

```
services/scheduler/
├── __init__.py          # Public API exports
├── models.py            # Data models (JobStatus, JobPriority, ScheduledJob)
├── storage.py           # Persistence layer (JobStorage)
├── recovery.py          # Recovery logic (JobRecovery)
├── job_manager.py       # Job management (JobManager)
├── execution.py         # Execution logic (JobExecutor)
└── scheduler.py         # Main orchestrator (Scheduler)
```

## Module Responsibilities

### 1. models.py - Data Models
**Classes:**
- `JobStatus` (Enum): PENDING, SCHEDULED, RUNNING, COMPLETED, FAILED, CANCELLED, EXPIRED
- `JobPriority` (Enum): LOW(1), NORMAL(2), HIGH(3), URGENT(4)
- `ScheduledJob` (Dataclass): Job entity với business logic

**Key Methods:**
- `to_dict()` / `from_dict()`: Serialization
- `is_expired()`: Check nếu job > 24h từ scheduled_time
- `is_ready()`: Check nếu job sẵn sàng chạy (SCHEDULED + time >= scheduled_time + not expired)
- `can_retry()`: Check nếu còn retry count
- `is_stuck()`: Check nếu RUNNING > max_running_minutes (default 30)

**Status:** ✅ OK

### 2. storage.py - Persistence Layer
**Class:** `JobStorage`

**Responsibilities:**
- Load jobs từ files `jobs_YYYY-MM-DD.json`
- Save jobs vào files theo ngày (completed_at > scheduled_time)
- Cleanup empty files

**Key Methods:**
- `load_jobs()`: Load tất cả jobs từ tất cả files, handle duplicates
- `save_jobs(jobs)`: Save jobs, nhóm theo ngày, atomic write (temp → rename)
- `_cleanup_empty_files()`: Xóa files rỗng

**Error Handling:** JSONDecodeError, PermissionError, OSError

**Status:** ✅ OK

### 3. recovery.py - Recovery Logic
**Class:** `JobRecovery`

**Responsibilities:**
- Recover stuck jobs (RUNNING > 30 phút)
- Recover all running jobs khi scheduler start

**Key Methods:**
- `recover_stuck_jobs()`: Tìm jobs stuck, reset về SCHEDULED (retry) hoặc FAILED
- `recover_all_running_jobs()`: Recover TẤT CẢ jobs RUNNING khi start

**Logic:**
- Nếu `can_retry()`: SCHEDULED + exponential backoff (2^retry_count minutes)
- Nếu không: FAILED

**Status:** ✅ OK

### 4. job_manager.py - Job Management
**Class:** `JobManager`

**Responsibilities:**
- Add/remove jobs
- List/filter jobs
- Get ready jobs
- Cleanup expired jobs

**Key Methods:**
- `add_job()`: Validate input → Create job → Save
- `remove_job()`: Delete job → Save
- `list_jobs()`: Filter by account_id/status → Sort by priority
- `get_ready_jobs()`: Filter jobs where `is_ready() == True`
- `cleanup_expired_jobs()`: Mark expired jobs as EXPIRED

**Validation:**
- account_id: non-empty string
- content: non-empty string, max 500 chars
- scheduled_time: ±1 year from now
- priority: JobPriority enum
- max_retries: int >= 0

**Status:** ✅ OK

### 5. execution.py - Execution Logic
**Class:** `JobExecutor`

**Responsibilities:**
- Execute individual jobs
- Main scheduler loop

**Key Methods:**
- `run_job()`: Set RUNNING → Call post_callback → Handle result/retry
- `scheduler_loop()`: Main loop với cleanup/recovery/execution

**Logic Flow:**
```
run_job:
  RUNNING → Call post_callback
    ├─ Success → COMPLETED
    └─ Failed → Check can_retry()
        ├─ Yes → SCHEDULED + backoff
        └─ No → FAILED

scheduler_loop:
  while running:
    ├─ Cleanup expired
    ├─ Recover stuck
    ├─ Check if job running → Wait
    ├─ Get ready jobs → Run highest priority
    └─ No ready jobs → Sleep 30s (check flag every 1s)
```

**Status:** ✅ OK

### 6. scheduler.py - Main Orchestrator
**Class:** `Scheduler`

**Responsibilities:**
- Orchestrate tất cả components
- Public API
- Lifecycle management (start/stop)

**Initialization:**
- Create components: JobStorage, JobRecovery, JobManager, JobExecutor
- Load jobs from storage
- Recover all running jobs

**Public API (Delegates):**
- `add_job()` → JobManager.add_job()
- `remove_job()` → JobManager.remove_job()
- `list_jobs()` → JobManager.list_jobs()
- `get_ready_jobs()` → JobManager.get_ready_jobs()
- `cleanup_expired_jobs()` → JobManager.cleanup_expired_jobs()
- `recover_stuck_jobs()` → JobRecovery.recover_stuck_jobs()
- `recover_all_running_jobs()` → JobRecovery.recover_all_running_jobs()

**Lifecycle:**
- `start(post_callback)`: Check running → Create task → Start loop
- `stop()`: Set running=False → Cancel task → Save jobs → Flush logs

**Status:** ✅ OK

## Job Lifecycle

```
1. CREATE
   Scheduler.add_job()
     → JobManager.add_job()
       → Validate → Create ScheduledJob(status=SCHEDULED)
       → Save → Return job_id

2. SCHEDULED
   - Wait until scheduled_time
   - Check is_ready() → True when: SCHEDULED + now >= scheduled_time + not expired
   - Status message updated

3. RUNNING
   - JobExecutor.run_job()
   - Set: status=RUNNING, started_at=now
   - Call post_callback()
   - Handle result

4. COMPLETED/FAILED
   - Success → COMPLETED, thread_id, completed_at
   - Failed → Check can_retry()
     - Yes → SCHEDULED + backoff (2^retry_count min)
     - No → FAILED, error

5. RECOVERY
   - Stuck (RUNNING > 30min) → recover_stuck_jobs()
   - Running on start → recover_all_running_jobs()
   - Exponential backoff: 2, 4, 8 minutes

6. EXPIRED
   - > 24h from scheduled_time → cleanup_expired_jobs()
   - Mark as EXPIRED
```

## Data Flow

```
User Request
  ↓
Scheduler (Public API)
  ↓
Component (JobManager/JobRecovery/JobExecutor)
  ↓
Storage (JobStorage) → File System
  ↓
Models (ScheduledJob) → In-Memory Dict
```

## Error Handling

1. **Storage Errors**: Re-raise StorageError, log warning
2. **Job Execution Errors**: Retry với exponential backoff
3. **Validation Errors**: Raise ValueError/InvalidScheduleTimeError
4. **Recovery Errors**: Log và continue
5. **Loop Errors**: Log, sleep 10s, continue

## Thread Safety

- Single-threaded scheduler (1 job at a time)
- Jobs dict shared between components (by reference)
- Save operations atomic (temp file → rename)
- Running flag checked frequently for graceful shutdown

## Module Dependencies

```
Scheduler
  ├─ JobStorage (storage.py)
  │   └─ ScheduledJob (models.py)
  ├─ JobRecovery (recovery.py)
  │   └─ ScheduledJob (models.py)
  ├─ JobManager (job_manager.py)
  │   └─ ScheduledJob, JobStatus, JobPriority (models.py)
  └─ JobExecutor (execution.py)
      └─ ScheduledJob, JobStatus (models.py)
```

**All components share same `jobs` dict reference** - This is correct and intentional.

## Logic Validation

### Job Creation
- ✅ Validation: account_id, content (max 500), scheduled_time (±1 year)
- ✅ Default: priority=NORMAL, max_retries=3
- ✅ Status: SCHEDULED
- ✅ Auto-save after creation

### Job Execution
- ✅ Single job at a time (check running_jobs)
- ✅ Priority-based selection (highest first)
- ✅ Retry with exponential backoff
- ✅ Error handling with logging

### Job Recovery
- ✅ Stuck detection: RUNNING > 30 min
- ✅ Recovery on start: All RUNNING jobs
- ✅ Retry logic: Exponential backoff
- ✅ Failure handling: Mark FAILED if no retry

### Job Cleanup
- ✅ Expired detection: > 24h from scheduled_time
- ✅ Auto-cleanup in scheduler loop
- ✅ Empty file cleanup

### Persistence
- ✅ Atomic writes (temp file → rename)
- ✅ Group by date (completed_at > scheduled_time)
- ✅ Error handling: PermissionError, OSError
- ✅ Auto-save on changes

## Potential Issues (Đã kiểm tra)

1. ✅ **Job reference sharing**: All components share same `self.jobs` dict (by reference) - OK
2. ✅ **Save callback**: Properly passed to all methods that modify jobs - OK
3. ✅ **Recovery timing**: recover_all_running_jobs() called on init - OK
4. ✅ **Stop logic**: Proper cancellation with log flushing - OK
5. ✅ **Error handling**: All exceptions caught and logged - OK

## Summary

**Cấu trúc:** ✅ Modular, clear separation of concerns  
**Logic:** ✅ Correct, handles all edge cases  
**Error Handling:** ✅ Comprehensive  
**Persistence:** ✅ Atomic, safe  
**Recovery:** ✅ Handles crashes and network issues  
**Lifecycle:** ✅ Complete from creation to completion  

**Status:** ✅ READY FOR PRODUCTION

