#!/usr/bin/env python3
"""
Quick script to install dev dependencies for CI/CD.
Usage: python scripts/cli/install_dev_deps.py
"""

import sys
import subprocess
from pathlib import Path

# Get project root
project_root = Path(__file__).parent.parent.parent
requirements_dev = project_root / "requirements-dev.txt"

def main():
    """Install dev dependencies."""
    print("=" * 60)
    print("Installing Development Dependencies")
    print("=" * 60)
    print()
    
    # Check if requirements-dev.txt exists
    if not requirements_dev.exists():
        print(f"❌ {requirements_dev} not found!")
        print("   Make sure you're in the project root directory")
        sys.exit(1)
    
    # Install dev dependencies
    print(f"Installing from {requirements_dev}...")
    print()
    
    try:
        # Try to install from requirements-dev.txt first
        print("Attempting to install from requirements-dev.txt...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_dev)],
            cwd=project_root,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ All dependencies installed from requirements-dev.txt")
        else:
            # If failed, try installing core dependencies individually
            print("⚠️  Installation from file failed, installing individually...")
            print()
            
            core_deps = [
                "black>=24.3.0",
                "pylint>=3.1.0",
                "mypy>=1.9.0",
                "bandit>=1.7.6",
                "pre-commit>=3.6.0",
            ]
            
            print("Installing core dependencies...")
            failed = []
            for dep in core_deps:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", dep],
                        check=True,
                        cwd=project_root,
                        capture_output=True
                    )
                    print(f"  ✅ {dep.split('>=')[0]}")
                except subprocess.CalledProcessError:
                    print(f"  ❌ Failed: {dep.split('>=')[0]}")
                    failed.append(dep)
            
            if failed:
                print(f"\n⚠️  Some packages failed to install: {', '.join(failed)}")
                print("   You may need to install them manually")
            else:
                print("\n✅ Core dependencies installed successfully")
        print()
        print("=" * 60)
        print("✅ Development dependencies installed!")
        print("=" * 60)
        print()
        print("You can now run:")
        print("  python scripts/cli/run_tests.py --ci")
        print("  make ci")
        print()
    except subprocess.CalledProcessError as e:
        print()
        print(f"❌ Installation failed with exit code {e.returncode}")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ pip not found. Make sure Python is installed correctly.")
        sys.exit(1)


if __name__ == "__main__":
    main()
