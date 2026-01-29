#!/usr/bin/env python3
"""
Unified scripts runner for Threads Automation Tool
Combines all scripts from scripts/ directory into one menu
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def show_main_menu():
    """Show main menu."""
    print()
    print("=" * 60)
    print("THREADS AUTOMATION TOOL - SCRIPTS")
    print("=" * 60)
    print()
    print("1. Test Scripts")
    print("2. Utility Scripts")
    print("3. Check Scripts")
    print("4. Debug Scripts")
    print("5. Analysis Scripts")
    print("6. CLI Tools")
    print("7. Backup Scripts")
    print("8. Cleanup Scripts")
    print()
    print("0. Exit")
    print()
    choice = input("Chọn category (0-8): ").strip()
    return choice


def show_test_menu():
    """Show test scripts menu."""
    print()
    print("=" * 60)
    print("TEST SCRIPTS")
    print("=" * 60)
    print()
    print("1. Test Post and Extract Thread ID")
    print("2. Test Fetch Metrics Real")
    print("3. Test Fetch Metrics Workflow")
    print("4. Test Username Extraction")
    print("5. Test Metrics XPath")
    print("6. Test Next Button Selector")
    print("7. Test MySQL Storage")
    print("8. Test Excel Upload")
    print("9. Test Migration Sample")
    print("10. Test Callback Factory")
    print("11. Get Thread IDs from Profile")
    print()
    print("0. Back")
    print()
    choice = input("Chọn script (0-11): ").strip()
    return choice


def show_utility_menu():
    """Show utility scripts menu."""
    print()
    print("=" * 60)
    print("UTILITY SCRIPTS")
    print("=" * 60)
    print()
    print("1. Initialize Default Data")
    print("2. Validate Job JSON")
    print("3. Archive Old Jobs")
    print("4. Remove Duplicate Jobs")
    print("5. Sync Jobs from Logs")
    print("6. Find Next Button")
    print("7. Fix Account Username")
    print("8. Check Browser Profile")
    print("9. Cleanup Old Logs")
    print("10. Fetch All Metrics")
    print("11. View Metrics")
    print()
    print("0. Back")
    print()
    choice = input("Chọn script (0-11): ").strip()
    return choice


def show_check_menu():
    """Show check scripts menu."""
    print()
    print("=" * 60)
    print("CHECK SCRIPTS")
    print("=" * 60)
    print()
    print("1. Check Job Status")
    print("2. Check Scheduler Status")
    print("3. Check Scheduler Live")
    print("4. Check Scheduler Workflow")
    print("5. Check Jobs Simple")
    print("6. Check Thread ID in DB")
    print("7. Check Thread ID in DB (Direct)")
    print("8. Verify Browser Profile Account")
    print()
    print("0. Back")
    print()
    choice = input("Chọn script (0-8): ").strip()
    return choice


def show_debug_menu():
    """Show debug scripts menu."""
    print()
    print("=" * 60)
    print("DEBUG SCRIPTS")
    print("=" * 60)
    print()
    print("1. Debug Scheduler Detailed")
    print("2. Debug Excel Upload Flow")
    print("3. Debug Save Flow")
    print()
    print("0. Back")
    print()
    choice = input("Chọn script (0-3): ").strip()
    return choice


def show_analysis_menu():
    """Show analysis scripts menu."""
    print()
    print("=" * 60)
    print("ANALYSIS SCRIPTS")
    print("=" * 60)
    print()
    print("1. Analyze Jobs")
    print("2. Analyze Next Button Logs")
    print()
    print("0. Back")
    print()
    choice = input("Chọn script (0-2): ").strip()
    return choice


def show_cli_menu():
    """Show CLI tools menu."""
    print()
    print("=" * 60)
    print("CLI TOOLS")
    print("=" * 60)
    print()
    print("1. Jobs CLI")
    print()
    print("0. Back")
    print()
    choice = input("Chọn tool (0-1): ").strip()
    return choice


def show_backup_menu():
    """Show backup scripts menu."""
    print()
    print("=" * 60)
    print("BACKUP SCRIPTS")
    print("=" * 60)
    print()
    print("1. MySQL Backup")
    print("2. Restore Backup")
    print("3. Setup Cron")
    print("4. List Backups")
    print()
    print("0. Back")
    print()
    choice = input("Chọn script (0-4): ").strip()
    return choice


def run_script(script_path: Path, *args):
    """Run a script with optional arguments."""
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    print()
    print("=" * 60)
    print(f"Running: {script_path.name}")
    print("=" * 60)
    print()
    
    try:
        cmd = [sys.executable, str(script_path)] + list(args)
        result = subprocess.run(cmd, cwd=str(project_root))
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return False


def handle_test_scripts(choice: str):
    """Handle test scripts menu."""
    scripts = {
        "1": ("scripts/test/test_post_and_extract_thread_id.py", []),
        "2": ("scripts/test/test_fetch_metrics_real.py", []),
        "3": ("scripts/test/test_fetch_metrics_workflow.py", []),
        "4": ("scripts/test/test_username_extraction.py", []),
        "5": ("scripts/test/test_metrics_xpath.py", []),
        "6": ("scripts/test/test_next_button_selector.py", []),
        "7": ("scripts/test/test_mysql_storage.py", []),
        "8": ("scripts/test/test_excel_upload.py", []),
        "9": ("scripts/test/test_migration_sample.py", []),
        "10": ("scripts/test/test_callback_factory.py", []),
        "11": ("scripts/test/get_thread_ids_from_profile.py", []),
    }
    
    if choice == "0":
        return True
    
    if choice in scripts:
        script_path, args = scripts[choice]
        run_script(project_root / script_path, *args)
        return False
    else:
        print("❌ Invalid option")
        return False


def handle_utility_scripts(choice: str):
    """Handle utility scripts menu."""
    utility_script = project_root / "scripts/utility/utility.py"
    
    if choice == "0":
        return True
    
    if not utility_script.exists():
        print(f"❌ Utility script not found: {utility_script}")
        return False
    
    # Simply run utility.py - it has its own menu
    print()
    print("=" * 60)
    print("Opening utility.py menu...")
    print("=" * 60)
    print()
    try:
        result = subprocess.run(
            [sys.executable, str(utility_script)],
            cwd=str(project_root)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running script: {e}")
        return False


def handle_check_scripts(choice: str):
    """Handle check scripts menu."""
    check_script = project_root / "scripts/check/check.py"
    
    if choice == "0":
        return True
    
    if not check_script.exists():
        print(f"❌ Check script not found: {check_script}")
        return False
    
    # Map choices to commands
    commands = {
        "1": ["--job-status"],
        "2": ["--scheduler-status"],
        "3": ["--scheduler-live"],
        "4": ["--scheduler-workflow"],
        "5": ["--jobs-simple"],
        "6": ["--thread-id"],  # Will prompt for thread_id
        "7": ["--thread-id-direct"],  # Will prompt for account_id
        "8": ["--verify-profile"],  # Will prompt for account_id
    }
    
    if choice in commands:
        cmd = commands[choice]
        print()
        print("=" * 60)
        print(f"Running: check.py {' '.join(cmd)}")
        print("=" * 60)
        print()
        try:
            # For commands that need input, just run check.py menu
            if choice in ["6", "7", "8"]:
                # These need interactive input, so run check.py directly
                result = subprocess.run(
                    [sys.executable, str(check_script)],
                    cwd=str(project_root)
                )
            else:
                result = subprocess.run(
                    [sys.executable, str(check_script)] + cmd,
                    cwd=str(project_root)
                )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running script: {e}")
            return False
    else:
        print("❌ Invalid option")
        return False


def handle_debug_scripts(choice: str):
    """Handle debug scripts menu."""
    debug_script = project_root / "scripts/debug/debug.py"
    
    if choice == "0":
        return True
    
    if not debug_script.exists():
        print(f"❌ Debug script not found: {debug_script}")
        return False
    
    # Map choices to commands
    commands = {
        "1": ["--scheduler"],
        "2": ["--excel-upload"],
        "3": ["--save-flow"],
    }
    
    if choice in commands:
        cmd = commands[choice]
        print()
        print("=" * 60)
        print(f"Running: debug.py {' '.join(cmd)}")
        print("=" * 60)
        print()
        try:
            result = subprocess.run(
                [sys.executable, str(debug_script)] + cmd,
                cwd=str(project_root)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running script: {e}")
            return False
    else:
        print("❌ Invalid option")
        return False


def handle_analysis_scripts(choice: str):
    """Handle analysis scripts menu."""
    analysis_script = project_root / "scripts/analysis/analysis.py"
    
    if choice == "0":
        return True
    
    if not analysis_script.exists():
        print(f"❌ Analysis script not found: {analysis_script}")
        return False
    
    # Map choices to commands
    commands = {
        "1": ["--analyze-jobs"],
        "2": ["--analyze-logs"],
    }
    
    if choice in commands:
        cmd = commands[choice]
        print()
        print("=" * 60)
        print(f"Running: analysis.py {' '.join(cmd)}")
        print("=" * 60)
        print()
        try:
            # These need interactive input, so run analysis.py directly
            result = subprocess.run(
                [sys.executable, str(analysis_script)],
                cwd=str(project_root)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running script: {e}")
            return False
    else:
        print("❌ Invalid option")
        return False


def handle_cli_tools(choice: str):
    """Handle CLI tools menu."""
    if choice == "0":
        return True
    
    if choice == "1":
        print()
        print("=" * 60)
        print("JOBS CLI")
        print("=" * 60)
        print()
        print("Usage: python scripts/cli/jobs_cli.py <command> [options]")
        print()
        print("Commands:")
        print("  list        - Liệt kê jobs với filter")
        print("  search      - Tìm kiếm jobs theo content/keyword")
        print("  stats       - Thống kê jobs")
        print("  export      - Export jobs ra CSV/JSON")
        print("  import      - Import jobs từ template file")
        print("  backup      - Backup jobs")
        print("  restore     - Restore jobs từ backup")
        print("  clean       - Cleanup jobs")
        print("  bulk        - Bulk operations")
        print("  template    - Tạo job template")
        print("  validate    - Validate jobs")
        print()
        print("Example:")
        print("  python scripts/cli/jobs_cli.py list --status pending")
        print("  python scripts/cli/jobs_cli.py stats")
        print()
        return False
    else:
        print("❌ Invalid option")
        return False


def show_cleanup_menu():
    """Show cleanup scripts menu."""
    print()
    print("=" * 60)
    print("CLEANUP SCRIPTS")
    print("=" * 60)
    print()
    print("1. Pre-Deployment Cleanup (Full)")
    print("2. Pre-Deployment Cleanup (Quick)")
    print("3. Cleanup Data Folders")
    print("4. Cleanup Streamlit UI")
    print("5. Cleanup Docs & Scripts")
    print("6. Archive Docs & Scripts (Shell)")
    print("7. Fix Failed Archive")
    print("8. Run All Cleanups")
    print()
    print("0. Back")
    print()
    choice = input("Chọn script (0-8): ").strip()
    return choice


def handle_cleanup_scripts(choice: str):
    """Handle cleanup scripts menu."""
    cleanup_script = project_root / "scripts/cleanup/cleanup.py"
    
    if choice == "0":
        return True
    
    if not cleanup_script.exists():
        print(f"❌ Cleanup script not found: {cleanup_script}")
        return False
    
    # Map choices to commands
    commands = {
        "1": ["--pre-deploy-full"],
        "2": ["--pre-deploy-quick"],
        "3": ["--data-folders"],
        "4": ["--streamlit-ui"],
        "5": ["--docs-scripts"],
        "6": ["--archive-shell"],
        "7": ["--fix-archive"],
        "8": ["--all"],
    }
    
    if choice in commands:
        cmd = commands[choice]
        print()
        print("=" * 60)
        print(f"Running: cleanup.py {' '.join(cmd)}")
        print("=" * 60)
        print()
        try:
            result = subprocess.run(
                [sys.executable, str(cleanup_script)] + cmd,
                cwd=str(project_root)
            )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running script: {e}")
            return False
    else:
        print("❌ Invalid option")
        return False


def handle_backup_scripts(choice: str):
    """Handle backup scripts menu."""
    backup_script = project_root / "scripts/backup/backup.sh"
    
    if choice == "0":
        return True
    
    if not backup_script.exists():
        print(f"❌ Backup script not found: {backup_script}")
        return False
    
    # Map choices to commands
    commands = {
        "1": "backup",
        "2": "restore",
        "3": "cron",
        "4": "list",
    }
    
    if choice in commands:
        cmd = commands[choice]
        print()
        print("=" * 60)
        print(f"Running: backup.sh {cmd}")
        print("=" * 60)
        print()
        try:
            # For restore, we need to handle interactively
            if cmd == "restore":
                result = subprocess.run(
                    ["bash", str(backup_script), cmd],
                    cwd=str(project_root)
                )
            else:
                result = subprocess.run(
                    ["bash", str(backup_script), cmd],
                    cwd=str(project_root)
                )
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Error running script: {e}")
            return False
    else:
        print("❌ Invalid option")
        return False


def main():
    """Main function."""
    while True:
        choice = show_main_menu()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            # Test scripts
            while True:
                test_choice = show_test_menu()
                if handle_test_scripts(test_choice):
                    break
                if test_choice != "0":
                    input("\nPress Enter to continue...")
        elif choice == "2":
            # Utility scripts
            while True:
                util_choice = show_utility_menu()
                if handle_utility_scripts(util_choice):
                    break
                if util_choice != "0":
                    input("\nPress Enter to continue...")
        elif choice == "3":
            # Check scripts
            while True:
                check_choice = show_check_menu()
                if handle_check_scripts(check_choice):
                    break
                if check_choice != "0":
                    input("\nPress Enter to continue...")
        elif choice == "4":
            # Debug scripts
            while True:
                debug_choice = show_debug_menu()
                if handle_debug_scripts(debug_choice):
                    break
                if debug_choice != "0":
                    input("\nPress Enter to continue...")
        elif choice == "5":
            # Analysis scripts
            while True:
                analysis_choice = show_analysis_menu()
                if handle_analysis_scripts(analysis_choice):
                    break
                if analysis_choice != "0":
                    input("\nPress Enter to continue...")
        elif choice == "6":
            # CLI tools
            while True:
                cli_choice = show_cli_menu()
                if handle_cli_tools(cli_choice):
                    break
                if cli_choice != "0":
                    input("\nPress Enter to continue...")
        elif choice == "7":
            # Backup scripts
            while True:
                backup_choice = show_backup_menu()
                if handle_backup_scripts(backup_choice):
                    break
                if backup_choice != "0":
                    input("\nPress Enter to continue...")
        elif choice == "8":
            # Cleanup scripts
            while True:
                cleanup_choice = show_cleanup_menu()
                if handle_cleanup_scripts(cleanup_choice):
                    break
                if cleanup_choice != "0":
                    input("\nPress Enter to continue...")
        else:
            print("❌ Invalid option. Please choose 0-8.")
        
        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
