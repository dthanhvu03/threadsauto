#!/usr/bin/env python3
"""
Quick test runner for git_cli.py
Usage: python scripts/cli/run_tests.py [--unit|--integration|--all|--coverage]
"""

import sys
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def check_and_install_deps():
    """Check if dev dependencies are installed, offer to install if missing."""
    missing_deps = []
    deps_to_check = {
        'black': 'black',
        'pylint': 'pylint',
        'mypy': 'mypy',
        'bandit': 'bandit'
    }
    
    for cmd, package in deps_to_check.items():
        try:
            subprocess.run(
                [cmd, '--version'],
                capture_output=True,
                check=True,
                timeout=5
            )
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            missing_deps.append(package)
    
    if missing_deps:
        print(f"\n⚠️  Missing dev dependencies: {', '.join(missing_deps)}")
        print(f"   Install with: pip install -r requirements-dev.txt")
        print(f"   Or run: python scripts/cli/install_dev_deps.py")
        print()
        return False
    return True


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")
    
    try:
        result = subprocess.run(cmd, cwd=project_root, check=True)
        print(f"\n✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} - FAILED (exit code: {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"\n❌ Command not found: {cmd[0]}")
        print(f"   Install with: pip install -r requirements-dev.txt")
        print(f"   Or run: python scripts/cli/install_dev_deps.py")
        return False


def main():
    """Main test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for git_cli.py")
    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run unit tests only'
    )
    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run integration tests only'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Run all tests'
    )
    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run tests with coverage report'
    )
    parser.add_argument(
        '--lint',
        action='store_true',
        help='Run linting checks'
    )
    parser.add_argument(
        '--format',
        action='store_true',
        help='Check code formatting'
    )
    parser.add_argument(
        '--ci',
        action='store_true',
        help='Run all CI checks (format, lint, type-check, test, security)'
    )
    
    args = parser.parse_args()
    
    # If no args, run unit tests by default
    if not any(vars(args).values()):
        args.unit = True
    
    # Check dev dependencies if running CI or lint/format checks
    if args.ci or args.lint or args.format:
        if not check_and_install_deps():
            print("⚠️  Some dev dependencies are missing.")
            print("   Continuing with available tools only...")
            print()
    
    all_passed = True
    
    # Format check
    if args.format or args.ci:
        all_passed &= run_command(
            ['black', '--check', 'scripts/cli/git_cli.py'],
            'Code Formatting Check'
        )
    
    # Linting
    if args.lint or args.ci:
        all_passed &= run_command(
            ['pylint', 'scripts/cli/git_cli.py', '--rcfile=.pylintrc'],
            'Pylint Check'
        )
    
    # Type checking
    if args.ci:
        all_passed &= run_command(
            ['mypy', 'scripts/cli/git_cli.py', '--ignore-missing-imports'],
            'Type Checking'
        )
    
    # Unit tests
    if args.unit or args.all or args.ci:
        cmd = ['pytest', 'tests/unit/test_git_cli.py', '-v']
        if args.coverage:
            cmd.extend([
                '--cov=scripts/cli/git_cli',
                '--cov-report=html',
                '--cov-report=term'
            ])
        all_passed &= run_command(cmd, 'Unit Tests')
    
    # Integration tests
    if args.integration or args.all:
        all_passed &= run_command(
            ['pytest', 'tests/integration/test_git_cli_integration.py', '-v', '-m', 'integration'],
            'Integration Tests'
        )
    
    # Coverage only
    if args.coverage and not args.unit:
        all_passed &= run_command(
            [
                'pytest',
                'tests/unit/test_git_cli.py',
                '--cov=scripts/cli/git_cli',
                '--cov-report=html',
                '--cov-report=term'
            ],
            'Coverage Report'
        )
    
    # Security scan
    if args.ci:
        all_passed &= run_command(
            [
                'bandit',
                '-r',
                'scripts/cli/git_cli.py',
                '-c',
                '.bandit',
                '-f',
                'json',
                '-o',
                'bandit-report.json'
            ],
            'Security Scan'
        )
    
    # Summary
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ ALL CHECKS PASSED")
    else:
        print("❌ SOME CHECKS FAILED")
    print(f"{'='*60}\n")
    
    sys.exit(0 if all_passed else 1)


if __name__ == '__main__':
    main()
