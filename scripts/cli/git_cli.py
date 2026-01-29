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
        
        try:
            result = subprocess.run(
                git_cmd,
                check=check,
                capture_output=capture_output,
                text=True,
                encoding='utf-8',
                timeout=300  # 5 minutes timeout
            )
            return result
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            print(f"❌ Git command failed: {' '.join(git_cmd)}")
            print(f"   Error: {error_msg}")
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
        pull_cmd = ['pull']
        if rebase:
            pull_cmd.append('--rebase')
        pull_cmd.append(remote)
        pull_cmd.append(branch)
        
        self._run_git_command(pull_cmd)
        print(f"✅ Đã pull {branch} từ {remote}")
    
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
        force: bool = False
    ) -> None:
        """
        Setup remote repository.
        
        Args:
            url: Remote repository URL (e.g., https://github.com/user/repo.git)
            name: Remote name (default: origin)
            force: Force update if remote exists (default: False)
        """
        print_header("🔗 SETTING UP REMOTE")
        
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
    
    # Setup command
    setup_parser = subparsers.add_parser('setup', help='Setup tổng hợp (init + remote + commit + push)')
    setup_parser.add_argument('remote_url', help='Remote repository URL')
    setup_parser.add_argument('--message', default='Initial commit', help='Initial commit message (default: Initial commit)')
    setup_parser.add_argument('--remote-name', default='origin', help='Remote name (default: origin)')
    setup_parser.add_argument('--branch', default='main', help='Branch name (default: main)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
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
                force=args.force
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
