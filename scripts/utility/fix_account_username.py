#!/usr/bin/env python3
"""
Script để kiểm tra và fix username trong account metadata.

Usage:
    python scripts/utility/fix_account_username.py                    # List all accounts
    python scripts/utility/fix_account_username.py account_01          # Check account_01
    python scripts/utility/fix_account_username.py account_01 username # Set username for account_01
"""

import sys
from pathlib import Path
import json

# Setup path using common utility
from scripts.common import (
    setup_path,
    get_account_storage,
    get_mysql_config,
    print_header,
    print_section
)

# Add parent directory to path (must be after importing common)
setup_path()


def list_accounts():
    """List all accounts với username trong metadata."""
    try:
        storage = get_account_storage()
        accounts = storage.list_accounts()
        
        print_header("📋 ACCOUNTS & USERNAMES")
        print(f"{'Account ID':<20} {'Username':<30} {'Source':<20}")
        print_section("", width=80)
        
        for account in accounts:
            account_id = account.get('account_id', 'N/A')
            metadata = account.get('metadata', {})
            
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            username = metadata.get('username') or metadata.get('threads_username') or '❌ NOT SET'
            source = 'metadata' if username != '❌ NOT SET' else 'missing'
            
            print(f"{account_id:<20} {username:<30} {source:<20}")
        
        print_section("", width=80)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def check_account(account_id: str):
    """Check username cho một account."""
    try:
        storage = get_account_storage()
        
        account = storage.get_account(account_id)
        
        if not account:
            print(f"❌ Account '{account_id}' not found!")
            sys.exit(1)
        
        metadata = account.get('metadata', {})
        
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        username = metadata.get('username') or metadata.get('threads_username')
        
        print_header(f"📋 ACCOUNT: {account_id}")
        print(f"Username: {username or '❌ NOT SET'}")
        print(f"Metadata: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
        print_section("", width=80)
        
        if not username:
            print("\n⚠️  WARNING: Username not set!")
            print("   This will cause fetch metrics to extract username from browser page,")
            print("   which may get wrong username if browser is logged into different account.")
            print("\n   To fix:")
            print(f"   python {sys.argv[0]} {account_id} your_username")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def set_username(account_id: str, username: str):
    """Set username cho một account."""
    try:
        storage = get_account_storage()
        
        account = storage.get_account(account_id)
        
        if not account:
            print(f"❌ Account '{account_id}' not found!")
            sys.exit(1)
        
        # Get current metadata
        metadata = account.get('metadata', {})
        
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except:
                metadata = {}
        
        # Update username
        metadata['username'] = username
        metadata['threads_username'] = username  # Alternative key
        
        # Save
        storage.update_account(account_id, metadata=metadata)
        
        print_header(f"✅ UPDATED: {account_id}")
        print(f"Username: {username}")
        print(f"Metadata: {json.dumps(metadata, indent=2, ensure_ascii=False)}")
        print_section("", width=80)
        print("\n✅ Username đã được lưu vào metadata!")
        print("   Fetch metrics sẽ dùng username này thay vì extract từ page.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Main function."""
    if len(sys.argv) == 1:
        # List all accounts
        list_accounts()
    elif len(sys.argv) == 2:
        # Check one account
        account_id = sys.argv[1]
        check_account(account_id)
    elif len(sys.argv) == 3:
        # Set username
        account_id = sys.argv[1]
        username = sys.argv[2]
        
        # Remove @ prefix if present
        if username.startswith('@'):
            username = username[1:]
        
        set_username(account_id, username)
    else:
        print("Usage:")
        print(f"  {sys.argv[0]}                    # List all accounts")
        print(f"  {sys.argv[0]} account_id         # Check account")
        print(f"  {sys.argv[0]} account_id username # Set username")
        sys.exit(1)


if __name__ == "__main__":
    main()
