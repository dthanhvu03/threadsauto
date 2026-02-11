#!/usr/bin/env python3
"""
Check Node.js version và so sánh với requirements.

Usage: python scripts/cli/check_node_version.py
"""

import subprocess
import sys
from pathlib import Path


def get_node_version():
    """Get current Node.js version."""
    try:
        result = subprocess.run(
            ['node', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_npm_version():
    """Get current npm version."""
    try:
        result = subprocess.run(
            ['npm', '--version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def get_node_path():
    """Get Node.js installation path."""
    try:
        result = subprocess.run(
            ['which', 'node'],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def parse_version(version_str):
    """Parse version string to tuple (major, minor, patch)."""
    if not version_str:
        return None
    
    # Remove 'v' prefix if present
    version_str = version_str.lstrip('v')
    
    try:
        parts = version_str.split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return (major, minor, patch)
    except (ValueError, IndexError):
        return None


def main():
    """Main function."""
    print("=" * 60)
    print("Node.js Version Check")
    print("=" * 60)
    print()
    
    # Get current versions
    node_version = get_node_version()
    npm_version = get_npm_version()
    node_path = get_node_path()
    
    # Display current versions
    if node_version:
        print(f"✅ Node.js version: {node_version}")
        node_parsed = parse_version(node_version)
        if node_parsed:
            print(f"   Major: {node_parsed[0]}, Minor: {node_parsed[1]}, Patch: {node_parsed[2]}")
    else:
        print("❌ Node.js not found or not in PATH")
        print("   Install Node.js: https://nodejs.org/")
        sys.exit(1)
    
    if npm_version:
        print(f"✅ npm version: {npm_version}")
    else:
        print("⚠️  npm not found")
    
    if node_path:
        print(f"📍 Node.js path: {node_path}")
    
    print()
    
    # Check against requirements
    print("=" * 60)
    print("Version Requirements")
    print("=" * 60)
    print()
    
    # From Dockerfile.frontend
    print("📦 Dockerfile.frontend: node:18-alpine")
    print("   Required: Node.js 18.x")
    
    # From .codacy/codacy.yaml
    print("🔍 Codacy config: node@22.2.0")
    print("   Recommended: Node.js 22.2.0")
    
    print()
    
    # Compare versions
    if node_parsed:
        major = node_parsed[0]
        
        print("=" * 60)
        print("Compatibility Check")
        print("=" * 60)
        print()
        
        # Check Dockerfile requirement (18)
        if major >= 18:
            print(f"✅ Compatible with Dockerfile (requires 18+, you have {major})")
        else:
            print(f"❌ Not compatible with Dockerfile (requires 18+, you have {major})")
            print("   Consider upgrading to Node.js 18 or higher")
        
        # Check Codacy recommendation (22)
        if major >= 22:
            print(f"✅ Meets Codacy recommendation (22.2.0, you have {major})")
        elif major >= 18:
            print(f"⚠️  Below Codacy recommendation (22.2.0, you have {major})")
            print("   Current version should work, but 22.2.0 is recommended")
        else:
            print(f"❌ Below Codacy recommendation (22.2.0, you have {major})")
        
        print()
        
        # Recommendations
        print("=" * 60)
        print("Recommendations")
        print("=" * 60)
        print()
        
        if major < 18:
            print("❌ Upgrade required:")
            print("   - Minimum: Node.js 18.x (for Dockerfile)")
            print("   - Recommended: Node.js 22.2.0 (for Codacy)")
            print()
            print("   Install Node.js 22:")
            print("     - Using nvm: nvm install 22 && nvm use 22")
            print("     - Download: https://nodejs.org/")
        elif major < 22:
            print("⚠️  Consider upgrading:")
            print("   - Current: Node.js {}.x".format(major))
            print("   - Recommended: Node.js 22.2.0 (for Codacy)")
            print()
            print("   Upgrade with nvm:")
            print("     nvm install 22.2.0")
            print("     nvm use 22.2.0")
        else:
            print("✅ Node.js version is up to date!")
            print(f"   Current: {node_version}")
            print("   Meets all requirements")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
