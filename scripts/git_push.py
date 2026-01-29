#!/usr/bin/env python3
"""
Quick Git Push Script - Wrapper đơn giản cho git_cli.py

Usage:
    python scripts/git_push.py "commit message"
    python scripts/git_push.py "commit message" --force
    python scripts/git_push.py "commit message" --branch main
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.cli.git_cli import GitCLI


def main():
    """Quick push wrapper."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/git_push.py \"commit message\" [--force] [--branch BRANCH]")
        print("\nExamples:")
        print("  python scripts/git_push.py \"Update code\"")
        print("  python scripts/git_push.py \"Fix bug\" --force")
        print("  python scripts/git_push.py \"Add feature\" --branch main")
        sys.exit(1)
    
    message = sys.argv[1]
    force = '--force' in sys.argv
    branch = None
    
    if '--branch' in sys.argv:
        idx = sys.argv.index('--branch')
        if idx + 1 < len(sys.argv):
            branch = sys.argv[idx + 1]
    
    try:
        cli = GitCLI()
        cli.quick_push(
            message=message,
            force=force,
            branch=branch
        )
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
