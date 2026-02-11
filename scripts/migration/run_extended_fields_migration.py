#!/usr/bin/env python3
"""
Migration script: Add extended fields to feed_posts table.

This script adds new columns to feed_posts table:
- User Information: user_id, user_display_name, user_avatar_url, is_verified
- Post Metadata: post_url, is_reply, parent_post_id, thread_id, quoted_post
- Text Entities: hashtags, mentions, links
- Media Metadata: media_type, video_duration
- Additional Counts: view_count, share_count

Usage:
    python scripts/migration/run_extended_fields_migration.py
    
    # Or with custom MySQL credentials:
    python scripts/migration/run_extended_fields_migration.py --host localhost --port 3306 --user threads_user --password "" --database threads_analytics
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


def check_column_exists(cursor, table_name: str, column_name: str, database: str = "threads_analytics") -> bool:
    """Check if column exists in table."""
    cursor.execute("""
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = %s
        AND COLUMN_NAME = %s
    """, (database, table_name, column_name))
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
    Run migration to add extended fields to feed_posts table.
    
    Args:
        host: MySQL host
        port: MySQL port
        user: MySQL user
        password: MySQL password
        database: Database name
    """
    logger = StructuredLogger(name="extended_fields_migration")
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
        
        # Read migration SQL file
        migration_file = Path(__file__).parent.parent.parent / "docker" / "mysql" / "migrations" / "007_add_extended_fields_to_feed_posts.sql"
        
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
        
        # Check if feed_posts table exists
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s 
            AND TABLE_NAME = 'feed_posts'
        """, (database,))
        result = cursor.fetchone()
        
        if result['count'] == 0:
            raise ValueError("feed_posts table does not exist. Please run 006_create_feed_tables.sql migration first.")
        
        # Check which columns already exist
        columns_to_add = [
            'user_id', 'user_display_name', 'user_avatar_url', 'is_verified',
            'post_url', 'is_reply', 'parent_post_id', 'thread_id', 'quoted_post',
            'hashtags', 'mentions', 'links',
            'media_type', 'video_duration',
            'view_count', 'share_count'
        ]
        
        existing_columns = []
        for column_name in columns_to_add:
            if check_column_exists(cursor, 'feed_posts', column_name, database):
                existing_columns.append(column_name)
        
        if existing_columns:
            logger.log_step(
                step="CHECK_EXISTING_COLUMNS",
                result="INFO",
                existing_columns=existing_columns,
                note="Some columns already exist. Duplicate column errors will be handled gracefully."
            )
        
        # Execute migration SQL
        logger.log_step(
            step="EXECUTE_MIGRATION",
            result="IN_PROGRESS",
            columns_to_add=columns_to_add
        )
        
        # Execute the entire SQL file (it uses IF NOT EXISTS so safe to run multiple times)
        try:
            # Remove USE statement if present (we're already connected to the database)
            sql_to_execute = migration_sql.replace('USE threads_analytics;', '').strip()
            
            # Split by semicolon but handle multi-line statements properly
            statements = []
            current_statement = []
            
            for line in sql_to_execute.split('\n'):
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
                    # Ignore errors for duplicate column/index (already exists)
                    # MySQL error 1060: Duplicate column name
                    # MySQL error 1061: Duplicate key name (for indexes)
                    # Error message format: (1060, "Duplicate column name 'column_name'")
                    # Error message format: (1061, "Duplicate key name 'index_name'")
                    if (error_code in (1060, 1061) or 
                        "duplicate column name" in error_str.lower() or 
                        "duplicate key name" in error_str.lower() or
                        "already exists" in error_str.lower()):
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
            
            logger.log_step(
                step="EXECUTE_MIGRATION",
                result="SUCCESS",
                executed_statements=executed_count,
                total_statements=len(statements)
            )
            
        except Exception as e:
            logger.log_step(
                step="EXECUTE_MIGRATION",
                result="ERROR",
                error=str(e),
                error_type=type(e).__name__
            )
            raise
        
        conn.commit()
        
        logger.log_step(
            step="EXECUTE_MIGRATION",
            result="SUCCESS",
            columns_to_add=columns_to_add
        )
        
        # Verify columns were added
        logger.log_step(
            step="VERIFY_MIGRATION",
            result="IN_PROGRESS"
        )
        
        added_columns = []
        for column_name in columns_to_add:
            if check_column_exists(cursor, 'feed_posts', column_name, database):
                added_columns.append(column_name)
        
        if len(added_columns) == len(columns_to_add):
            logger.log_step(
                step="VERIFY_MIGRATION",
                result="SUCCESS",
                added_columns=added_columns
            )
            print("✅ Migration completed successfully!")
            print(f"   Added columns: {', '.join(added_columns)}")
        else:
            missing = set(columns_to_add) - set(added_columns)
            logger.log_step(
                step="VERIFY_MIGRATION",
                result="WARNING",
                added_columns=added_columns,
                missing_columns=list(missing)
            )
            print("⚠️  Migration completed with warnings")
            print(f"   Added columns: {', '.join(added_columns) if added_columns else 'None'}")
            if missing:
                print(f"   Missing columns: {', '.join(missing)}")
        
    except Exception as e:
        logger.log_step(
            step="MIGRATION",
            result="ERROR",
            error=str(e),
            error_type=type(e).__name__
        )
        print(f"❌ Migration failed: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
            logger.log_step(
                step="CLOSE_CONNECTION",
                result="SUCCESS"
            )


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run extended fields migration")
    parser.add_argument("--host", type=str, default=None, help="MySQL host")
    parser.add_argument("--port", type=int, default=None, help="MySQL port")
    parser.add_argument("--user", type=str, default=None, help="MySQL user")
    parser.add_argument("--password", type=str, default=None, help="MySQL password")
    parser.add_argument("--database", type=str, default=None, help="Database name")
    
    args = parser.parse_args()
    
    # Try to get config from environment if not provided
    try:
        storage_config = get_storage_config_from_env()
        mysql_config = storage_config.mysql if storage_config.mysql else None
        
        host = args.host or (mysql_config.host if mysql_config else "localhost")
        port = args.port or (mysql_config.port if mysql_config else 3306)
        user = args.user or (mysql_config.user if mysql_config else "threads_user")
        password = args.password or (mysql_config.password if mysql_config else "")
        database = args.database or (mysql_config.database if mysql_config else "threads_analytics")
    except Exception:
        # Fallback to defaults or command line args
        host = args.host or "localhost"
        port = args.port or 3306
        user = args.user or "threads_user"
        password = args.password or ""
        database = args.database or "threads_analytics"
    
    run_migration(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )


if __name__ == "__main__":
    main()
