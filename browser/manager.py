"""
Module: browser/manager.py

Quản lý browser cho Threads automation.
Xử lý vòng đời browser, quản lý profile, và duy trì session.
"""

# Standard library
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import random
import os
import psutil
import time
import sys
import re
import shutil
from datetime import datetime


# Ensure DISPLAY is set for WSL/WSLg environments
# This is required for headed browser mode
if not os.environ.get("DISPLAY"):
    # Check if WSLg is available
    if os.path.exists("/mnt/wslg/.X11-unix"):
        os.environ["DISPLAY"] = ":0"
    # Fallback for regular X server
    elif os.path.exists("/tmp/.X11-unix/X0"):
        os.environ["DISPLAY"] = ":0"

# fcntl chỉ có trên Linux/Unix, không có trên Windows
try:
    import fcntl

    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False


def normalize_profile_path(profile_path: str) -> str:
    """
    Normalize profile path từ Windows format sang Linux format (WSL).

    Args:
        profile_path: Profile path có thể là:
            - Windows path: \\\\wsl.localhost\\Ubuntu\\home\\zusem\\threads\\profiles\\02
            - Linux path: /home/zusem/threads/profiles/02
            - Relative path: profiles/02 hoặc ./profiles/02

    Returns:
        Normalized Linux path (absolute path)
    """
    if not profile_path:
        return profile_path

    # Nếu đã là absolute Linux path (bắt đầu bằng / và không phải Windows UNC), return as-is
    if (
        os.path.isabs(profile_path)
        and not profile_path.startswith("\\\\")
        and not profile_path.startswith("//")
    ):
        return profile_path

    # Initialize path variable early to avoid UnboundLocalError
    path = profile_path

    # Nếu là Windows UNC path format (\\wsl.localhost\... hoặc \\\\wsl.localhost\\...)
    if profile_path.startswith("\\\\") or (
        profile_path.startswith("//") and "wsl" in profile_path.lower()
    ):
        # Convert Windows path sang Linux path
        # \\\\wsl.localhost\\Ubuntu\\home\\zusem\\threads\\profiles\\02
        # -> /home/zusem/threads/profiles/02
        path = profile_path.replace("\\", "/")

        # Remove leading slashes
        path = path.lstrip("/")

        # Tìm phần /home/ hoặc /mnt/ trong path (case-insensitive)
        # Pattern: wsl.localhost/Ubuntu/home/... hoặc wsl.localhost/Ubuntu/mnt/...
        if "/home/" in path.lower():
            # Extract phần sau home/
            parts = (
                path.split("/home/", 1) if "/home/" in path else path.split("/Home/", 1)
            )
            if len(parts) > 1:
                path = "/home/" + parts[1]
            else:
                # Fallback: tìm bằng regex
                match = re.search(r"home/(.+)", path, re.IGNORECASE)
                if match:
                    path = "/home/" + match.group(1)
        elif "/mnt/" in path.lower():
            # Extract phần sau mnt/
            parts = (
                path.split("/mnt/", 1) if "/mnt/" in path else path.split("/Mnt/", 1)
            )
            if len(parts) > 1:
                path = "/mnt/" + parts[1]
            else:
                match = re.search(r"mnt/(.+)", path, re.IGNORECASE)
                if match:
                    path = "/mnt/" + match.group(1)
        else:
            # Không tìm thấy home/ hoặc mnt/, thử extract từ threads nếu có
            if "threads" in path.lower():
                threads_idx = path.lower().find("threads")
                if threads_idx != -1:
                    # Tìm username từ phần trước threads
                    before_threads = path[:threads_idx]
                    match = re.search(r"home/([^/]+)", before_threads, re.IGNORECASE)
                    if match:
                        username = match.group(1)
                        after_threads = path[threads_idx:]
                        path = f"/home/{username}/{after_threads}"
                    else:
                        # Fallback: giả sử username là zusem
                        path = "/home/zusem/" + path[threads_idx:]
                else:
                    path = "/home/zusem/" + path.split("/")[-1]
            else:
                # Không có pattern nào match, fallback về relative path
                path = profile_path.replace("\\", "/").lstrip("/")
                base_dir = Path.cwd()
                normalized = (base_dir / path).resolve()
                return str(normalized)

    # Nếu là relative path, convert sang absolute
    if not os.path.isabs(path):
        # Convert relative path sang absolute dựa trên current working directory
        base_dir = Path.cwd()
        normalized = (base_dir / path).resolve()
        return str(normalized)

    return path


# Third-party
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    Playwright,
)

# Local
from services.logger import StructuredLogger
from config import Config


class BrowserManager:
    """
    Quản lý browser cho automation.

    Xử lý vòng đời browser, quản lý profile,
    và duy trì session sử dụng Playwright.

    Attributes:
        account_id: Mã định danh tài khoản
        browser: Instance browser
        context: Browser context (với persistent profile)
        page: Instance trang hiện tại
        playwright: Instance Playwright
        config: Đối tượng cấu hình
        config: Đối tượng cấu hình
        logger: Instance structured logger
    """

    # Track active instances for graceful shutdown
    _active_instances = set()

    @classmethod
    async def close_all(cls):
        """Close all active browser instances."""
        if not cls._active_instances:
            return

        print(f"Shutting down {len(cls._active_instances)} active browser instances...")
        # Create tasks for all close operations
        tasks = [instance.close() for instance in list(cls._active_instances)]
        await asyncio.gather(*tasks, return_exceptions=True)
        cls._active_instances.clear()

    def __init__(
        self,
        account_id: Optional[str] = None,
        profile_path: Optional[str] = None,
        config: Optional[Config] = None,
        logger: Optional[StructuredLogger] = None,
    ):
        """
        Khởi tạo browser manager.

        Args:
            account_id: Mã định danh tài khoản (ví dụ: "account_01")
            profile_path: Browser profile path (client-side, optional). Nếu không có, sẽ tự động tạo từ account_id
            config: Đối tượng cấu hình (tùy chọn)
            logger: Instance structured logger (tùy chọn)
        """
        self.account_id = account_id
        self.config = config or Config()
        self.logger = logger or StructuredLogger(name="browser_manager")

        # Các instance browser
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        # Đường dẫn profile
        if profile_path:
            # Normalize profile path (convert Windows path sang Linux path nếu cần)
            normalized_path = normalize_profile_path(profile_path)
            self.profile_path = Path(normalized_path)
            self.logger.log_step(
                step="PROFILE_PATH_NORMALIZE",
                result="INFO",
                original_path=profile_path,
                normalized_path=str(self.profile_path),
                account_id=self.account_id,
            )
        elif account_id:
            # Fallback về cách cũ: tạo từ account_id
            self.profile_path = Path(f"./profiles/{account_id}")
        else:
            # Default profile path nếu không có cả account_id và profile_path
            self.profile_path = Path("./profiles/default")

        # Tạo thư mục profile nếu chưa tồn tại
        self.profile_path.mkdir(parents=True, exist_ok=True)

        # Lock file để tránh multiple instances
        self.lock_file_path = self.profile_path / ".browser_manager.lock"
        self.lock_file = None

        # Register instance
        BrowserManager._active_instances.add(self)

    def _check_and_kill_existing_processes(self) -> None:
        """
        Kiểm tra và kill các Chrome process đang sử dụng profile này.

        Chrome không cho phép nhiều instance cùng sử dụng một profile.
        """
        try:
            profile_path_str = str(self.profile_path.absolute())
            killed_count = 0

            for proc in psutil.process_iter(["pid", "name", "cmdline"]):
                try:
                    # Kiểm tra nếu là Chrome/Chromium process
                    proc_name = proc.info["name"] or ""
                    if (
                        "chrome" not in proc_name.lower()
                        and "chromium" not in proc_name.lower()
                    ):
                        continue

                    # Kiểm tra cmdline có chứa profile path không
                    cmdline = proc.info["cmdline"] or []
                    cmdline_str = " ".join(cmdline)

                    if profile_path_str in cmdline_str:
                        self.logger.log_step(
                            step="KILL_EXISTING_PROCESS",
                            result="INFO",
                            note=f"Found existing Chrome process (PID: {proc.info['pid']}) using profile",
                            pid=proc.info["pid"],
                        )
                        try:
                            proc.kill()
                            proc.wait(timeout=5)
                            killed_count += 1
                            self.logger.log_step(
                                step="KILL_EXISTING_PROCESS",
                                result="SUCCESS",
                                note=f"Killed Chrome process PID: {proc.info['pid']}",
                                pid=proc.info["pid"],
                            )
                        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                            pass
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            if killed_count > 0:
                # Đợi một chút để process cleanup hoàn tất
                time.sleep(1)
                self.logger.log_step(
                    step="KILL_EXISTING_PROCESSES",
                    result="SUCCESS",
                    note=f"Killed {killed_count} existing Chrome process(es)",
                    killed_count=killed_count,
                )
        except Exception as e:
            self.logger.log_step(
                step="KILL_EXISTING_PROCESSES",
                result="WARNING",
                error=str(e),
                note="Could not check/kill existing processes (may not have permission)",
            )

    def _acquire_lock(self) -> bool:
        """
        Acquire file lock để tránh multiple instances.

        Returns:
            True nếu acquire lock thành công, False nếu profile đang được sử dụng
        """
        try:
            # Kiểm tra lock file cũ (stale lock)
            if self.lock_file_path.exists():
                try:
                    with open(self.lock_file_path, "r") as f:
                        lock_pid_str = f.read().strip()
                        if lock_pid_str:
                            lock_pid = int(lock_pid_str)
                            # Kiểm tra xem process còn tồn tại không
                            if psutil.pid_exists(lock_pid):
                                try:
                                    proc = psutil.Process(lock_pid)
                                    # Kiểm tra xem process có đang sử dụng profile không
                                    cmdline = " ".join(proc.cmdline() or [])
                                    if str(self.profile_path.absolute()) in cmdline:
                                        self.logger.log_step(
                                            step="ACQUIRE_LOCK",
                                            result="FAILED",
                                            error=f"Profile is locked by active process (PID: {lock_pid})",
                                            lock_pid=lock_pid,
                                        )
                                        return False
                                except (psutil.NoSuchProcess, psutil.AccessDenied):
                                    pass
                            # Process không còn tồn tại, xóa stale lock
                            self.lock_file_path.unlink()
                except (ValueError, FileNotFoundError):
                    pass

            # Tạo lock file mới
            self.lock_file = open(self.lock_file_path, "w")

            if HAS_FCNTL:
                # Trên Linux/Unix: sử dụng fcntl
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    # Lock đã được acquire bởi process khác
                    self.lock_file.close()
                    self.lock_file = None
                    return False
            else:
                # Trên Windows: chỉ kiểm tra process, không có file lock
                # File lock trên Windows phức tạp hơn, dựa vào process check
                pass

            # Ghi PID vào lock file
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()

            self.logger.log_step(
                step="ACQUIRE_LOCK",
                result="SUCCESS",
                note=f"Acquired lock for profile (PID: {os.getpid()})",
            )
            return True

        except Exception as e:
            self.logger.log_step(
                step="ACQUIRE_LOCK",
                result="WARNING",
                error=str(e),
                note="Could not acquire lock",
            )
            if self.lock_file:
                try:
                    self.lock_file.close()
                except:
                    pass
                self.lock_file = None
            return False

    def _release_lock(self) -> None:
        """Release file lock."""
        if self.lock_file:
            try:
                if HAS_FCNTL:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                self.lock_file = None
            except Exception:
                pass

        # Xóa lock file
        try:
            if self.lock_file_path.exists():
                self.lock_file_path.unlink()
        except Exception:
            pass

    def _recover_profile(self) -> bool:
        """
        Thử khôi phục profile bị lỗi (Corrupted).

        Chiến lược:
        1. Backup profile hiện tại
        2. Tạo profile mới sạch sẽ
        3. Restore Cookies và Local State từ backup (để giữ đăng nhập)

        Returns:
            True nếu recovery thành công (đã tạo profile mới), False nếu thất bại
        """
        try:
            self.logger.log_step(
                step="PROFILE_RECOVERY",
                result="IN_PROGRESS",
                note="Detected corrupted profile. Starting auto-healing...",
                profile_path=str(self.profile_path),
            )

            # 1. Tạo backup path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = (
                self.profile_path.parent
                / f"{self.profile_path.name}_corrupted_{timestamp}"
            )

            # 2. Move profile hiện tại sang backup
            if self.profile_path.exists():
                # Đảm bảo kill hết process trước khi move
                self._check_and_kill_existing_processes()
                time.sleep(1)

                shutil.move(str(self.profile_path), str(backup_path))
                self.logger.log_step(
                    step="PROFILE_BACKUP",
                    result="SUCCESS",
                    note=f"Backed up corrupted profile to {backup_path}",
                )

            # 3. Tạo profile mới
            self.profile_path.mkdir(parents=True, exist_ok=True)

            # 4. Restore Cookies và settings quan trọng
            restore_items = [
                ("Default/Cookies", "Cookies"),
                ("Default/Local State", "Local State"),
                ("Default/Preferences", "Preferences"),
                ("Default/Network Action Predictor", "Network Action Predictor"),
            ]

            restored_count = 0
            for rel_path, name in restore_items:
                src_file = backup_path / rel_path
                dst_file = self.profile_path / rel_path

                if src_file.exists():
                    try:
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        restored_count += 1
                    except Exception as e:
                        self.logger.log_step(
                            step="PROFILE_RESTORE",
                            result="WARNING",
                            error=str(e),
                            note=f"Failed to restore {name}",
                        )

            self.logger.log_step(
                step="PROFILE_RECOVERY",
                result="SUCCESS",
                note=f"Created fresh profile and restored {restored_count} critical files",
                restored_files=restored_count,
            )
            return True

        except Exception as e:
            self.logger.log_step(
                step="PROFILE_RECOVERY",
                result="FAILED",
                error=str(e),
                note="Fatal error during profile recovery",
            )
            return False

    async def start(self) -> None:
        """
        Khởi động browser với persistent profile.

        Sử dụng launch_persistent_context để tự động lưu cookie/localStorage.
        Browser chạy ở chế độ headed (không headless).

        Có cơ chế Auto-Healing: Nếu launch thất bại do profile lỗi,
        tự động backup và tạo profile mới rồi thử lại.

        Raises:
            RuntimeError: Nếu browser không khởi động được
        """
        # Outer loop cho healing retry (thử tối đa 2 lần: 1 lần thường, 1 lần sau healing)
        max_healing_attempts = 2
        last_error = None

        for healing_attempt in range(max_healing_attempts):
            try:
                await self._start_internal()
                return  # Thành công
            except Exception as e:
                last_error = e
                is_corruption_error = (
                    "Target page, context or browser has been closed" in str(e)
                    or "crash" in str(e).lower()
                )

                if healing_attempt < max_healing_attempts - 1 and is_corruption_error:
                    self.logger.log_step(
                        step="BROWSER_HEALING",
                        result="INFO",
                        note="Launch failed likely due to corruption. Attempting to heal profile...",
                    )
                    # Thử recover profile
                    if self._recover_profile():
                        continue  # Retry với profile mới

                # Nếu không heal được hoặc đã hết lượt
                raise last_error

    async def _start_internal(self) -> None:
        """Logic khởi động browser thực tế (được gọi bởi start)."""
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.log_step(
                step="BROWSER_START",
                result="IN_PROGRESS",
                account_id=self.account_id,
                profile_path=str(self.profile_path),
            )

            # Kiểm tra và kill các process Chrome đang sử dụng profile này
            self._check_and_kill_existing_processes()

            # Acquire lock để tránh multiple instances
            if not self._acquire_lock():
                raise RuntimeError(
                    f"Profile đang được sử dụng bởi process khác. "
                    f"Chrome không cho phép nhiều instance cùng sử dụng một profile. "
                    f"Vui lòng đợi process khác kết thúc hoặc kill process đó."
                )

            # Cleanup SingletonLock file nếu có (tránh lỗi "profile already in use")
            singleton_lock_path = self.profile_path / "SingletonLock"
            singleton_socket_path = self.profile_path / "SingletonSocket"
            singleton_cookie_path = self.profile_path / "SingletonCookie"
            lockfile_path = self.profile_path / "lockfile"

            # Cleanup tất cả lock files
            for lock_file in [
                singleton_lock_path,
                singleton_socket_path,
                singleton_cookie_path,
                lockfile_path,
            ]:
                if lock_file.exists():
                    try:
                        lock_file.unlink()
                        self.logger.log_step(
                            step="CLEANUP_LOCK_FILE",
                            result="SUCCESS",
                            note=f"Removed stale lock file: {lock_file.name}",
                        )
                    except Exception as e:
                        self.logger.log_step(
                            step="CLEANUP_LOCK_FILE",
                            result="WARNING",
                            error=str(e),
                            note=f"Could not remove {lock_file.name} (may be in use)",
                        )

            # Đảm bảo profile directory có quyền ghi
            try:
                # Test write permission
                test_file = self.profile_path / ".write_test"
                test_file.touch()
                test_file.unlink()
            except Exception as e:
                self.logger.log_step(
                    step="CHECK_PROFILE_PERMISSIONS",
                    result="WARNING",
                    error=str(e),
                    note="Profile directory may not have write permissions",
                )

            # Khởi động Playwright
            # Ensure DISPLAY is set right before launch (may have been cleared since import)
            if not os.environ.get("DISPLAY"):
                if os.path.exists("/tmp/.X11-unix/X0") or os.path.exists(
                    "/mnt/wslg/.X11-unix"
                ):
                    os.environ["DISPLAY"] = ":0"
                    self.logger.log_step(
                        step="SET_DISPLAY",
                        result="SUCCESS",
                        note="Set DISPLAY=:0 for WSL/WSLg environment",
                    )
            self.playwright = await async_playwright().start()

            # Khởi động browser với persistent context
            # Tự động xử lý lưu cookie/localStorage
            # Thêm các flags để tránh lỗi trong WSL/headless environments
            chrome_args = [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                # GPU và display flags (tránh lỗi GPU trong WSL)
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-gpu-sandbox",
                "--disable-gpu-process-crash-limit",
                # SSL fix (tránh lỗi SSL handshake trong WSL)
                "--ignore-certificate-errors",
                "--ignore-ssl-errors",
                # DBus và system service flags (tránh lỗi DBus trong WSL)
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-breakpad",
                "--disable-component-update",
                "--disable-default-apps",
                "--disable-extensions",
                "--disable-features=TranslateUI",
                "--disable-hang-monitor",
                "--disable-ipc-flooding-protection",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-renderer-backgrounding",
                "--disable-sync",
                "--disable-translate",
                # Performance và stability flags
                "--metrics-recording-only",
                "--no-first-run",
                "--no-default-browser-check",
                "--password-store=basic",
                "--use-mock-keychain",
                # Tránh lỗi crashpad và CPU frequency
                "--disable-crash-reporter",
                "--disable-crashpad",
            ]

            # Retry logic với exponential backoff
            max_retries = 3
            retry_delay = 2.0  # seconds

            for attempt in range(max_retries):
                try:
                    self.logger.log_step(
                        step="BROWSER_LAUNCH",
                        result="IN_PROGRESS",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        account_id=self.account_id,
                        profile_path=str(self.profile_path),
                    )

                    self.context = await self.playwright.chromium.launch_persistent_context(
                        user_data_dir=str(self.profile_path),
                        headless=False,  # Chế độ headed (bắt buộc)
                        slow_mo=self.config.browser.slow_mo,  # Làm chậm để debug
                        args=chrome_args,
                        ignore_default_args=[
                            "--enable-automation",  # Tránh conflict với flags khác
                        ],
                        viewport={"width": 1280, "height": 720},
                        locale="en-US",
                        timezone_id="America/New_York",
                        # Thêm timeout để tránh hang
                        timeout=60000,  # 60 seconds timeout
                    )

                    # Đợi lâu hơn để browser context ổn định hoàn toàn
                    await asyncio.sleep(2.0)

                    # Kiểm tra context có còn hoạt động không
                    if not self.context:
                        raise RuntimeError("Browser context is None after launch")

                    # Kiểm tra context có bị đóng không
                    try:
                        if self.context.pages is None:
                            raise RuntimeError(
                                "Browser context pages is None - context may be closed"
                            )
                    except Exception as pages_check_error:
                        # Nếu không thể truy cập pages, context có thể đã bị đóng
                        error_msg = str(pages_check_error)
                        if "closed" in error_msg.lower() or "Target" in error_msg:
                            raise RuntimeError(
                                f"Browser context was closed immediately after launch: {error_msg}"
                            )
                        raise

                    # Kiểm tra browser có còn hoạt động không
                    try:
                        browser = self.context.browser
                        if browser is None:
                            raise RuntimeError("Browser instance is None after launch")

                        # Kiểm tra browser có còn connected không
                        if (
                            hasattr(browser, "is_connected")
                            and not browser.is_connected()
                        ):
                            raise RuntimeError("Browser is not connected after launch")

                        # Kiểm tra thêm: thử truy cập pages để đảm bảo context còn sống
                        pages = self.context.pages
                        if pages is None:
                            raise RuntimeError(
                                "Cannot access context pages - context may be closed"
                            )

                    except Exception as check_error:
                        error_msg = str(check_error)
                        self.logger.log_step(
                            step="BROWSER_LAUNCH_CHECK",
                            result="FAILED",
                            error=error_msg,
                            attempt=attempt + 1,
                            account_id=self.account_id,
                        )
                        # Đóng context nếu có
                        if self.context:
                            try:
                                await self.context.close()
                            except:
                                pass
                            self.context = None
                        raise RuntimeError(
                            f"Browser context check failed: {error_msg}"
                        ) from check_error

                    # Thành công - tiếp tục với phần còn lại của start()
                    self.logger.log_step(
                        step="BROWSER_LAUNCH",
                        result="SUCCESS",
                        attempt=attempt + 1,
                        account_id=self.account_id,
                        profile_path=str(self.profile_path),
                    )
                    break  # Thoát khỏi retry loop

                except Exception as launch_error:
                    error_msg = str(launch_error)
                    self.logger.log_step(
                        step="BROWSER_LAUNCH",
                        result="FAILED",
                        error=error_msg,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        account_id=self.account_id,
                        profile_path=str(self.profile_path),
                    )

                    # Cleanup nếu có context
                    if self.context:
                        try:
                            await self.context.close()
                        except:
                            pass
                        self.context = None

                    # Nếu đây là lần thử cuối, raise error
                    if attempt == max_retries - 1:
                        # Cleanup thêm một lần nữa
                        self._check_and_kill_existing_processes()
                        await asyncio.sleep(1.0)

                        raise RuntimeError(
                            f"Không thể khởi động browser sau {max_retries} lần thử. "
                            f"Lỗi cuối cùng: {error_msg}. "
                            f"Profile path: {self.profile_path}. "
                            f"Vui lòng kiểm tra:\n"
                            f"1. Không có process Chrome nào đang sử dụng profile này\n"
                            f"2. Profile directory có quyền ghi\n"
                            f"3. Đủ bộ nhớ và tài nguyên hệ thống\n"
                            f"4. Playwright Chromium đã được cài đặt đúng"
                        ) from launch_error

                    # Đợi trước khi retry
                    wait_time = retry_delay * (2**attempt)  # Exponential backoff
                    self.logger.log_step(
                        step="BROWSER_LAUNCH_RETRY",
                        result="WAITING",
                        wait_time=wait_time,
                        next_attempt=attempt + 2,
                        account_id=self.account_id,
                    )
                    await asyncio.sleep(wait_time)

                    # Cleanup lại trước khi retry
                    self._check_and_kill_existing_processes()
                    # Re-cleanup lock files for next attempt
                    for lock_file in [
                        self.profile_path / "SingletonLock",
                        self.profile_path / "SingletonSocket",
                        self.profile_path / "SingletonCookie",
                        self.profile_path / "lockfile",
                    ]:
                        try:
                            if lock_file.exists():
                                lock_file.unlink()
                        except Exception:
                            pass
                    await asyncio.sleep(0.5)

            # Kiểm tra context sau khi retry loop kết thúc
            if not self.context:
                raise RuntimeError("Browser context is None after all retry attempts")

            # Lấy hoặc tạo page
            pages = self.context.pages
            if pages:
                self.page = pages[0]
            else:
                self.page = await self.context.new_page()

            # Kiểm tra page có hợp lệ không
            if not self.page or self.page.is_closed():
                raise RuntimeError("Page was closed immediately after creation")

            # Đặt timeout mặc định
            self.page.set_default_timeout(self.config.browser.timeout)

            # Verify browser is actually running
            try:
                # Try to get browser version to verify it's running
                browser_version = await self.context.browser.version()
                self.logger.log_step(
                    step="VERIFY_BROWSER",
                    result="SUCCESS",
                    note=f"Browser version: {browser_version}",
                    account_id=self.account_id,
                )
            except Exception as e:
                self.logger.log_step(
                    step="VERIFY_BROWSER",
                    result="WARNING",
                    error=str(e),
                    note="Could not verify browser version, but continuing",
                )

            # Bật request interception để debug (tùy chọn)
            if self.config.browser.debug:
                self.page.on(
                    "request",
                    lambda request: self.logger.debug(
                        f"Request: {request.method} {request.url}"
                    ),
                )
                self.page.on(
                    "response",
                    lambda response: self.logger.debug(
                        f"Response: {response.status} {response.url}"
                    ),
                )

            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000

            self.logger.log_step(
                step="BROWSER_START",
                result="SUCCESS",
                time_ms=elapsed_time,
                account_id=self.account_id,
            )

        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000

            self.logger.log_step(
                step="BROWSER_START",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Failed to start browser: {str(e)}",
                account_id=self.account_id,
            )
            raise RuntimeError(f"Không thể khởi động browser: {str(e)}") from e

    async def navigate(self, url: str, wait_until: str = "domcontentloaded") -> None:
        """
        Điều hướng đến URL với xử lý lỗi.

        Args:
            url: URL cần điều hướng đến
            wait_until: Điều kiện chờ (mặc định: "networkidle")

        Raises:
            RuntimeError: Nếu điều hướng thất bại
        """
        if not self.page:
            raise RuntimeError("Browser chưa khởi động. Gọi start() trước.")

        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.log_step(
                step="NAVIGATE",
                result="IN_PROGRESS",
                account_id=self.account_id,
                url=url,
            )

            await self.page.goto(url, wait_until=wait_until)

            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000

            self.logger.log_step(
                step="NAVIGATE",
                result="SUCCESS",
                time_ms=elapsed_time,
                account_id=self.account_id,
                url=url,
            )

        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000

            self.logger.log_step(
                step="NAVIGATE",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Navigation failed: {str(e)}",
                account_id=self.account_id,
                url=url,
            )
            raise RuntimeError(f"Điều hướng thất bại: {str(e)}") from e

    async def close(self) -> None:
        """
        Đóng browser và dọn dẹp tài nguyên.

        Đảm bảo dọn dẹp đúng cách browser, context, và các instance playwright.
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.log_step(
                step="BROWSER_CLOSE", result="IN_PROGRESS", account_id=self.account_id
            )

            # Đóng page
            if self.page:
                try:
                    await self.page.close()
                except Exception:
                    pass
                self.page = None

            # Đóng context (tự động lưu cookies/localStorage)
            if self.context:
                try:
                    await self.context.close()
                except Exception:
                    pass
                self.context = None

            # Đóng browser
            if self.browser:
                try:
                    await self.browser.close()
                except Exception:
                    pass
                self.browser = None

            # Dừng playwright
            if self.playwright:
                try:
                    await self.playwright.stop()
                except Exception:
                    pass
                self.playwright = None

            # Release lock
            self._release_lock()

            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000

            self.logger.log_step(
                step="BROWSER_CLOSE",
                result="SUCCESS",
                time_ms=elapsed_time,
                account_id=self.account_id,
            )

        except Exception as e:
            elapsed_time = (asyncio.get_event_loop().time() - start_time) * 1000

            self.logger.log_step(
                step="BROWSER_CLOSE",
                result="FAILED",
                time_ms=elapsed_time,
                error=f"Close failed: {str(e)}",
                account_id=self.account_id,
            )
            # Release lock ngay cả khi có lỗi
            try:
                self._release_lock()
            except Exception:
                pass
            # Không raise - cleanup nên là best effort
        finally:
            # Unregister instance
            if self in BrowserManager._active_instances:
                BrowserManager._active_instances.remove(self)

    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False

    def __str__(self) -> str:
        """Biểu diễn chuỗi."""
        account_str = self.account_id or "default"
        return f"BrowserManager(account={account_str}, profile={self.profile_path})"
