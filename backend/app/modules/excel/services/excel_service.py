"""
Excel service.

Business logic layer for Excel file operations.
Handles file upload, processing, and template retrieval.
"""

# Standard library
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime, timedelta, timezone
from fastapi import UploadFile
import asyncio

# Third-party
import aiofiles

# Local
from services.logger import StructuredLogger
from backend.app.shared.base_service import BaseService
from backend.app.modules.excel.repositories.excel_repository import ExcelRepository
from backend.app.modules.jobs.services.jobs_service import JobsService
from backend.app.core.exceptions import NotFoundError, InternalError, ValidationError
from content.excel_loader import ExcelLoader, ExcelLoadError


class ExcelService(BaseService):
    """
    Service for Excel business logic.
    
    Handles:
    - File upload and processing
    - Template retrieval
    - Job creation from Excel
    """
    
    def __init__(
        self,
        repository: Optional[ExcelRepository] = None,
        jobs_service: Optional[JobsService] = None
    ):
        """
        Initialize Excel service.
        
        Args:
            repository: ExcelRepository instance. If None, creates new instance.
            jobs_service: JobsService instance. If None, creates new instance.
        """
        super().__init__("excel_service")
        self.repository = repository or ExcelRepository()
        self.jobs_service = jobs_service or JobsService()
    
    async def upload_file(
        self,
        file: UploadFile,
        account_id: Optional[str] = None
    ) -> Dict:
        """
        Upload and process Excel file.
        
        Args:
            file: Uploaded file
            account_id: Optional account ID
        
        Returns:
            Dictionary with filename, account_id, and jobs_created
        
        Raises:
            ValidationError: If file is invalid
            InternalError: If processing fails
        """
        try:
            # Save uploaded file temporarily
            upload_dir = Path("uploads")
            upload_dir.mkdir(exist_ok=True)
            
            file_path = upload_dir / file.filename
            
            # Write file content (async file I/O)
            content = await file.read()
            async with aiofiles.open(file_path, "wb") as f:
                await f.write(content)
            
            # Process Excel file
            # 1. Load Excel file using ExcelLoader
            loader = ExcelLoader(logger=self.logger)
            posts = loader.load_from_file(file_path)
            
            # 2. Filter posts with scheduled_time (only scheduled posts become jobs)
            scheduled_posts = [p for p in posts if "scheduled_time" in p and p["scheduled_time"]]
            immediate_posts = [p for p in posts if "scheduled_time" not in p or not p.get("scheduled_time")]
            
            # Get minimum delay between posts from SafetyGuard config (default: 5 seconds)
            # Use a safety buffer (2x minimum) to account for execution time variations
            min_delay_seconds = 5.0
            safety_buffer_multiplier = 2.0  # Use 2x minimum delay for safety buffer
            try:
                from services.safety_guard import SafetyConfig
                safety_config = SafetyConfig()
                min_delay_seconds = safety_config.min_delay_between_posts_seconds
            except Exception:
                # Fallback to default if can't get config
                pass
            
            # Calculate spacing with safety buffer
            spacing_seconds = min_delay_seconds * safety_buffer_multiplier  # At least 10 seconds
            
            # 3. Sort scheduled posts by scheduled_time and adjust spacing
            # This ensures jobs don't violate SafetyGuard action spacing requirements
            from services.utils.datetime_utils import normalize_to_utc
            
            # Sort posts by scheduled_time
            scheduled_posts_with_datetime = []
            for post in scheduled_posts:
                scheduled_time = post["scheduled_time"]
                if isinstance(scheduled_time, datetime):
                    scheduled_time_utc = normalize_to_utc(scheduled_time)
                else:
                    # Parse string to datetime
                    try:
                        scheduled_time_utc = datetime.fromisoformat(str(scheduled_time).replace('Z', '+00:00'))
                        if scheduled_time_utc.tzinfo is None:
                            scheduled_time_utc = scheduled_time_utc.replace(tzinfo=timezone.utc)
                    except Exception:
                        # If parsing fails, use current time + delay
                        scheduled_time_utc = datetime.now(timezone.utc) + timedelta(seconds=spacing_seconds)
                
                scheduled_posts_with_datetime.append({
                    "post": post,
                    "scheduled_time": scheduled_time_utc
                })
            
            # Sort by scheduled_time
            scheduled_posts_with_datetime.sort(key=lambda x: x["scheduled_time"])
            
            # Adjust scheduled_time to ensure minimum spacing between jobs
            adjusted_posts = []
            last_scheduled_time = None
            
            for item in scheduled_posts_with_datetime:
                post = item["post"]
                scheduled_time = item["scheduled_time"]
                
                # If this is not the first post and scheduled_time is too close to previous
                if last_scheduled_time is not None:
                    time_diff = (scheduled_time - last_scheduled_time).total_seconds()
                    
                    # If scheduled_time is too close, adjust it
                    if time_diff < spacing_seconds:
                        # Adjust to be at least spacing_seconds after the previous job
                        scheduled_time = last_scheduled_time + timedelta(seconds=spacing_seconds)
                        
                        self.logger.log_step(
                            step="ADJUST_SCHEDULED_TIME_FOR_SPACING",
                            result="SUCCESS",
                            account_id=account_id,
                            original_time=item["scheduled_time"].isoformat(),
                            adjusted_time=scheduled_time.isoformat(),
                            spacing_seconds=spacing_seconds,
                            min_delay_seconds=min_delay_seconds
                        )
                
                adjusted_posts.append({
                    "post": post,
                    "scheduled_time": scheduled_time
                })
                last_scheduled_time = scheduled_time
            
            # 4. Create jobs for scheduled posts (now with adjusted times)
            jobs_created = 0
            jobs_failed = 0
            errors = []
            if not account_id:
                raise ValidationError(
                    message="account_id is required to create jobs from Excel",
                    details={"filename": file.filename}
                )
            
            for item in adjusted_posts:
                post = item["post"]
                scheduled_time = item["scheduled_time"]
                try:
                    # scheduled_time is already a datetime object (from adjustment step)
                    # Convert to ISO string format
                    scheduled_time_str = scheduled_time.isoformat()
                    
                    # Get priority (default: NORMAL)
                    priority = post.get("priority", "NORMAL")
                    if priority:
                        priority = priority.upper()
                    else:
                        priority = "NORMAL"
                    
                    # Get platform (default: THREADS)
                    platform = post.get("platform", "THREADS")
                    if platform:
                        platform = platform.upper()
                    else:
                        platform = "THREADS"
                    
                    # Get link_aff (optional)
                    link_aff = post.get("link_aff")
                    if link_aff:
                        link_aff_str = str(link_aff).strip()
                        if link_aff_str and link_aff_str.lower() not in ["nan", ""]:
                            link_aff = link_aff_str
                        else:
                            link_aff = None
                    else:
                        link_aff = None
                    
                    # Create job
                    job_id = self.jobs_service.create_job(
                        account_id=account_id,
                        content=post["content"],
                        scheduled_time=scheduled_time_str,
                        priority=priority,
                        platform=platform,
                        link_aff=link_aff
                    )
                    jobs_created += 1
                    self.logger.log_step(
                        step="CREATE_JOB_FROM_EXCEL",
                        result="SUCCESS",
                        job_id=job_id,
                        account_id=account_id,
                        scheduled_time=scheduled_time_str
                    )
                    
                except (ValidationError, InternalError) as e:
                    jobs_failed += 1
                    error_msg = str(e)
                    errors.append(error_msg)
                    self.logger.log_step(
                        step="CREATE_JOB_FROM_EXCEL",
                        result="FAILED",
                        error=error_msg,
                        account_id=account_id,
                        content_preview=post.get("content", "")[:50] if post.get("content") else None
                    )
                except Exception as e:
                    jobs_failed += 1
                    error_msg = f"Unexpected error: {str(e)}"
                    errors.append(error_msg)
                    self.logger.log_step(
                        step="CREATE_JOB_FROM_EXCEL",
                        result="ERROR",
                        error=error_msg,
                        account_id=account_id,
                        error_type=type(e).__name__
                    )
            
            # Log summary
            self.logger.log_step(
                step="UPLOAD_EXCEL_FILE",
                result="SUCCESS",
                filename=file.filename,
                account_id=account_id,
                file_path=str(file_path),
                total_posts=len(posts),
                scheduled_posts=len(scheduled_posts),
                immediate_posts=len(immediate_posts),
                jobs_created=jobs_created,
                jobs_failed=jobs_failed
            )
            
            # Broadcast WebSocket event if jobs were created
            # This will trigger refresh in Jobs and Scheduler pages
            if jobs_created > 0:
                try:
                    from backend.api.websocket.connection_manager import manager
                    from backend.api.websocket.messages import create_message, EVENT_JOB_CREATED
                    
                    # Broadcast to multiple rooms
                    message = create_message(
                        EVENT_JOB_CREATED,
                        {
                            "jobs_created": jobs_created,
                            "account_id": account_id,
                            "source": "excel_upload"
                        },
                        account_id=account_id
                    )
                    
                    # Try to broadcast in async context
                    try:
                        loop = asyncio.get_running_loop()
                        # Schedule broadcast as task
                        asyncio.create_task(manager.broadcast_to_room(
                            message,
                            room="jobs",
                            account_id=account_id
                        ))
                        asyncio.create_task(manager.broadcast_to_room(
                            message,
                            room="scheduler",
                            account_id=account_id
                        ))
                        asyncio.create_task(manager.broadcast_to_room(
                            message,
                            room="dashboard",
                            account_id=account_id
                        ))
                    except RuntimeError:
                        # No running loop, try to get event loop
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                asyncio.create_task(manager.broadcast_to_room(
                                    message,
                                    room="jobs",
                                    account_id=account_id
                                ))
                                asyncio.create_task(manager.broadcast_to_room(
                                    message,
                                    room="scheduler",
                                    account_id=account_id
                                ))
                                asyncio.create_task(manager.broadcast_to_room(
                                    message,
                                    room="dashboard",
                                    account_id=account_id
                                ))
                            else:
                                loop.run_until_complete(manager.broadcast_to_room(
                                    message,
                                    room="jobs",
                                    account_id=account_id
                                ))
                                loop.run_until_complete(manager.broadcast_to_room(
                                    message,
                                    room="scheduler",
                                    account_id=account_id
                                ))
                                loop.run_until_complete(manager.broadcast_to_room(
                                    message,
                                    room="dashboard",
                                    account_id=account_id
                                ))
                        except Exception:
                            # Skip WebSocket broadcast if not available
                            pass
                except ImportError:
                    # WebSocket not available, skip broadcast
                    pass
                except Exception as e:
                    # Log error but don't fail the upload
                    self.logger.log_step(
                        step="WEBSOCKET_BROADCAST_EXCEL_UPLOAD",
                        result="ERROR",
                        error=str(e),
                        error_type=type(e).__name__
                    )
            
            # Return result
            result = {
                "filename": file.filename,
                "account_id": account_id,
                "total_posts": len(posts),
                "scheduled_posts": len(scheduled_posts),
                "immediate_posts": len(immediate_posts),
                "jobs_created": jobs_created,
                "jobs_failed": jobs_failed
            }
            
            if errors:
                result["errors"] = errors[:10]  # Limit to first 10 errors
                if len(errors) > 10:
                    result["errors"].append(f"... and {len(errors) - 10} more errors")
            
            return result
        except ExcelLoadError as e:
            # Excel loading errors (file format, missing columns, etc.)
            self.logger.log_step(
                step="UPLOAD_EXCEL_FILE",
                result="ERROR",
                error=f"Excel load error: {str(e)}",
                filename=file.filename if file else None,
                account_id=account_id,
                error_type="ExcelLoadError"
            )
            raise ValidationError(
                message=f"Failed to load Excel file: {str(e)}",
                details={"filename": file.filename if file else None}
            )
        except ValidationError:
            # Re-raise validation errors as-is
            raise
        except Exception as e:
            self.logger.log_step(
                step="UPLOAD_EXCEL_FILE",
                result="ERROR",
                error=f"Failed to upload Excel file: {str(e)}",
                filename=file.filename if file else None,
                account_id=account_id,
                error_type=type(e).__name__
            )
            raise InternalError(message=f"Failed to upload Excel file: {str(e)}")
    
    def get_template_path(self) -> Path:
        """
        Get template file path.
        
        Returns:
            Path to template file
        
        Raises:
            NotFoundError: If template file does not exist
        """
        template_path = self.repository.get_template_path()
        
        if not self.repository.template_exists():
            raise NotFoundError(
                resource="Template",
                details={"path": str(template_path)}
            )
        
        return template_path
