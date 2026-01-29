#!/usr/bin/env python3
"""
Script to kill all processes using port 8000.
"""

import subprocess
import sys
import time

PORT = 8000

def find_processes_on_port(port: int) -> list[int]:
    """Find all PIDs using the specified port."""
    try:
        # Try lsof first (Linux/Mac)
        result = subprocess.run(
            ["lsof", "-ti", f":{port}"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            pids = [int(pid) for pid in result.stdout.strip().split("\n") if pid.strip()]
            return pids
    except FileNotFoundError:
        pass
    
    try:
        # Try fuser as fallback
        result = subprocess.run(
            ["fuser", f"{port}/tcp"],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            # fuser output format: "8000/tcp:  1234  5678"
            pids = []
            for line in result.stdout.split("\n"):
                if ":" in line:
                    pid_str = line.split(":")[1].strip()
                    pids.extend([int(p) for p in pid_str.split() if p.isdigit()])
            return pids
    except FileNotFoundError:
        pass
    
    return []

def kill_process(pid: int) -> bool:
    """Kill a process by PID."""
    try:
        subprocess.run(["kill", "-9", str(pid)], check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False

def main():
    print(f"Finding processes using port {PORT}...")
    print()
    
    pids = find_processes_on_port(PORT)
    
    if not pids:
        print(f"✓ Port {PORT} is already free")
        return 0
    
    print(f"Found {len(pids)} process(es): {', '.join(map(str, pids))}")
    print()
    
    # Show process details
    for pid in pids:
        try:
            result = subprocess.run(
                ["ps", "-p", str(pid), "-o", "pid,cmd", "--no-headers"],
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                print(f"Process {pid}: {result.stdout.strip()}")
            else:
                print(f"Process {pid}: (details not available)")
        except Exception:
            print(f"Process {pid}: (details not available)")
    
    print()
    print("Killing processes...")
    
    # Kill all processes
    killed = 0
    for pid in pids:
        if kill_process(pid):
            print(f"✓ Killed process {pid}")
            killed += 1
        else:
            print(f"✗ Failed to kill process {pid} (may have already ended)")
    
    time.sleep(1)
    
    # Verify port is free
    remaining = find_processes_on_port(PORT)
    if remaining:
        print()
        print(f"⚠ Warning: Port {PORT} may still be in use by: {', '.join(map(str, remaining))}")
        return 1
    else:
        print()
        print(f"✓ Port {PORT} is now free")
        print()
        print("You can now start the server with:")
        print("  python backend/main.py")
        return 0

if __name__ == "__main__":
    sys.exit(main())
