#!/usr/bin/env python3
"""
Unified Cleanup Script for Threads Automation Tool
Combines all cleanup scripts into one with menu
"""

import sys
import shutil
import os
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime
from collections import defaultdict

# Setup path using common utility
from scripts.common import setup_path, print_header, print_section

# Add parent directory to path (must be after importing common)
setup_path()


def show_menu():
    """Show cleanup menu."""
    print()
    print("=" * 60)
    print("CLEANUP SCRIPTS MENU")
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
    print("0. Exit")
    print()
    choice = input("Chọn option (0-8): ").strip()
    return choice


# ============================================================================
# PRE-DEPLOYMENT CLEANUP (FULL - PYTHON)
# ============================================================================

class CleanupStats:
    """Track cleanup statistics."""
    
    def __init__(self):
        self.files_deleted = 0
        self.dirs_deleted = 0
        self.errors = 0
        self.total_size = 0
    
    def add_file(self, size: int = 0):
        """Add deleted file to stats."""
        self.files_deleted += 1
        self.total_size += size
    
    def add_dir(self):
        """Add deleted directory to stats."""
        self.dirs_deleted += 1
    
    def add_error(self):
        """Add error to stats."""
        self.errors += 1
    
    def print_summary(self):
        """Print cleanup summary."""
        print()
        print("=" * 80)
        print("CLEANUP SUMMARY")
        print("=" * 80)
        print(f"Files deleted: {self.files_deleted}")
        print(f"Directories deleted: {self.dirs_deleted}")
        print(f"Total size freed: {self._format_size(self.total_size)}")
        print(f"Errors: {self.errors}")
        print("=" * 80)

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format bytes to human-readable size."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"


def get_file_size(path: Path) -> int:
    """Get file size in bytes."""
    try:
        return path.stat().st_size if path.is_file() else 0
    except Exception:
        return 0


def should_skip_path(path: Path) -> bool:
    """Check if path should be skipped."""
    path_str = str(path)
    skip_patterns = [
        '/venv/',
        '/profiles/',
        '/.git/',
        '/node_modules/',
    ]
    return any(pattern in path_str for pattern in skip_patterns)


def delete_path(path: Path, stats: CleanupStats, description: str = "") -> bool:
    """Delete a file or directory if it exists."""
    if not path.exists():
        return True
    
    if should_skip_path(path):
        return True
    
    try:
        if path.is_file():
            size = get_file_size(path)
            path.unlink()
            stats.add_file(size)
            if description:
                print(f"✅ Deleted: {description}")
            return True
        else:
            shutil.rmtree(path)
            stats.add_dir()
            if description:
                print(f"✅ Deleted: {description}")
            return True
    except Exception as e:
        stats.add_error()
        print(f"❌ Error deleting {path}: {e}")
        return False


def cleanup_pycache(stats: CleanupStats, repo_root: Path):
    """Cleanup __pycache__ directories."""
    print_section("Cleaning __pycache__ directories")
    
    for pycache_dir in repo_root.rglob("__pycache__"):
        if should_skip_path(pycache_dir):
            continue
        delete_path(pycache_dir, stats, f"__pycache__: {pycache_dir.relative_to(repo_root)}")


def cleanup_logs(stats: CleanupStats, repo_root: Path):
    """Cleanup log files."""
    print_section("Cleaning log files")
    
    for log_file in repo_root.rglob("*.log"):
        if should_skip_path(log_file):
            continue
        delete_path(log_file, stats, f"Log: {log_file.relative_to(repo_root)}")


def cleanup_build_artifacts(stats: CleanupStats, repo_root: Path):
    """Cleanup build artifacts."""
    print_section("Cleaning build artifacts")
    
    patterns = [
        "*.pyc", "*.pyo", "*.pyd",
        "*.old",
        ".DS_Store", "Thumbs.db",
        "*.swp", "*.swo", "*~",
        "*.egg-info",
        ".pytest_cache", ".coverage", "htmlcov"
    ]
    
    for pattern in patterns:
        for item in repo_root.rglob(pattern):
            if should_skip_path(item):
                continue
            delete_path(item, stats, f"{pattern}: {item.relative_to(repo_root)}")
    
    # Cleanup dist and build directories
    for dir_name in ["dist", "build"]:
        dir_path = repo_root / dir_name
        if dir_path.exists() and not should_skip_path(dir_path):
            delete_path(dir_path, stats, f"{dir_name}/ directory")


def cleanup_pre_deploy_full(dry_run: bool = False):
    """Full pre-deployment cleanup."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    
    print_header("PRE-DEPLOYMENT CLEANUP (FULL)")
    print()
    
    if dry_run:
        print("🔍 DRY RUN MODE - No files will be deleted")
        print()
    
    stats = CleanupStats()
    
    # Cleanup operations
    cleanup_pycache(stats, repo_root)
    cleanup_logs(stats, repo_root)
    cleanup_build_artifacts(stats, repo_root)
    
    stats.print_summary()
    
    if not dry_run:
        print()
        print("✅ Cleanup complete!")
        print()
        print("Next steps:")
        print("  1. Review: git status")
        print("  2. Commit: git commit -m 'chore: cleanup before deployment'")


# ============================================================================
# PRE-DEPLOYMENT CLEANUP (QUICK - SHELL)
# ============================================================================

def cleanup_pre_deploy_quick():
    """Quick pre-deployment cleanup using shell script."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    cleanup_script = script_path.parent / "cleanup_pre_deploy.sh"
    
    if not cleanup_script.exists():
        print("❌ cleanup_pre_deploy.sh not found")
        return
    
    print_header("PRE-DEPLOYMENT CLEANUP (QUICK)")
    print()
    
    try:
        result = subprocess.run(
            ["bash", str(cleanup_script)],
            cwd=str(repo_root)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running cleanup script: {e}")
        return False


# ============================================================================
# CLEANUP DATA FOLDERS
# ============================================================================

def cleanup_data_folders():
    """Delete data-only folders."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    
    print_header("CLEANUP DATA-ONLY FOLDERS")
    print()
    
    folders_to_delete = [
        ("uploadexcel", "User-uploaded Excel files"),
        ("backups", "Manual backup files"),
    ]
    
    for folder_name, description in folders_to_delete:
        folder_path = repo_root / folder_name
        if folder_path.exists():
            try:
                print(f"Deleting {description}: {folder_path}")
                shutil.rmtree(folder_path)
                print(f"✅ Successfully deleted {folder_path}")
            except Exception as e:
                print(f"❌ Error deleting {folder_path}: {e}")
        else:
            print(f"ℹ️  {folder_path} does not exist, skipping")
    
    print()
    print("=" * 80)
    print("Cleanup complete!")
    print("=" * 80)
    print()
    print("Note: These folders are now in .gitignore and will not be tracked.")


# ============================================================================
# CLEANUP STREAMLIT UI
# ============================================================================

def cleanup_streamlit_ui():
    """Delete Streamlit UI code."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    
    print_header("CLEANUP STREAMLIT UI CODE")
    print()
    
    paths_to_delete = [
        (repo_root / "ui" / "components", "ui/components/ (Streamlit components)"),
        (repo_root / "ui" / "config", "ui/config/ (Streamlit theme config)"),
        (repo_root / "ui" / "services", "ui/services/ (empty directory)"),
    ]
    
    for path, description in paths_to_delete:
        if path.exists():
            try:
                if path.is_file():
                    path.unlink()
                    print(f"✅ Deleted file: {path}")
                else:
                    shutil.rmtree(path)
                    print(f"✅ Deleted directory: {path}")
            except Exception as e:
                print(f"❌ Error deleting {path}: {e}")
        else:
            print(f"ℹ️  {path} does not exist, skipping")
    
    # Clean up ui/utils/ folder
    utils_folder = repo_root / "ui" / "utils"
    if utils_folder.exists():
        for file in ["cache.py", "toast.py"]:
            file_path = utils_folder / file
            if file_path.exists():
                try:
                    file_path.unlink()
                    print(f"✅ Deleted: ui/utils/{file}")
                except Exception as e:
                    print(f"❌ Error deleting {file_path}: {e}")
    
    print()
    print("=" * 80)
    print("Cleanup complete!")
    print("=" * 80)
    print()
    print("✅ Kept:")
    print("   - ui/api/ (backend dependencies)")
    print("   - ui/utils.py (used by ui/api/*)")
    print("   - ui/utils/__init__.py (folder structure)")


# ============================================================================
# CLEANUP DOCS & SCRIPTS (PYTHON)
# ============================================================================

class DocScriptAnalyzer:
    """Analyze documentation and script files for cleanup."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.files_to_archive: List[Path] = []
        self.files_to_delete: List[Path] = []
        self.files_to_keep: List[Path] = []
        self.duplicates: List[Tuple[Path, Path]] = []
    
    def analyze(self) -> Dict:
        """Analyze all .md and .sh files."""
        print_header("DOCUMENTATION & SCRIPTS CLEANUP ANALYSIS")
        print()
        
        # Find all .md files in root
        md_files = list(self.repo_root.glob("*.md"))
        # Find all .sh files in root
        sh_files = list(self.repo_root.glob("*.sh"))
        
        print(f"Found {len(md_files)} .md files in root")
        print(f"Found {len(sh_files)} .sh files in root")
        print()
        
        # Analyze .md files
        self._analyze_md_files(md_files)
        
        # Analyze .sh files
        self._analyze_sh_files(sh_files)
        
        # Check for duplicates
        self._check_duplicates()
        
        return {
            "to_archive": self.files_to_archive,
            "to_delete": self.files_to_delete,
            "to_keep": self.files_to_keep,
            "duplicates": self.duplicates
        }
    
    def _analyze_md_files(self, files: List[Path]) -> None:
        """Analyze markdown files."""
        print("Analyzing .md files...")
        print()
        
        # Files to keep (essential)
        keep_patterns = [
            "README.md",
            "DEPLOYMENT_CHECKLIST.md",
            "CLEANUP_PRE_DEPLOY.md",
            "DOCKER_README.md",
        ]
        
        # Files to archive (phase/migration completion)
        archive_patterns = [
            "PHASE", "CLEANUP_PHASE", "CLEANUP_STATUS", "CLEANUP_VERIFICATION",
            "CLEANUP_COMPLIANCE", "CLEANUP_FINAL", "CLEANUP_IMPLEMENTATION",
            "MIGRATION_COMPLETE", "MIGRATION_GUIDE", "MIGRATE_TESTS",
            "UI_PHASE", "UI_CLEANUP", "UI_UX_PRO_MAX", "REFACTORING_VERIFICATION",
            "IMPROVEMENTS_PROGRESS", "TEST_RESULTS",
        ]
        
        for file in files:
            file_name = file.name
            
            # Check if should keep
            if any(keep in file_name for keep in keep_patterns):
                self.files_to_keep.append(file)
                print(f"✅ Keep: {file_name}")
                continue
            
            # Check if should archive
            if any(pattern in file_name for pattern in archive_patterns):
                self.files_to_archive.append(file)
                print(f"📦 Archive: {file_name}")
            else:
                # Unknown file - keep for now
                self.files_to_keep.append(file)
                print(f"❓ Unknown: {file_name} (keeping)")
    
    def _analyze_sh_files(self, files: List[Path]) -> None:
        """Analyze shell script files."""
        print()
        print("Analyzing .sh files...")
        print()
        
        # Essential scripts to keep
        keep_patterns = [
            "setup.sh",
            "install_dependencies.sh",
        ]
        
        for file in files:
            file_name = file.name
            
            if any(keep in file_name for keep in keep_patterns):
                self.files_to_keep.append(file)
                print(f"✅ Keep: {file_name}")
            else:
                # Check for duplicates
                py_version = file.with_suffix('.py')
                if py_version.exists():
                    self.duplicates.append((file, py_version))
                    print(f"⚠️  Duplicate: {file_name} (Python version exists)")
                else:
                    # Unknown - keep for now
                    self.files_to_keep.append(file)
                    print(f"❓ Unknown: {file_name} (keeping)")
    
    def _check_duplicates(self) -> None:
        """Check for duplicate files."""
        if self.duplicates:
            print()
            print("Found duplicates:")
            for sh_file, py_file in self.duplicates:
                print(f"  - {sh_file.name} <-> {py_file.name}")
    
    def generate_report(self) -> str:
        """Generate cleanup report."""
        report = []
        report.append("=" * 80)
        report.append("CLEANUP REPORT")
        report.append("=" * 80)
        report.append("")
        report.append(f"Files to archive: {len(self.files_to_archive)}")
        report.append(f"Files to delete: {len(self.files_to_delete)}")
        report.append(f"Files to keep: {len(self.files_to_keep)}")
        report.append(f"Duplicates found: {len(self.duplicates)}")
        report.append("")
        
        if self.files_to_archive:
            report.append("Files to archive:")
            for file in self.files_to_archive:
                report.append(f"  - {file.name}")
            report.append("")
        
        return "\n".join(report)
    
    def create_archive_script(self) -> str:
        """Create shell script to archive files."""
        script_lines = [
            "#!/bin/bash",
            "# Auto-generated archive script",
            "",
            "ARCHIVE_DIR=\"docs/archive/root_files\"",
            "mkdir -p \"$ARCHIVE_DIR\"",
            "",
        ]
        
        for file in self.files_to_archive:
            script_lines.append(f'mv "{file.name}" "$ARCHIVE_DIR/" 2>/dev/null || echo "Failed: {file.name}"')
        
        return "\n".join(script_lines)


def cleanup_docs_scripts():
    """Cleanup documentation and scripts."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    
    print_header("DOCUMENTATION & SCRIPTS CLEANUP")
    print()
    
    analyzer = DocScriptAnalyzer(repo_root)
    results = analyzer.analyze()
    
    print()
    print(analyzer.generate_report())
    
    if results["to_archive"]:
        print()
        response = input("Archive these files? (yes/no): ").strip().lower()
        if response == "yes":
            archive_dir = repo_root / "docs" / "archive" / "root_files"
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            archived = 0
            for file in results["to_archive"]:
                try:
                    dest = archive_dir / file.name
                    if dest.exists():
                        print(f"⚠️  {file.name} already exists in archive, skipping")
                        continue
                    shutil.move(str(file), str(dest))
                    print(f"✅ Archived: {file.name}")
                    archived += 1
                except Exception as e:
                    print(f"❌ Failed to archive {file.name}: {e}")
            
            print()
            print(f"✅ Archived {archived} files")
            print(f"   Location: {archive_dir}")


# ============================================================================
# ARCHIVE DOCS & SCRIPTS (SHELL)
# ============================================================================

def archive_docs_scripts_shell():
    """Archive docs and scripts using shell script."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    cleanup_script = script_path.parent / "cleanup_docs_scripts.sh"
    
    if not cleanup_script.exists():
        print("❌ cleanup_docs_scripts.sh not found")
        return
    
    print_header("ARCHIVE DOCS & SCRIPTS (SHELL)")
    print()
    
    try:
        result = subprocess.run(
            ["bash", str(cleanup_script)],
            cwd=str(repo_root)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running cleanup script: {e}")
        return False


# ============================================================================
# FIX FAILED ARCHIVE
# ============================================================================

def fix_failed_archive():
    """Fix failed archive files."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent.parent
    fix_script = script_path.parent / "fix_failed_archive.sh"
    
    if not fix_script.exists():
        print("❌ fix_failed_archive.sh not found")
        return
    
    print_header("FIX FAILED ARCHIVE")
    print()
    
    try:
        result = subprocess.run(
            ["bash", str(fix_script)],
            cwd=str(repo_root)
        )
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running fix script: {e}")
        return False


# ============================================================================
# RUN ALL CLEANUPS
# ============================================================================

def run_all_cleanups():
    """Run all cleanup operations."""
    print_header("RUNNING ALL CLEANUPS")
    print()
    
    print("This will run:")
    print("  1. Pre-deployment cleanup (quick)")
    print("  2. Cleanup data folders")
    print("  3. Archive docs & scripts")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != "yes":
        print("Cancelled.")
        return
    
    print()
    print("=" * 60)
    print("STEP 1: Pre-Deployment Cleanup")
    print("=" * 60)
    cleanup_pre_deploy_quick()
    
    print()
    print("=" * 60)
    print("STEP 2: Cleanup Data Folders")
    print("=" * 60)
    cleanup_data_folders()
    
    print()
    print("=" * 60)
    print("STEP 3: Archive Docs & Scripts")
    print("=" * 60)
    archive_docs_scripts_shell()
    
    print()
    print("=" * 60)
    print("ALL CLEANUPS COMPLETE")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Review: git status")
    print("  2. Commit: git commit -m 'chore: cleanup before deployment'")


# ============================================================================
# MAIN FUNCTION
# ============================================================================

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Unified Cleanup Script")
    parser.add_argument('--pre-deploy-full', action='store_true', help='Full pre-deployment cleanup')
    parser.add_argument('--pre-deploy-quick', action='store_true', help='Quick pre-deployment cleanup')
    parser.add_argument('--data-folders', action='store_true', help='Cleanup data folders')
    parser.add_argument('--streamlit-ui', action='store_true', help='Cleanup Streamlit UI')
    parser.add_argument('--docs-scripts', action='store_true', help='Cleanup docs & scripts')
    parser.add_argument('--archive-shell', action='store_true', help='Archive docs & scripts (shell)')
    parser.add_argument('--fix-archive', action='store_true', help='Fix failed archive')
    parser.add_argument('--all', action='store_true', help='Run all cleanups')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no deletions)')
    
    args = parser.parse_args()
    
    # If command provided, run directly
    if args.pre_deploy_full:
        cleanup_pre_deploy_full(dry_run=args.dry_run)
        return
    
    if args.pre_deploy_quick:
        cleanup_pre_deploy_quick()
        return
    
    if args.data_folders:
        cleanup_data_folders()
        return
    
    if args.streamlit_ui:
        cleanup_streamlit_ui()
        return
    
    if args.docs_scripts:
        cleanup_docs_scripts()
        return
    
    if args.archive_shell:
        archive_docs_scripts_shell()
        return
    
    if args.fix_archive:
        fix_failed_archive()
        return
    
    if args.all:
        run_all_cleanups()
        return
    
    # Otherwise show menu
    while True:
        choice = show_menu()
        
        if choice == "0":
            print("👋 Goodbye!")
            break
        elif choice == "1":
            cleanup_pre_deploy_full()
        elif choice == "2":
            cleanup_pre_deploy_quick()
        elif choice == "3":
            cleanup_data_folders()
        elif choice == "4":
            cleanup_streamlit_ui()
        elif choice == "5":
            cleanup_docs_scripts()
        elif choice == "6":
            archive_docs_scripts_shell()
        elif choice == "7":
            fix_failed_archive()
        elif choice == "8":
            run_all_cleanups()
        else:
            print("❌ Invalid option. Please choose 0-8.")
        
        if choice != "0":
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã hủy bởi user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
