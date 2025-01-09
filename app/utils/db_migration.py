"""Database migration utilities for PostgreSQL."""
import logging
import sqlite3
import psycopg2
from psycopg2.extras import DictCursor
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseMigrator:
    """Handle migration from SQLite to PostgreSQL."""
    
    def __init__(self, sqlite_path, pg_config):
        """Initialize migrator.
        
        Args:
            sqlite_path: Path to SQLite database
            pg_config: PostgreSQL connection configuration dictionary
        """
        self.sqlite_path = sqlite_path
        self.pg_config = pg_config
    
    def migrate(self):
        """Perform migration from SQLite to PostgreSQL."""
        try:
            # Connect to databases
            sqlite_conn = sqlite3.connect(self.sqlite_path)
            sqlite_conn.row_factory = sqlite3.Row
            
            pg_conn = psycopg2.connect(**self.pg_config)
            pg_conn.autocommit = False
            
            # Get list of tables
            tables = self._get_sqlite_tables(sqlite_conn)
            
            # Start transaction
            with pg_conn:
                with pg_conn.cursor() as pg_cursor:
                    # Migrate each table
                    for table in tables:
                        self._migrate_table(sqlite_conn, pg_cursor, table)
                
                # Commit transaction
                pg_conn.commit()
            
            logger.info("Migration completed successfully")
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            if 'pg_conn' in locals():
                pg_conn.rollback()
            raise
        
        finally:
            if 'sqlite_conn' in locals():
                sqlite_conn.close()
            if 'pg_conn' in locals():
                pg_conn.close()
    
    def _get_sqlite_tables(self, conn):
        """Get list of tables from SQLite database."""
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row['name'] for row in cursor.fetchall()]
    
    def _migrate_table(self, sqlite_conn, pg_cursor, table):
        """Migrate a single table from SQLite to PostgreSQL."""
        logger.info(f"Migrating table: {table}")
        
        # Get table schema
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = sqlite_cursor.fetchall()
        
        # Create table in PostgreSQL
        column_defs = []
        for col in columns:
            name = col['name']
            type_ = self._convert_type(col['type'])
            nullable = '' if col['notnull'] else 'NULL'
            default = f"DEFAULT {col['dflt_value']}" if col['dflt_value'] else ''
            primary_key = 'PRIMARY KEY' if col['pk'] else ''
            
            column_defs.append(f"{name} {type_} {nullable} {default} {primary_key}".strip())
        
        create_sql = f"CREATE TABLE IF NOT EXISTS {table} (\n    " + ",\n    ".join(column_defs) + "\n)"
        pg_cursor.execute(create_sql)
        
        # Copy data
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()
        
        if rows:
            columns = [col['name'] for col in columns]
            placeholders = ','.join(['%s'] * len(columns))
            insert_sql = f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})"
            
            for row in rows:
                values = [row[col] for col in columns]
                pg_cursor.execute(insert_sql, values)
        
        logger.info(f"Migrated {len(rows)} rows from table {table}")
    
    def _convert_type(self, sqlite_type):
        """Convert SQLite type to PostgreSQL type."""
        type_mapping = {
            'INTEGER': 'INTEGER',
            'REAL': 'DOUBLE PRECISION',
            'TEXT': 'TEXT',
            'BLOB': 'BYTEA',
            'BOOLEAN': 'BOOLEAN',
            'DATETIME': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME'
        }
        
        sqlite_type = sqlite_type.upper().split('(')[0]
        return type_mapping.get(sqlite_type, 'TEXT')

def migrate_to_postgres(app):
    """Migrate database from SQLite to PostgreSQL.
    
    Args:
        app: Flask application instance
    """
    # Backup current database
    from app.utils.backup import DatabaseBackup
    backup = DatabaseBackup(app.config['SQLITE_DATABASE_PATH'])
    backup.create_backup(note="Pre-migration backup")
    
    # PostgreSQL configuration
    pg_config = {
        'dbname': os.getenv('POSTGRES_DB', 'attendance'),
        'user': os.getenv('POSTGRES_USER', 'postgres'),
        'password': os.getenv('POSTGRES_PASSWORD'),
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432')
    }
    
    # Perform migration
    migrator = DatabaseMigrator(
        sqlite_path=app.config['SQLITE_DATABASE_PATH'],
        pg_config=pg_config
    )
    
    try:
        migrator.migrate()
        logger.info("Database migration completed successfully")
        
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise
