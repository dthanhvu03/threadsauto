#!/usr/bin/env python3
"""
Migration script: Create feed_items table.

This script creates the feed_items table to store feed posts from Threads with history tracking.

Usage:
    python scripts/migration/run_feed_items_migration.py
    
    # Or with custom MySQL credentials:
    python scripts/migration/run_feed_items_migration.py --host localhost --port 3306 --user threads_user --password "" --database threads_analytics
"""

# Standard library
import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Third-party
import pymysql
from pymysql.cursors import DictCursor

# Local
from config.storage_config_loader import get_storage_config_from_env
from services.logger import StructuredLogger


def check_table_exists(cursor, table_name: str, database: str = "threads_analytics") -> bool:
    """Check if table exists."""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s
    """, (database, table_name))
    result = cursor.fetchone()
    return result['count'] > 0


def run_migration(
    host: str = "localhost",
    port: int = 3306,
    user: str = "threads_user",
    password: str = "",
    database: str = "threads_analytics"
):
    """
    Run migration to create feed_items table.
    
    Args:
        host: MySQL host
        port: MySQL port
        user: MySQL user
        password: MySQL password
        database: Database name
    """
    logger = StructuredLogger(name="feed_items_migration")
    conn = None
    
    try:
        # Connect to MySQL
        logger.log_step(
            step="CONNECT_MYSQL",
            result="IN_PROGRESS",
            host=host,
            port=port,
            user=user,
            database=database
        )
        
        conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            charset='utf8mb4',
            cursorclass=DictCursor
        )
        
        cursor = conn.cursor()
        
        logger.log_step(
            step="CONNECT_MYSQL",
            result="SUCCESS",
            host=host,
            port=port,
            user=user,
            database=database
        )
        
        # Check if table already exists
        if check_table_exists(cursor, 'feed_items', database):
            logger.log_step(
                step="CHECK_TABLE_EXISTS",
                result="INFO",
                note="feed_items table already exists, skipping migration",
                table="feed_items"
            )
            print("✓ feed_items table already exists. Migration not needed.")
            return
        
        # Read migration SQL file
        migration_file = Path(__file__).parent.parent.parent / "docker" / "mysql" / "migrations" / "005_create_feed_items_table.sql"
        
        if not migration_file.exists():
            raise FileNotFoundError(f"Migration file not found: {migration_file}")
        
        logger.log_step(
            step="READ_MIGRATION_FILE",
            result="IN_PROGRESS",
            file_path=str(migration_file)
        )
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        logger.log_step(
            step="READ_MIGRATION_FILE",
            result="SUCCESS",
            file_path=str(migration_file)
        )
        
        # Execute migration
        logger.log_step(
            step="EXECUTE_MIGRATION",
            result="IN_PROGRESS",
            table="feed_items"
        )
        
        # Execute SQL statements one by one
        # Remove USE statement if present (we're already connected to the database)
        sql_without_use = migration_sql.replace('USE threads_analytics;', '').replace('USE threads_analytics', '').strip()
        
        # Split by semicolon but handle multi-line statements properly
        statements = []
        current_statement = []
        
        for line in sql_without_use.split('\n'):
            line = line.strip()
            # Skip empty lines and comments
            if not line or line.startswith('--'):
                continue
            
            current_statement.append(line)
            
            # If line ends with semicolon, it's the end of a statement
            if line.endswith(';'):
                statement = ' '.join(current_statement).rstrip(';').strip()
                if statement:
                    statements.append(statement)
                current_statement = []
        
        # Add any remaining statement
        if current_statement:
            statement = ' '.join(current_statement).strip()
            if statement:
                statements.append(statement)
        
        # Execute each statement
        executed_count = 0
        for i, statement in enumerate(statements, 1):
            if not statement:
                continue
            
            try:
                cursor.execute(statement)
                executed_count += 1
                logger.log_step(
                    step="EXECUTE_STATEMENT",
                    result="SUCCESS",
                    statement_number=i,
                    total_statements=len(statements)
                )
            except pymysql.Error as e:
                error_str = str(e)
                error_code = e.args[0] if e.args else None
                # Ignore errors for duplicate table/index (already exists)
                # MySQL error 1050: Table already exists
                # MySQL error 1061: Duplicate key name (for indexes)
                if (error_code in (1050, 1061) or 
                    "already exists" in error_str.lower() or 
                    "duplicate key name" in error_str.lower()):
                    logger.log_step(
                        step="EXECUTE_STATEMENT",
                        result="WARNING",
                        statement_number=i,
                        error=f"Already exists (safe to ignore): {error_str[:200]}",
                        error_code=error_code
                    )
                    executed_count += 1  # Count as executed even if it already exists
                    continue
                else:
                    logger.log_step(
                        step="EXECUTE_STATEMENT",
                        result="ERROR",
                        statement_number=i,
                        error=error_str,
                        statement_preview=statement[:200] + "..." if len(statement) > 200 else statement
                    )
                    raise
        
        conn.commit()
        
        logger.log_step(
            step="EXECUTE_MIGRATION",
            result="SUCCESS",
            table="feed_items"
        )
        
        # Verify table was created
        if check_table_exists(cursor, 'feed_items', database):
            logger.log_step(
                step="VERIFY_MIGRATION",
                result="SUCCESS",
                table="feed_items",
                note="Table created successfully"
            )
            print("✓ feed_items table created successfully!")
        else:
            raise RuntimeError("Table feed_items was not created after migration")
        
    except pymysql.Error as e:
        logger.log_step(
            step="MIGRATION_ERROR",
            result="FAILED",
            error=str(e),
            error_type=type(e).__name__
        )
        if conn:
            conn.rollback()
        raise
    except Exception as e:
        logger.log_step(
            step="MIGRATION_ERROR",
            result="FAILED",
            error=str(e),
            error_type=type(e).__name__
        )
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create feed_items table migration")
    parser.add_argument("--host", default="localhost", help="MySQL host")
    parser.add_argument("--port", type=int, default=3306, help="MySQL port")
    parser.add_argument("--user", default="threads_user", help="MySQL user")
    parser.add_argument("--password", default="", help="MySQL password")
    parser.add_argument("--database", default="threads_analytics", help="Database name")
    
    args = parser.parse_args()
    
    # Try to get config from environment if not provided
    if not args.password:
        try:
            storage_config = get_storage_config_from_env()
            mysql_config = storage_config.mysql
            args.host = mysql_config.host
            args.port = mysql_config.port
            args.user = mysql_config.user
            args.password = mysql_config.password
            args.database = mysql_config.database
        except Exception:
            # Use defaults if config not available
            pass
    
    try:
        run_migration(
            host=args.host,
            port=args.port,
            user=args.user,
            password=args.password,
            database=args.database
        )
        print("\n✓ Migration completed successfully!")
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
