#!/usr/bin/env python3
"""
Unified CLI Menu - Tích hợp tất cả CLI tools vào một menu duy nhất.

Usage:
    python scripts/cli/cli_menu.py
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def print_header(title: str, width: int = 80) -> None:
    """Print formatted header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_section(title: str, width: int = 80) -> None:
    """Print formatted section."""
    print("\n" + "-" * width)
    print(title)
    print("-" * width)


def prompt_input(prompt: str, default: Optional[str] = None) -> str:
    """Prompt for user input with optional default."""
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
    """Prompt for yes/no question."""
    default_str = "Y/n" if default else "y/N"
    response = prompt_input(f"{prompt} ({default_str})", default="y" if default else "n")
    return response.lower() in ["y", "yes"]


def show_main_menu():
    """Display main menu."""
    print_header("🚀 THREADS AUTOMATION - CLI TOOLS")
    print()
    print("1. 📦 Git Operations")
    print("2. 📋 Jobs Management")
    print("3. 🧪 Testing & CI/CD")
    print("4. ⚙️  Development Tools")
    print("5. 🔍 Utilities")
    print()
    print("0. Exit")
    print()


def show_git_menu():
    """Display Git operations menu."""
    from scripts.cli.git_cli import GitCLI, show_basic_menu, show_push_pull_menu, show_setup_menu, show_advanced_menu
    
    cli = GitCLI()
    
    while True:
        print_header("📦 GIT OPERATIONS")
        print("1. Basic Operations (Status, Add, Commit)")
        print("2. Push/Pull Operations")
        print("3. Setup Operations (Init, Remote, Complete Setup)")
        print("4. Advanced Operations (Branch, Force Push, etc.)")
        print("5. Quick Push (Add all + Commit + Push)")
        print()
        print("0. Back to main menu")
        print()
        
        choice = prompt_input("Chọn option (0-5)", default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            show_basic_menu(cli)
        elif choice == "2":
            show_push_pull_menu(cli)
        elif choice == "3":
            show_setup_menu(cli)
        elif choice == "4":
            show_advanced_menu(cli)
        elif choice == "5":
            try:
                message = prompt_input("Commit message")
                if message:
                    cli.quick(message)
                else:
                    print("⚠️  Commit message không được để trống")
            except Exception as e:
                print(f"\n❌ Lỗi: {e}")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_jobs_menu():
    """Display Jobs management menu."""
    try:
        from scripts.cli.jobs_cli import JobsCLI
        cli = JobsCLI()
        
        while True:
            print_header("📋 JOBS MANAGEMENT")
            print("1. List Jobs")
            print("2. Search Jobs")
            print("3. Job Statistics")
            print("4. Export Jobs")
            print("5. Import Jobs")
            print("6. Backup Jobs")
            print("7. Restore Jobs")
            print("8. Clean Jobs")
            print("9. Bulk Operations")
            print("10. Create Template")
            print("11. Validate Jobs")
            print()
            print("0. Back to main menu")
            print()
            
            choice = prompt_input("Chọn option (0-11)", default="0")
            
            if choice == "0":
                break
            elif choice == "1":
                status_filter = prompt_input("Filter by status (pending/running/completed/failed/all)", default="all")
                cli.list_jobs(status=status_filter if status_filter != "all" else None)
            elif choice == "2":
                keyword = prompt_input("Search keyword")
                if keyword:
                    cli.search_jobs(keyword)
            elif choice == "3":
                cli.stats()
            elif choice == "4":
                format_type = prompt_input("Export format (csv/json)", default="json")
                output_file = prompt_input("Output file path", default="jobs_export.json")
                cli.export_jobs(output_file, format=format_type)
            elif choice == "5":
                template_file = prompt_input("Template file path")
                if template_file:
                    cli.import_jobs(template_file)
            elif choice == "6":
                backup_file = prompt_input("Backup file path", default="jobs_backup.json")
                cli.backup_jobs(backup_file)
            elif choice == "7":
                backup_file = prompt_input("Backup file path")
                if backup_file:
                    cli.restore_jobs(backup_file)
            elif choice == "8":
                cli.clean_jobs()
            elif choice == "9":
                print("Bulk operations menu...")
                # TODO: Implement bulk operations menu
            elif choice == "10":
                template_file = prompt_input("Template file path", default="job_template.json")
                cli.create_template(template_file)
            elif choice == "11":
                cli.validate_jobs()
            else:
                print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
            
            prompt_input("\nNhấn Enter để tiếp tục...", default="")
    except ImportError as e:
        print(f"❌ Jobs CLI không khả dụng: {e}")
        print("   Có thể cần install dependencies hoặc Jobs CLI chưa được implement.")
        prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_testing_menu():
    """Display Testing & CI/CD menu."""
    while True:
        print_header("🧪 TESTING & CI/CD")
        print("1. Run All CI Checks (Format, Lint, Type-check, Test, Security)")
        print("2. Run Unit Tests")
        print("3. Run Integration Tests")
        print("4. Run Tests with Coverage")
        print("5. Code Formatting Check")
        print("6. Linting Check")
        print("7. Type Checking")
        print("8. Security Scan")
        print()
        print("0. Back to main menu")
        print()
        
        choice = prompt_input("Chọn option (0-8)", default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            run_command(["python", "scripts/cli/run_tests.py", "--ci"])
        elif choice == "2":
            run_command(["python", "scripts/cli/run_tests.py", "--unit"])
        elif choice == "3":
            run_command(["python", "scripts/cli/run_tests.py", "--integration"])
        elif choice == "4":
            run_command(["python", "scripts/cli/run_tests.py", "--coverage"])
        elif choice == "5":
            run_command(["python", "scripts/cli/run_tests.py", "--format"])
        elif choice == "6":
            run_command(["python", "scripts/cli/run_tests.py", "--lint"])
        elif choice == "7":
            run_command(["mypy", "scripts/cli/git_cli.py", "--ignore-missing-imports"])
        elif choice == "8":
            run_command([
                "bandit",
                "-r",
                "scripts/cli/git_cli.py",
                "-c",
                ".bandit",
                "-f",
                "json",
                "-o",
                "bandit-report.json"
            ])
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
        
        prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_dev_tools_menu():
    """Display Development Tools menu."""
    while True:
        print_header("⚙️  DEVELOPMENT TOOLS")
        print("1. Install Dev Dependencies")
        print("2. Check Node.js Version")
        print("3. Verify Python Imports")
        print()
        print("0. Back to main menu")
        print()
        
        choice = prompt_input("Chọn option (0-3)", default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            run_command(["python", "scripts/cli/install_dev_deps.py"])
        elif choice == "2":
            run_command(["python", "scripts/cli/check_node_version.py"])
        elif choice == "3":
            try:
                from scripts.cli.git_cli import GitCLI
                print("✅ Git CLI import successful!")
                print(f"   GitCLI: {GitCLI}")
            except ImportError as e:
                print(f"❌ Import failed: {e}")
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
        
        prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_utilities_menu():
    """Display Utilities menu."""
    while True:
        print_header("🔍 UTILITIES")
        print("1. Check Git Status")
        print("2. Check Python Version")
        print("3. Check Installed Packages")
        print("4. Project Info")
        print()
        print("0. Back to main menu")
        print()
        
        choice = prompt_input("Chọn option (0-4)", default="0")
        
        if choice == "0":
            break
        elif choice == "1":
            run_command(["git", "status"])
        elif choice == "2":
            run_command([sys.executable, "--version"])
        elif choice == "3":
            run_command([sys.executable, "-m", "pip", "list"])
        elif choice == "4":
            show_project_info()
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
        
        prompt_input("\nNhấn Enter để tiếp tục...", default="")


def show_project_info():
    """Show project information."""
    print_section("Project Information")
    print(f"Project Root: {project_root}")
    print(f"Python Version: {sys.version}")
    print(f"Python Executable: {sys.executable}")
    
    # Check git info
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0:
            print(f"Git Root: {result.stdout.strip()}")
        
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        if result.returncode == 0:
            print(f"Current Branch: {result.stdout.strip()}")
    except Exception:
        pass


def run_command(cmd: list[str]) -> None:
    """Run a command and display output."""
    print_section(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=False
        )
        if result.returncode != 0:
            print(f"\n⚠️  Command exited with code {result.returncode}")
    except FileNotFoundError:
        print(f"❌ Command not found: {cmd[0]}")
        print(f"   Make sure it's installed and in PATH")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main menu loop."""
    while True:
        show_main_menu()
        choice = prompt_input("Chọn option (0-5)", default="0")
        
        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            show_git_menu()
        elif choice == "2":
            show_jobs_menu()
        elif choice == "3":
            show_testing_menu()
        elif choice == "4":
            show_dev_tools_menu()
        elif choice == "5":
            show_utilities_menu()
        else:
            print("❌ Lựa chọn không hợp lệ. Vui lòng chọn lại.")
            prompt_input("\nNhấn Enter để tiếp tục...", default="")


if __name__ == "__main__":
    main()
