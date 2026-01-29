#!/usr/bin/env python3
"""
Git CLI Tool - Công cụ đẩy code lên git dễ dàng.

Usage:
    python scripts/cli/git_cli.py <command> [options]

Commands:
    status      - Xem git status
    add         - Add files (--all hoặc specific files)
    commit      - Commit với message
    push        - Push lên remote
    quick       - Quick push (add all, commit, push)
"""

import sys
import subprocess
import argparse
import getpass
import os
import json
from pathlib import Path
from typing import List, Optional


def print_header(title: str, width: int = 80) -> None:
    """
    Print formatted header.
    
    Args:
        title: Header title
        width: Width of header (default: 80)
    """
    print("=" * width)
    print(title)
    print("=" * width)


def print_section(title: str, width: int = 80) -> None:
    """
    Print formatted section.
    
    Args:
        title: Section title
        width: Width (default: 80)
    """
    print("\n" + "-" * width)
    print(title)
    print("-" * width)


class GitCLI:
    """CLI tool để quản lý git operations."""
    
    def __init__(self, repo_path: Optional[Path] = None, require_git: bool = False):
        """
        Initialize Git CLI tool.
        
        Args:
            repo_path: Path to git repository (default: current directory)
            require_git: Require git repository to exist (default: False, allows init)
        """
        self.repo_path = repo_path or Path.cwd()
        self.repo_path = self.repo_path.resolve()
        
        # Verify git repository only if required
        if require_git and not (self.repo_path / ".git").exists():
            raise ValueError(f"Không phải git repository: {self.repo_path}")
    
    def _setup_github_ssh(self) -> None:
        """
        Setup GitHub SSH host key in known_hosts to avoid interactive prompt.
        """
        try:
            # Check if github.com is already in known_hosts
            ssh_dir = Path.home() / ".ssh"
            known_hosts = ssh_dir / "known_hosts"
            
            # Check if already configured
            if known_hosts.exists():
                with open(known_hosts, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Check for github.com entries
                    if 'github.com' in content:
                        # Verify it's a valid entry (not just a comment)
                        lines = content.split('\n')
                        for line in lines:
                            if 'github.com' in line and not line.strip().startswith('#'):
                                return  # Already configured
            
            # Ensure .ssh directory exists
            ssh_dir.mkdir(mode=0o700, exist_ok=True)
            
            # Use ssh-keyscan to get GitHub host keys
            print("🔑 Đang setup SSH host key cho GitHub...")
            result = subprocess.run(
                ['ssh-keyscan', '-t', 'rsa,ecdsa,ed25519', 'github.com'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and result.stdout:
                # Append to known_hosts
                with open(known_hosts, 'a', encoding='utf-8') as f:
                    # Add newline if file doesn't end with one
                    if known_hosts.exists() and known_hosts.stat().st_size > 0:
                        f.write('\n')
                    f.write(result.stdout.strip())
                
                # Set proper permissions
                known_hosts.chmod(0o600)
                print("✅ Đã thêm GitHub host key vào known_hosts")
            else:
                raise ValueError("ssh-keyscan failed to get GitHub host keys")
        except FileNotFoundError:
            print("⚠️  ssh-keyscan không được tìm thấy")
            print("   Vui lòng chạy thủ công: ssh-keyscan github.com >> ~/.ssh/known_hosts")
        except Exception as e:
            # Non-critical, just warn
            print(f"⚠️  Không thể tự động setup SSH host key: {e}")
            print("   Vui lòng chạy thủ công:")
            print("   ssh-keyscan github.com >> ~/.ssh/known_hosts")
    
    def _run_git_command(
        self,
        command: List[str],
        check: bool = True,
        capture_output: bool = False
    ) -> subprocess.CompletedProcess:
        """
        Run git command.
        
        Args:
            command: Git command as list (e.g., ['status', '--short'])
            check: Raise exception on error (default: True)
            capture_output: Capture output (default: False)
        
        Returns:
            CompletedProcess result
        
        Raises:
            ValueError: If git is not installed
            subprocess.CalledProcessError: If command fails and check=True
        """
        # Check if git is installed
        try:
            subprocess.run(
                ['git', '--version'],
                check=True,
                capture_output=True,
                timeout=5
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            raise ValueError(
                "Git không được cài đặt hoặc không có trong PATH.\n"
                "   Vui lòng cài đặt Git: https://git-scm.com/downloads"
            )
        
        git_cmd = ['git', '-C', str(self.repo_path)] + command
        
        # Setup SSH environment for non-interactive operations
        env = os.environ.copy()
        
        # Check if this is an SSH operation (push/pull/fetch/clone)
        is_ssh_operation = any(cmd in command for cmd in ['push', 'pull', 'fetch', 'clone'])
        
        # If SSH operation, setup GitHub SSH host key and configure SSH
        if is_ssh_operation:
            # Try to setup GitHub SSH host key if needed
            try:
                self._setup_github_ssh()
            except Exception:
                pass  # Non-critical, continue anyway
            
            # Use GIT_SSH_COMMAND to auto-accept host keys for GitHub
            # This prevents interactive prompts
            if 'GIT_SSH_COMMAND' not in env:
                env['GIT_SSH_COMMAND'] = 'ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile=~/.ssh/known_hosts'
        
        # #region agent log
        with open('.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"location": "git_cli.py:180", "message": "_run_git_command: executing", "data": {"cmd": git_cmd, "check": check, "capture_output": capture_output}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
        # #endregion
        try:
            result = subprocess.run(
                git_cmd,
                check=check,
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                errors='replace',  # Replace invalid UTF-8 characters instead of raising error
                timeout=300,  # 5 minutes timeout
                env=env
            )
            # #region agent log
            with open('.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"location": "git_cli.py:195", "message": "_run_git_command: success", "data": {"returncode": result.returncode, "has_stdout": bool(result.stdout), "has_stderr": bool(result.stderr)}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
            # #endregion
            return result
        except subprocess.CalledProcessError as e:
            # #region agent log
            with open('.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"location": "git_cli.py:198", "message": "_run_git_command: CalledProcessError", "data": {"has_stderr": bool(e.stderr), "has_stdout": bool(e.stdout), "stderr_preview": str(e.stderr)[:200] if e.stderr else None, "stdout_preview": str(e.stdout)[:200] if e.stdout else None, "capture_output": capture_output}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A,B"}) + "\n")
            # #endregion
            # Get error message from stderr, stdout, or exception
            # Handle encoding errors gracefully
            error_msg = ""
            try:
                if e.stderr:
                    error_msg += e.stderr
                if e.stdout:
                    # Always include stdout if available, not just for Permission denied
                    error_msg += " " + e.stdout
            except (UnicodeDecodeError, UnicodeError):
                # If encoding error, try to decode with errors='replace'
                try:
                    if e.stderr:
                        error_msg += e.stderr.decode('utf-8', errors='replace')
                    if e.stdout:
                        error_msg += " " + e.stdout.decode('utf-8', errors='replace')
                except (AttributeError, TypeError):
                    # If already string or other issue, use str() with error handling
                    if e.stderr:
                        error_msg += str(e.stderr)
                    if e.stdout:
                        error_msg += " " + str(e.stdout)
            if not error_msg:
                error_msg = str(e)
            # #region agent log
            with open('.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"location": "git_cli.py:207", "message": "_run_git_command: error message built", "data": {"error_msg_length": len(error_msg), "error_msg_preview": error_msg[:200]}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "B"}) + "\n")
            # #endregion
            
            print(f"❌ Git command failed: {' '.join(git_cmd)}")
            if error_msg.strip():
                print(f"   Error: {error_msg.strip()}")
            
            # Check for authentication errors
            if "Authentication failed" in error_msg or "Invalid username or token" in error_msg or "Password authentication is not supported" in error_msg:
                print("\n" + "=" * 80)
                print("⚠️  AUTHENTICATION ERROR")
                print("=" * 80)
                print("GitHub không còn hỗ trợ password authentication.")
                print("\nCó 2 cách để giải quyết:")
                print("\n1. Sử dụng Personal Access Token (PAT):")
                print("   - Tạo token tại: https://github.com/settings/tokens")
                print("   - Khi push, sử dụng token thay vì password")
                print("   - Hoặc cấu hình credential helper:")
                print("     git config --global credential.helper store")
                print("     (Sau đó push lại và nhập token)")
                print("\n2. Sử dụng SSH (khuyến nghị):")
                print("   - Setup SSH key: https://docs.github.com/en/authentication/connecting-to-github-with-ssh")
                print("   - Đổi remote URL sang SSH:")
                print("     git remote set-url origin git@github.com:dthanhvu03/threadsauto.git")
                print("\n" + "=" * 80)
            
            # Check for SSH host key verification errors
            if "Host key verification failed" in error_msg or "authenticity of host" in error_msg.lower():
                print("\n" + "=" * 80)
                print("⚠️  SSH HOST KEY VERIFICATION ERROR")
                print("=" * 80)
                print("SSH cần xác nhận host key của GitHub.")
                print("\nĐang tự động setup...")
                try:
                    self._setup_github_ssh()
                    print("\n✅ Đã setup SSH host key. Vui lòng thử push lại:")
                    print("   python scripts/cli/git_cli.py push")
                except Exception as setup_error:
                    print(f"\n❌ Không thể tự động setup: {setup_error}")
                    print("\nVui lòng chạy thủ công:")
                    print("   ssh-keyscan github.com >> ~/.ssh/known_hosts")
                    print("\nHoặc chấp nhận host key khi được hỏi:")
                    print("   ssh -T git@github.com")
                    print("   (Nhập 'yes' khi được hỏi)")
                print("=" * 80)
            
            # Check for SSH public key authentication errors
            if "Permission denied (publickey)" in error_msg or ("Permission denied" in error_msg and "publickey" in error_msg):
                print("\n" + "=" * 80)
                print("⚠️  SSH PUBLIC KEY AUTHENTICATION ERROR")
                print("=" * 80)
                print("SSH key chưa được setup hoặc chưa được add vào GitHub.")
                print("\nCác bước để setup SSH key:")
                print("\n1. Kiểm tra xem đã có SSH key chưa:")
                print("   ls -la ~/.ssh/id_*.pub")
                print("\n2. Nếu chưa có, tạo SSH key mới:")
                print("   ssh-keygen -t ed25519 -C \"your_email@example.com\"")
                print("   (Nhấn Enter để chấp nhận đường dẫn mặc định)")
                print("   (Nhấn Enter để không đặt passphrase hoặc đặt nếu muốn)")
                print("\n3. Copy public key:")
                print("   cat ~/.ssh/id_ed25519.pub")
                print("   (Hoặc: cat ~/.ssh/id_rsa.pub nếu dùng RSA)")
                print("\n4. Thêm SSH key vào GitHub:")
                print("   - Truy cập: https://github.com/settings/keys")
                print("   - Click 'New SSH key'")
                print("   - Paste public key vào")
                print("   - Click 'Add SSH key'")
                print("\n5. Test SSH connection:")
                print("   ssh -T git@github.com")
                print("   (Nếu thành công sẽ thấy: 'Hi username! You've successfully authenticated...')")
                print("\n6. Sau đó thử push lại:")
                print("   python scripts/cli/git_cli.py push")
                print("=" * 80)
            
            # Check for rejected push (remote has changes)
            if "rejected" in error_msg.lower() and "fetch first" in error_msg.lower():
                print("\n" + "=" * 80)
                print("⚠️  PUSH REJECTED - REMOTE HAS CHANGES")
                print("=" * 80)
                print("Remote repository có code mà local chưa có.")
                print("Cần pull remote changes trước khi push.")
                print("\nCó 2 cách giải quyết:")
                print("\n1. Pull và merge (khuyến nghị):")
                print("   python scripts/cli/git_cli.py pull")
                print("   # Sau đó push lại:")
                print("   python scripts/cli/git_cli.py push")
                print("\n2. Pull với rebase (giữ lịch sử sạch hơn):")
                print("   python scripts/cli/git_cli.py pull --rebase")
                print("   # Sau đó push lại:")
                print("   python scripts/cli/git_cli.py push")
                print("\n⚠️  LƯU Ý: Không nên dùng --force trừ khi bạn chắc chắn muốn ghi đè remote!")
                print("=" * 80)
            
            raise
        except subprocess.TimeoutExpired:
            raise ValueError(f"Git command timeout: {' '.join(git_cmd)}")
    
    def status(self, short: bool = False) -> None:
        """
        Xem git status.
        
        Args:
            short: Use short format (default: False)
        
        Raises:
            ValueError: If not a git repository
        """
        # Check if git repository exists
        if not (self.repo_path / ".git").exists():
            raise ValueError(
                f"Không phải git repository: {self.repo_path}\n"
                f"   Vui lòng chạy: python scripts/cli/git_cli.py init"
            )
        
        print_header("📊 GIT STATUS")
        print(f"Repository: {self.repo_path}\n")
        
        command = ['status', '--short'] if short else ['status']
        result = self._run_git_command(command, check=False, capture_output=True)
        
        if result.stdout:
            print(result.stdout)
        else:
            print("✅ Working tree clean - không có thay đổi")
        
        # Show branch info
        branch_result = self._run_git_command(
            ['branch', '--show-current'],
            check=False,
            capture_output=True
        )
        if branch_result.stdout:
            current_branch = branch_result.stdout.strip()
            print(f"\n🌿 Current branch: {current_branch}")
        
        # Show remote info
        remote_result = self._run_git_command(
            ['remote', '-v'],
            check=False,
            capture_output=True
        )
        if remote_result.stdout:
            print("\n🔗 Remotes:")
            print(remote_result.stdout)
        else:
            print("\n⚠️  Chưa có remote repository được setup")
    
    def add(self, files: Optional[List[str]] = None, all_files: bool = False) -> None:
        """
        Add files to staging.
        
        Args:
            files: List of files to add (default: None)
            all_files: Add all files (default: False)
        
        Raises:
            ValueError: If not a git repository or invalid arguments
        """
        # Check if git repository exists
        if not (self.repo_path / ".git").exists():
            raise ValueError(
                f"Không phải git repository: {self.repo_path}\n"
                f"   Vui lòng chạy: python scripts/cli/git_cli.py init"
            )
        
        if all_files:
            print_header("📦 ADDING ALL FILES")
            self._run_git_command(['add', '-A'])
            print("✅ Đã add tất cả files")
        elif files:
            print_header(f"📦 ADDING FILES: {len(files)} files")
            added_count = 0
            for file in files:
                file_path = self.repo_path / file
                if not file_path.exists():
                    print(f"⚠️  File không tồn tại: {file}")
                    continue
                try:
                    self._run_git_command(['add', file])
                    print(f"✅ Added: {file}")
                    added_count += 1
                except subprocess.CalledProcessError as e:
                    print(f"❌ Không thể add file {file}: {e}")
            
            if added_count == 0:
                print("⚠️  Không có file nào được add")
                return
        else:
            raise ValueError("Cần chỉ định --all hoặc danh sách files")
        
        # Show status after add
        print_section("Status sau khi add:")
        self.status(short=True)
    
    def _check_git_config(self) -> tuple[bool, Optional[str], Optional[str]]:
        """
        Check if Git user config is set.
        
        Returns:
            Tuple of (is_configured, user_name, user_email)
        """
        name_result = self._run_git_command(
            ['config', 'user.name'],
            check=False,
            capture_output=True
        )
        email_result = self._run_git_command(
            ['config', 'user.email'],
            check=False,
            capture_output=True
        )
        
        user_name = name_result.stdout.strip() if name_result.returncode == 0 and name_result.stdout else None
        user_email = email_result.stdout.strip() if email_result.returncode == 0 and email_result.stdout else None
        
        is_configured = user_name and user_email
        return is_configured, user_name, user_email
    
    def _setup_git_user(self, name: Optional[str] = None, email: Optional[str] = None, global_config: bool = False) -> None:
        """
        Setup Git user name and email.
        
        Args:
            name: User name (if None, will prompt or use default)
            email: User email (if None, will prompt or use default)
            global_config: Use global config (default: False, use local)
        """
        config_scope = '--global' if global_config else '--local'
        
        if not name:
            # Try to get from system or use default
            name = os.getenv('GIT_USER_NAME') or getpass.getuser() or 'Git User'
        
        if not email:
            # Try to get from system or use default
            email = os.getenv('GIT_USER_EMAIL') or f'{name.lower().replace(" ", ".")}@example.com'
        
        self._run_git_command(['config', config_scope, 'user.name', name])
        self._run_git_command(['config', config_scope, 'user.email', email])
        
        print(f"✅ Đã cấu hình Git user:")
        print(f"   Name: {name}")
        print(f"   Email: {email}")
        print(f"   Scope: {'global' if global_config else 'local'}")
    
    def commit(
        self,
        message: str,
        allow_empty: bool = False,
        no_verify: bool = False,
        auto_setup_user: bool = True
    ) -> None:
        """
        Commit changes.
        
        Args:
            message: Commit message
            allow_empty: Allow empty commit (default: False)
            no_verify: Skip hooks (default: False)
            auto_setup_user: Auto setup Git user if not configured (default: True)
        
        Raises:
            ValueError: If not a git repository or invalid message
        """
        # Check if git repository exists
        if not (self.repo_path / ".git").exists():
            raise ValueError(
                f"Không phải git repository: {self.repo_path}\n"
                f"   Vui lòng chạy: python scripts/cli/git_cli.py init"
            )
        
        # Validate commit message
        if not message or not message.strip():
            raise ValueError("Commit message không được để trống")
        
        # Check Git user config
        is_configured, _, _ = self._check_git_config()
        if not is_configured:
            if auto_setup_user:
                print("⚠️  Git user chưa được cấu hình, đang tự động cấu hình...")
                self._setup_git_user(global_config=False)
            else:
                raise ValueError(
                    "Git user chưa được cấu hình.\n"
                    "   Vui lòng chạy:\n"
                    "   git config user.name \"Your Name\"\n"
                    "   git config user.email \"your.email@example.com\""
                )
        
        print_header("💾 COMMITTING CHANGES")
        
        # Check if there are changes to commit
        status_result = self._run_git_command(
            ['status', '--short'],
            check=False,
            capture_output=True
        )
        
        if not status_result.stdout.strip() and not allow_empty:
            print("⚠️  Không có thay đổi nào để commit")
            return
        
        # Build commit command
        commit_cmd = ['commit', '-m', message]
        if allow_empty:
            commit_cmd.append('--allow-empty')
        if no_verify:
            commit_cmd.append('--no-verify')
        
        try:
            self._run_git_command(commit_cmd)
            print(f"✅ Đã commit: {message}")
            
            # Show last commit
            log_result = self._run_git_command(
                ['log', '-1', '--oneline'],
                check=False,
                capture_output=True
            )
            if log_result.stdout:
                print(f"\n📝 Last commit: {log_result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            # Check if error is about user identity
            if "Author identity unknown" in str(e) or "empty ident name" in str(e):
                if auto_setup_user:
                    print("\n⚠️  Phát hiện lỗi cấu hình user, đang tự động sửa...")
                    self._setup_git_user(global_config=False)
                    # Retry commit
                    self._run_git_command(commit_cmd)
                    print(f"✅ Đã commit: {message}")
                else:
                    raise ValueError(
                        "Git user chưa được cấu hình.\n"
                        "   Vui lòng chạy:\n"
                        "   git config user.name \"Your Name\"\n"
                        "   git config user.email \"your.email@example.com\""
                    )
            else:
                raise
    
    def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        set_upstream: bool = False
    ) -> None:
        """
        Push to remote.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            force: Force push (default: False)
            set_upstream: Set upstream (default: False)
        """
        print_header("🚀 PUSHING TO REMOTE")
        
        # Get current branch if not specified
        if not branch:
            branch_result = self._run_git_command(
                ['branch', '--show-current'],
                check=True,
                capture_output=True
            )
            branch = branch_result.stdout.strip()
        
        print(f"Remote: {remote}")
        print(f"Branch: {branch}\n")
        
        # Get current branch to check if we need to create new branch
        current_branch_result = self._run_git_command(
            ['branch', '--show-current'],
            check=False,
            capture_output=True
        )
        current_branch = current_branch_result.stdout.strip() if current_branch_result.stdout else None
        
        # Check if branch exists locally
        branch_check = self._run_git_command(
            ['show-ref', '--verify', '--quiet', f'refs/heads/{branch}'],
            check=False,
            capture_output=True
        )
        if branch_check.returncode != 0:
            # Branch doesn't exist locally - auto-create it from current branch
            if current_branch:
                print(f"⚠️  Branch '{branch}' không tồn tại, đang tạo từ current branch '{current_branch}'...")
                self._run_git_command(['checkout', '-b', branch])
                print(f"✅ Đã tạo và checkout branch: {branch}")
            else:
                # No current branch (detached HEAD or no commits), create orphan branch
                print(f"⚠️  Branch '{branch}' không tồn tại, đang tạo branch mới...")
                self._run_git_command(['checkout', '-b', branch])
                print(f"✅ Đã tạo và checkout branch: {branch}")
        
        # Check if using SSH and setup GitHub host key if needed
        remote_result = self._run_git_command(
            ['remote', 'get-url', remote],
            check=False,
            capture_output=True
        )
        if remote_result.returncode == 0 and remote_result.stdout:
            remote_url = remote_result.stdout.strip()
            if remote_url.startswith('git@') or 'github.com' in remote_url:
                self._setup_github_ssh()
        
        # Build push command
        push_cmd = ['push']
        if force:
            push_cmd.append('--force')
        if set_upstream:
            push_cmd.append('--set-upstream')
            push_cmd.append(remote)
            push_cmd.append(branch)
        else:
            push_cmd.append(remote)
            push_cmd.append(branch)
        
        self._run_git_command(push_cmd)
        print(f"✅ Đã push {branch} lên {remote}")
    
    def quick_push(
        self,
        message: str,
        remote: str = "origin",
        branch: Optional[str] = None,
        force: bool = False,
        no_verify: bool = False
    ) -> None:
        """
        Quick push: add all, commit, push.
        Auto-setup git repository and remote if needed.
        
        Args:
            message: Commit message
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            force: Force push (default: False)
            no_verify: Skip hooks (default: False)
        """
        print_header("⚡ QUICK PUSH")
        print(f"Repository: {self.repo_path}\n")
        
        # Check if git repository exists
        if not (self.repo_path / ".git").exists():
            print("⚠️  Git repository chưa được khởi tạo")
            print("   Đang khởi tạo git repository...")
            self.init()
        
        # Check if remote exists
        remote_result = self._run_git_command(
            ['remote', 'show', remote],
            check=False,
            capture_output=True
        )
        if remote_result.returncode != 0:
            print(f"⚠️  Remote '{remote}' chưa được setup")
            print(f"   Vui lòng chạy: python scripts/cli/git_cli.py setup-remote <url> --name {remote}")
            print("   Hoặc sử dụng: python scripts/cli/git_cli.py setup <url>")
            raise ValueError(f"Remote '{remote}' chưa được setup. Vui lòng setup remote trước.")
        
        # Step 1: Status
        print_section("Step 1: Checking status")
        self.status(short=True)
        
        # Step 2: Add all
        print_section("Step 2: Adding all files")
        self.add(all_files=True)
        
        # Step 3: Commit
        print_section("Step 3: Committing")
        self.commit(message, no_verify=no_verify)
        
        # Step 4: Push
        print_section("Step 4: Pushing")
        # Use set_upstream if branch doesn't have upstream yet
        branch_result = self._run_git_command(
            ['branch', '--show-current'],
            check=False,
            capture_output=True
        )
        current_branch = branch_result.stdout.strip() if branch_result.stdout else None
        target_branch = branch or current_branch
        
        # If target branch is different from current branch, check if it exists
        if target_branch and target_branch != current_branch:
            branch_check = self._run_git_command(
                ['show-ref', '--verify', '--quiet', f'refs/heads/{target_branch}'],
                check=False,
                capture_output=True
            )
            if branch_check.returncode != 0:
                # Branch doesn't exist, create it from current branch
                print(f"⚠️  Branch '{target_branch}' không tồn tại, đang tạo từ current branch '{current_branch}'...")
                self._run_git_command(['checkout', '-b', target_branch])
                print(f"✅ Đã tạo và checkout branch: {target_branch}")
        
        # Check if upstream exists
        upstream_result = self._run_git_command(
            ['rev-parse', '--abbrev-ref', f'{target_branch}@{{upstream}}'],
            check=False,
            capture_output=True
        )
        set_upstream = upstream_result.returncode != 0
        
        self.push(remote=remote, branch=target_branch, force=force, set_upstream=set_upstream)
        
        print_header("✅ QUICK PUSH COMPLETED")
    
    def pull(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        rebase: bool = False
    ) -> None:
        """
        Pull from remote.
        
        Args:
            remote: Remote name (default: origin)
            branch: Branch name (default: current branch)
            rebase: Use rebase instead of merge (default: False)
        """
        print_header("⬇️  PULLING FROM REMOTE")
        
        # Get current branch if not specified
        if not branch:
            branch_result = self._run_git_command(
                ['branch', '--show-current'],
                check=True,
                capture_output=True
            )
            branch = branch_result.stdout.strip()
        
        print(f"Remote: {remote}")
        print(f"Branch: {branch}\n")
        
        # Build pull command
        # Default to merge strategy if not specified to avoid divergent branches error
        pull_cmd = ['pull']
        if rebase:
            pull_cmd.append('--rebase')
        else:
            # Explicitly use merge strategy to avoid "divergent branches" error
            pull_cmd.append('--no-rebase')
        pull_cmd.append(remote)
        pull_cmd.append(branch)
        
        try:
            # #region agent log
            with open('.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"location": "git_cli.py:708", "message": "pull: attempting initial pull", "data": {"cmd": pull_cmd, "remote": remote, "branch": branch}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A"}) + "\n")
            # #endregion
            # Use capture_output=True to capture error messages for proper error handling
            self._run_git_command(pull_cmd, capture_output=True)
            print(f"✅ Đã pull {branch} từ {remote}")
        except subprocess.CalledProcessError as e:
            # #region agent log
            with open('.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"location": "git_cli.py:712", "message": "pull: exception caught", "data": {"has_stderr": bool(e.stderr), "has_stdout": bool(e.stdout), "stderr_preview": str(e.stderr)[:100] if e.stderr else None, "stdout_preview": str(e.stdout)[:100] if e.stdout else None, "exception_str": str(e)[:200]}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "A,B"}) + "\n")
            # #endregion
            # Get error message from stderr, stdout, or exception
            error_msg = ""
            if e.stderr:
                error_msg += e.stderr
            if e.stdout:
                error_msg += " " + e.stdout
            if not error_msg:
                error_msg = str(e)
            error_msg_lower = error_msg.lower()
            
            # #region agent log
            with open('.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"location": "git_cli.py:720", "message": "pull: error message extracted", "data": {"error_msg_length": len(error_msg), "error_msg_preview": error_msg[:200], "error_msg_lower_preview": error_msg_lower[:200], "contains_unrelated": "refusing to merge unrelated histories" in error_msg_lower, "contains_divergent": "divergent branches" in error_msg_lower}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "C"}) + "\n")
            # #endregion
            
            # Check for unrelated histories error
            if "refusing to merge unrelated histories" in error_msg_lower:
                # #region agent log
                with open('.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"location": "git_cli.py:723", "message": "pull: unrelated histories detected, retrying", "data": {}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}) + "\n")
                # #endregion
                print("\n" + "=" * 80)
                print("⚠️  UNRELATED HISTORIES DETECTED")
                print("=" * 80)
                print("Local và remote repositories có lịch sử commit không liên quan.")
                print("Đang thử pull với --allow-unrelated-histories...")
                print("=" * 80)
                # Retry with --allow-unrelated-histories
                pull_cmd_retry = ['pull', '--no-rebase', '--allow-unrelated-histories', remote, branch]
                # #region agent log
                with open('.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"location": "git_cli.py:731", "message": "pull: executing retry command", "data": {"retry_cmd": pull_cmd_retry}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "E"}) + "\n")
                # #endregion
                try:
                    # Use capture_output=True to capture error messages for proper error handling
                    self._run_git_command(pull_cmd_retry, capture_output=True)
                    # #region agent log
                    with open('.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"location": "git_cli.py:733", "message": "pull: retry succeeded", "data": {}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "E"}) + "\n")
                    # #endregion
                    print(f"✅ Đã pull {branch} từ {remote} (với --allow-unrelated-histories)")
                except Exception as retry_error:
                    # #region agent log
                    with open('.cursor/debug.log', 'a') as f:
                        f.write(json.dumps({"location": "git_cli.py:738", "message": "pull: retry failed", "data": {"error_type": type(retry_error).__name__, "error_msg": str(retry_error)[:200]}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "E"}) + "\n")
                    # #endregion
                    raise
            # Check for unmerged files (merge conflict) error
            elif "unmerged files" in error_msg_lower or "unresolved conflict" in error_msg_lower:
                print("\n" + "=" * 80)
                print("⚠️  MERGE CONFLICT DETECTED")
                print("=" * 80)
                print("Có unmerged files từ lần merge trước.")
                print("Cần resolve conflicts trước khi pull tiếp.")
                print("\nCác bước để resolve:")
                print("\n1. Kiểm tra files có conflict:")
                print("   git status")
                print("\n2. Resolve conflicts trong các files:")
                print("   - Mở file có conflict")
                print("   - Tìm các markers: <<<<<<<, =======, >>>>>>>")
                print("   - Chọn code muốn giữ và xóa markers")
                print("\n3. Sau khi resolve xong, add files:")
                print("   python scripts/cli/git_cli.py add <file>")
                print("   # Hoặc add tất cả:")
                print("   python scripts/cli/git_cli.py add --all")
                print("\n4. Commit để hoàn tất merge:")
                print("   python scripts/cli/git_cli.py commit \"Resolve merge conflicts\"")
                print("\n5. Sau đó pull lại:")
                print("   python scripts/cli/git_cli.py pull")
                print("\nHoặc nếu muốn abort merge:")
                print("   git merge --abort")
                print("=" * 80)
            # Check for divergent branches error
            elif "divergent branches" in error_msg_lower or "Need to specify how to reconcile" in error_msg_lower:
                print("\n" + "=" * 80)
                print("⚠️  DIVERGENT BRANCHES DETECTED")
                print("=" * 80)
                print("Local và remote branches đã phân nhánh.")
                print("Đang thử pull với merge strategy...")
                print("=" * 80)
                # Retry with explicit merge strategy
                pull_cmd_retry = ['pull', '--no-rebase', remote, branch]
                # Use capture_output=True to capture error messages for proper error handling
                self._run_git_command(pull_cmd_retry, capture_output=True)
                print(f"✅ Đã pull {branch} từ {remote} (với merge)")
            else:
                # #region agent log
                with open('.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"location": "git_cli.py:796", "message": "pull: no matching error handler, re-raising", "data": {"error_msg_preview": error_msg[:200]}, "timestamp": int(__import__('time').time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "D"}) + "\n")
                # #endregion
                raise
    
    def init(self) -> bool:
        """
        Initialize git repository if not exists.
        
        Returns:
            True if repository was newly initialized, False if already exists
        """
        print_header("🔧 INITIALIZING GIT REPOSITORY")
        
        if (self.repo_path / ".git").exists():
            print("✅ Git repository đã tồn tại")
            return False
        
        self._run_git_command(['init'])
        print(f"✅ Đã khởi tạo git repository tại: {self.repo_path}")
        
        # Check if .gitignore exists
        gitignore_path = self.repo_path / ".gitignore"
        if not gitignore_path.exists():
            print("⚠️  Chưa có file .gitignore")
        else:
            print("✅ File .gitignore đã tồn tại")
        
        return True
    
    def setup_remote(
        self,
        url: str,
        name: str = "origin",
        force: bool = False,
        use_ssh: bool = False
    ) -> None:
        """
        Setup remote repository.
        
        Args:
            url: Remote repository URL (e.g., https://github.com/user/repo.git)
            name: Remote name (default: origin)
            force: Force update if remote exists (default: False)
            use_ssh: Convert HTTPS URL to SSH format (default: False)
        """
        print_header("🔗 SETTING UP REMOTE")
        
        # Convert HTTPS to SSH if requested
        if use_ssh and url.startswith('https://'):
            # Convert https://github.com/user/repo.git to git@github.com:user/repo.git
            url = url.replace('https://', '').replace('http://', '')
            if url.startswith('github.com/'):
                url = url.replace('github.com/', 'github.com:')
            url = f"git@{url}"
            print(f"📝 Đã chuyển đổi sang SSH URL: {url}")
        
        # Validate URL format
        if not url or not (url.startswith('http') or url.startswith('git@') or url.startswith('ssh://')):
            raise ValueError(f"Remote URL không hợp lệ: {url}")
        
        # Check existing remotes
        remote_result = self._run_git_command(
            ['remote', '-v'],
            check=False,
            capture_output=True
        )
        
        existing_remotes = {}
        if remote_result.stdout:
            for line in remote_result.stdout.strip().split('\n'):
                if line:
                    parts = line.split()
                    if len(parts) >= 2:
                        remote_name = parts[0]
                        remote_url = parts[1]
                        existing_remotes[remote_name] = remote_url
        
        # Check if remote already exists
        if name in existing_remotes:
            if existing_remotes[name] == url:
                print(f"✅ Remote '{name}' đã tồn tại với URL: {url}")
                return
            elif force:
                print(f"⚠️  Remote '{name}' đã tồn tại với URL: {existing_remotes[name]}")
                print(f"   Đang cập nhật thành: {url}")
                self._run_git_command(['remote', 'set-url', name, url])
                print(f"✅ Đã cập nhật remote '{name}'")
            else:
                raise ValueError(
                    f"Remote '{name}' đã tồn tại với URL: {existing_remotes[name]}\n"
                    f"   Sử dụng --force để cập nhật hoặc chọn tên remote khác"
                )
        else:
            # Add new remote
            self._run_git_command(['remote', 'add', name, url])
            print(f"✅ Đã thêm remote '{name}': {url}")
        
        # Show all remotes
        print_section("Remotes hiện tại:")
        remote_result = self._run_git_command(
            ['remote', '-v'],
            check=False,
            capture_output=True
        )
        if remote_result.stdout:
            print(remote_result.stdout)
    
    def setup(
        self,
        remote_url: str,
        commit_message: str = "Initial commit",
        remote_name: str = "origin",
        branch: str = "main"
    ) -> None:
        """
        Complete setup: init, remote, first commit, push.
        
        Args:
            remote_url: Remote repository URL
            commit_message: Initial commit message (default: "Initial commit")
            remote_name: Remote name (default: origin)
            branch: Branch name (default: main)
        """
        print_header("🚀 COMPLETE GIT SETUP")
        print(f"Repository: {self.repo_path}\n")
        
        # Step 1: Init
        print_section("Step 1: Initializing git repository")
        was_new = self.init()
        if not was_new:
            print("   Repository đã tồn tại, tiếp tục setup...")
        
        # Step 2: Setup remote
        print_section("Step 2: Setting up remote")
        self.setup_remote(remote_url, name=remote_name, force=False)
        
        # Step 3: Add all files
        print_section("Step 3: Adding all files")
        self.add(all_files=True)
        
        # Step 4: Commit
        print_section("Step 4: Creating initial commit")
        self.commit(commit_message, allow_empty=False, no_verify=False, auto_setup_user=True)
        
        # Step 5: Push with --set-upstream
        print_section("Step 5: Pushing to remote")
        # Check if branch exists, if not create it
        branch_result = self._run_git_command(
            ['branch', '--show-current'],
            check=False,
            capture_output=True
        )
        current_branch = branch_result.stdout.strip() if branch_result.stdout else None
        
        if not current_branch or current_branch != branch:
            # No branch yet or different branch, create and checkout
            self._run_git_command(['checkout', '-b', branch])
            print(f"✅ Đã tạo và checkout branch: {branch}")
        
        # Push with set-upstream
        self.push(remote=remote_name, branch=branch, force=False, set_upstream=True)
        
        print_header("✅ SETUP COMPLETED")
        print(f"Repository đã được setup và push lên {remote_name}/{branch}")


# ============ INTERACTIVE MENU SYSTEM ============

def prompt_input(prompt: str, default: Optional[str] = None) -> str:
    """
    Prompt for user input with optional default.
    
    Args:
        prompt: Prompt message
        default: Default value if user presses Enter
    
    Returns:
        User input or default value
    """
    if default:
        full_prompt = f"{prompt} (default: {default}): "
    else:
        full_prompt = f"{prompt}: "
    
    try:
        user_input = input(full_prompt).strip()
        return user_input if user_input else (default or "")
    except (KeyboardInterrupt, EOFError):
        print("\n\n⚠️  Đã hủy bởi user")
        sys.exit(0)


def prompt_yes_no(prompt: str, default: bool = False) -> bool:
    """
    Prompt for yes/no question.
    
    Args:
        prompt: Prompt message
        default: Default value (True for yes, False for no)
    
    Returns:
        True if yes, False if no
    """
    default_str = "Y/n" if default else "y/N"
    response = prompt_input(f"{prompt} ({default_str})", default="y" if default else "n")
    return response.lower() in ["y", "yes"]


def show_basic_menu(cli: GitCLI) -> None:
    """Display basic operations menu."""
    while True:
        print_header("📋 BASIC OPERATIONS")
        print("1. Status")
        print("2. Add files")
        print("3. Commit")
        print("0. Back to main menu")
        
        choice = prompt_input("\nChọn option (0-3)")
        
        if choice == "0":
            break
        elif choice == "1":
            try:
                cli.status()
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "2":
            try:
                add_choice = prompt_yes_no("Add tất cả files?", default=True)
                if add_choice:
                    cli.add(all_files=True)
                else:
                    files_input = prompt_input("Nhập danh sách files (cách nhau bởi dấu cách)")
                    if files_input:
                        files = files_input.split()
                        cli.add(files=files)
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "3":
            try:
                message = prompt_input("Commit message")
                if message:
                    cli.commit(message)
                else:
                    print("⚠️  Commit message không được để trống")
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_push_pull_menu(cli: GitCLI) -> None:
    """Display push/pull operations menu."""
    while True:
        print_header("📋 PUSH/PULL OPERATIONS")
        print("1. Push")
        print("2. Pull")
        print("3. Quick Push (add + commit + push)")
        print("0. Back to main menu")
        
        choice = prompt_input("\nChọn option (0-3)")
        
        if choice == "0":
            break
        elif choice == "1":
            try:
                remote = prompt_input("Remote name", default="origin")
                branch = prompt_input("Branch name (Enter để dùng current branch)", default="")
                force = prompt_yes_no("Force push?", default=False)
                set_upstream = prompt_yes_no("Set upstream?", default=False)
                cli.push(
                    remote=remote or "origin",
                    branch=branch if branch else None,
                    force=force,
                    set_upstream=set_upstream
                )
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "2":
            try:
                remote = prompt_input("Remote name", default="origin")
                branch = prompt_input("Branch name (Enter để dùng current branch)", default="")
                rebase = prompt_yes_no("Use rebase instead of merge?", default=False)
                cli.pull(
                    remote=remote or "origin",
                    branch=branch if branch else None,
                    rebase=rebase
                )
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "3":
            try:
                message = prompt_input("Commit message")
                if not message:
                    print("⚠️  Commit message không được để trống")
                else:
                    remote = prompt_input("Remote name", default="origin")
                    branch = prompt_input("Branch name (Enter để dùng current branch)", default="")
                    force = prompt_yes_no("Force push?", default=False)
                    no_verify = prompt_yes_no("Skip hooks (--no-verify)?", default=False)
                    cli.quick_push(
                        message=message,
                        remote=remote or "origin",
                        branch=branch if branch else None,
                        force=force,
                        no_verify=no_verify
                    )
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_setup_menu(cli: GitCLI) -> None:
    """Display setup operations menu."""
    while True:
        print_header("📋 SETUP OPERATIONS")
        print("1. Init repository")
        print("2. Setup remote")
        print("3. Complete setup (init + remote + commit + push)")
        print("0. Back to main menu")
        
        choice = prompt_input("\nChọn option (0-3)")
        
        if choice == "0":
            break
        elif choice == "1":
            try:
                cli.init()
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "2":
            try:
                url = prompt_input("Remote repository URL (e.g., https://github.com/user/repo.git)")
                if not url:
                    print("⚠️  URL không được để trống")
                else:
                    name = prompt_input("Remote name", default="origin")
                    force = prompt_yes_no("Force update if remote exists?", default=False)
                    use_ssh = prompt_yes_no("Convert HTTPS URL to SSH format?", default=False)
                    cli.setup_remote(
                        url=url,
                        name=name or "origin",
                        force=force,
                        use_ssh=use_ssh
                    )
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "3":
            try:
                remote_url = prompt_input("Remote repository URL (e.g., https://github.com/user/repo.git)")
                if not remote_url:
                    print("⚠️  URL không được để trống")
                else:
                    commit_message = prompt_input("Initial commit message", default="Initial commit")
                    remote_name = prompt_input("Remote name", default="origin")
                    branch = prompt_input("Branch name", default="main")
                    cli.setup(
                        remote_url=remote_url,
                        commit_message=commit_message or "Initial commit",
                        remote_name=remote_name or "origin",
                        branch=branch or "main"
                    )
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_advanced_menu(cli: GitCLI) -> None:
    """Display advanced operations menu."""
    while True:
        print_header("📋 ADVANCED OPERATIONS")
        print("1. Status (short format)")
        print("2. Add specific files")
        print("3. Commit with options")
        print("4. Push with options")
        print("5. Pull with options")
        print("0. Back to main menu")
        
        choice = prompt_input("\nChọn option (0-5)")
        
        if choice == "0":
            break
        elif choice == "1":
            try:
                cli.status(short=True)
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "2":
            try:
                files_input = prompt_input("Nhập danh sách files (cách nhau bởi dấu cách)")
                if files_input:
                    files = files_input.split()
                    cli.add(files=files)
                else:
                    print("⚠️  Cần nhập ít nhất một file")
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "3":
            try:
                message = prompt_input("Commit message")
                if not message:
                    print("⚠️  Commit message không được để trống")
                else:
                    allow_empty = prompt_yes_no("Allow empty commit?", default=False)
                    no_verify = prompt_yes_no("Skip hooks (--no-verify)?", default=False)
                    cli.commit(
                        message=message,
                        allow_empty=allow_empty,
                        no_verify=no_verify
                    )
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "4":
            try:
                remote = prompt_input("Remote name", default="origin")
                branch = prompt_input("Branch name (Enter để dùng current branch)", default="")
                force = prompt_yes_no("Force push?", default=False)
                set_upstream = prompt_yes_no("Set upstream?", default=False)
                cli.push(
                    remote=remote or "origin",
                    branch=branch if branch else None,
                    force=force,
                    set_upstream=set_upstream
                )
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        elif choice == "5":
            try:
                remote = prompt_input("Remote name", default="origin")
                branch = prompt_input("Branch name (Enter để dùng current branch)", default="")
                rebase = prompt_yes_no("Use rebase instead of merge?", default=False)
                cli.pull(
                    remote=remote or "origin",
                    branch=branch if branch else None,
                    rebase=rebase
                )
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_main_menu(cli: GitCLI) -> None:
    """Display main menu and handle navigation."""
    while True:
        print_header("📋 GIT CLI MENU")
        print("1. Basic Operations (status, add, commit)")
        print("2. Push/Pull Operations")
        print("3. Setup Operations")
        print("4. Advanced Operations")
        print("0. Exit")
        
        choice = prompt_input("\nChọn option (0-4)")
        
        if choice == "0":
            print("\n👋 Tạm biệt!")
            break
        elif choice == "1":
            show_basic_menu(cli)
        elif choice == "2":
            show_push_pull_menu(cli)
        elif choice == "3":
            show_setup_menu(cli)
        elif choice == "4":
            show_advanced_menu(cli)
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Git CLI Tool - Đẩy code lên git dễ dàng",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--repo',
        type=Path,
        default=Path.cwd(),
        help="Path to git repository (default: current directory)"
    )
    
    parser.add_argument(
        '--menu',
        action='store_true',
        help='Show interactive menu (ignores other arguments)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Xem git status')
    status_parser.add_argument('--short', action='store_true', help='Short format')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add files')
    add_parser.add_argument('--all', action='store_true', dest='all_files', help='Add all files')
    add_parser.add_argument('files', nargs='*', help='Files to add (optional if --all is used)')
    
    # Commit command
    commit_parser = subparsers.add_parser('commit', help='Commit changes')
    commit_parser.add_argument('message', help='Commit message')
    commit_parser.add_argument('--allow-empty', action='store_true', help='Allow empty commit')
    commit_parser.add_argument('--no-verify', action='store_true', help='Skip hooks')
    
    # Push command
    push_parser = subparsers.add_parser('push', help='Push to remote')
    push_parser.add_argument('--remote', default='origin', help='Remote name (default: origin)')
    push_parser.add_argument('--branch', help='Branch name (default: current branch)')
    push_parser.add_argument('--force', action='store_true', help='Force push')
    push_parser.add_argument('--set-upstream', action='store_true', help='Set upstream')
    
    # Quick push command
    quick_parser = subparsers.add_parser('quick', help='Quick push (add all, commit, push)')
    quick_parser.add_argument('message', help='Commit message')
    quick_parser.add_argument('--remote', default='origin', help='Remote name (default: origin)')
    quick_parser.add_argument('--branch', help='Branch name (default: current branch)')
    quick_parser.add_argument('--force', action='store_true', help='Force push')
    quick_parser.add_argument('--no-verify', action='store_true', help='Skip hooks')
    
    # Pull command
    pull_parser = subparsers.add_parser('pull', help='Pull from remote')
    pull_parser.add_argument('--remote', default='origin', help='Remote name (default: origin)')
    pull_parser.add_argument('--branch', help='Branch name (default: current branch)')
    pull_parser.add_argument('--rebase', action='store_true', help='Use rebase instead of merge')
    
    # Init command
    subparsers.add_parser('init', help='Khởi tạo git repository')
    
    # Setup-remote command
    setup_remote_parser = subparsers.add_parser('setup-remote', help='Thêm remote repository')
    setup_remote_parser.add_argument('url', help='Remote repository URL')
    setup_remote_parser.add_argument('--name', default='origin', help='Remote name (default: origin)')
    setup_remote_parser.add_argument('--force', action='store_true', help='Force update if remote exists')
    setup_remote_parser.add_argument('--ssh', action='store_true', dest='use_ssh', help='Convert HTTPS URL to SSH format')
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup tổng hợp (init + remote + commit + push)')
    setup_parser.add_argument('remote_url', help='Remote repository URL')
    setup_parser.add_argument('--message', default='Initial commit', help='Initial commit message (default: Initial commit)')
    setup_parser.add_argument('--remote-name', default='origin', help='Remote name (default: origin)')
    setup_parser.add_argument('--branch', default='main', help='Branch name (default: main)')
    
    args = parser.parse_args()
    
    # If --menu flag or no command provided, show menu
    if args.menu or not args.command:
        cli = GitCLI(repo_path=args.repo, require_git=False)
        show_main_menu(cli)
        return
    
    # Otherwise, execute command as before
    
    try:
        # Commands that don't require git repository
        if args.command == 'init':
            cli = GitCLI(repo_path=args.repo, require_git=False)
            cli.init()
            return
        
        # Commands that require git repository
        require_git = args.command not in ['init', 'setup']
        cli = GitCLI(repo_path=args.repo, require_git=require_git)
        
        if args.command == 'status':
            cli.status(short=args.short)
        elif args.command == 'add':
            if args.all_files:
                cli.add(all_files=True)
            elif args.files:
                cli.add(files=args.files)
            else:
                print("❌ Cần chỉ định --all hoặc danh sách files")
                add_parser.print_help()
                sys.exit(1)
        elif args.command == 'commit':
            cli.commit(
                message=args.message,
                allow_empty=args.allow_empty,
                no_verify=args.no_verify
            )
        elif args.command == 'push':
            cli.push(
                remote=args.remote,
                branch=args.branch,
                force=args.force,
                set_upstream=args.set_upstream
            )
        elif args.command == 'quick':
            cli.quick_push(
                message=args.message,
                remote=args.remote,
                branch=args.branch,
                force=args.force,
                no_verify=args.no_verify
            )
        elif args.command == 'pull':
            cli.pull(
                remote=args.remote,
                branch=args.branch,
                rebase=args.rebase
            )
        elif args.command == 'setup-remote':
            cli.setup_remote(
                url=args.url,
                name=args.name,
                force=args.force,
                use_ssh=getattr(args, 'use_ssh', False)
            )
        elif args.command == 'setup':
            cli.setup(
                remote_url=args.remote_url,
                commit_message=args.message,
                remote_name=args.remote_name,
                branch=args.branch
            )
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
