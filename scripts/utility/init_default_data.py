#!/usr/bin/env python3
"""
Initialize default data: config và selectors vào MySQL.

Usage:
    python scripts/init_default_data.py --mysql-password=your_password
"""

import sys
from pathlib import Path

# Setup path using common utility
from scripts.common import setup_path, get_logger, get_mysql_config, print_header, print_section

# Add parent to path (must be after importing common)
setup_path()

from services.storage.config_storage import ConfigStorage
from services.storage.selectors_storage import SelectorStorage
from config.storage import load_config, save_config
from config.config import Config
from config.selectors_storage import _get_default_selectors
from datetime import datetime
import argparse


def init_default_config(mysql_password: str) -> bool:
    """Initialize default config vào MySQL."""
    print_header("⚙️  Initializing default config in MySQL...")
    
    try:
        mysql_config = get_mysql_config()
        logger = get_logger("init_config")
        
        # Override password if provided
        if mysql_password:
            mysql_config.password = mysql_password
        
        config_storage = ConfigStorage(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password,
            database=mysql_config.database,
            logger=logger
        )
        
        # Load từ file nếu có, otherwise dùng defaults
        config_file = Path("./config.json")
        if config_file.exists():
            print("   ℹ️  Loading config from config.json...")
            config = load_config(use_mysql=False)  # Load từ file
        else:
            print("   ℹ️  Using default config...")
            config = Config()  # Default config
        
        # Save vào MySQL
        config_storage.save_config(config)
        print("   ✅ Default config saved to MySQL")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def init_default_selectors(mysql_password: str) -> bool:
    """Initialize default selectors vào MySQL."""
    print_header("🎯 Initializing default selectors in MySQL...")
    
    try:
        mysql_config = get_mysql_config()
        logger = get_logger("init_selectors")
        
        # Override password if provided
        if mysql_password:
            mysql_config.password = mysql_password
        
        selector_storage = SelectorStorage(
            host=mysql_config.host,
            port=mysql_config.port,
            user=mysql_config.user,
            password=mysql_config.password,
            database=mysql_config.database,
            logger=logger
        )
        
        platforms = ["threads", "facebook"]
        versions = ["v1"]
        
        total = 0
        
        for platform in platforms:
            for version in versions:
                try:
                    # Get default selectors từ hardcoded
                    selectors = _get_default_selectors(platform, version)
                    
                    if selectors:
                        metadata = {
                            "last_updated": datetime.now().isoformat(),
                            "platform": platform,
                            "version": version,
                            "source": "default_hardcoded"
                        }
                        
                        selector_storage.save_selectors(
                            platform=platform,
                            version=version,
                            selectors=selectors,
                            metadata=metadata
                        )
                        
                        total += len(selectors)
                        print(f"   ✅ {platform}/{version}: {len(selectors)} selector groups")
                    
                except Exception as e:
                    print(f"   ⚠️  Failed to save {platform}/{version}: {str(e)}")
                    continue
        
        print(f"   ✅ Total: {total} selector groups saved")
        return True
        
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Initialize default config and selectors in MySQL")
    
    parser.add_argument("--mysql-host", default="localhost", help="MySQL host")
    parser.add_argument("--mysql-port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--mysql-user", default="threads_user", help="MySQL user")
    parser.add_argument("--mysql-password", required=True, help="MySQL password")
    parser.add_argument("--mysql-database", default="threads_analytics", help="MySQL database")
    
    args = parser.parse_args()
    
    print("🔄 Initialize Default Data: Config & Selectors")
    print_header("", width=60)
    
    success_config = init_default_config(args.mysql_password)
    success_selectors = init_default_selectors(args.mysql_password)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print_header("", width=60)
    print(f"Config: {'✅ Success' if success_config else '❌ Failed'}")
    print(f"Selectors: {'✅ Success' if success_selectors else '❌ Failed'}")
    
    if success_config and success_selectors:
        print("\n✅ All default data initialized successfully!")
        return 0
    else:
        print("\n⚠️  Some operations failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
