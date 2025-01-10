import os
import psycopg2
from sqlalchemy import create_engine
from alembic.config import Config
from alembic import command

# Database connection parameters
DB_PARAMS = {
    'dbname': 'unilorin_ams_db',
    'user': 'unilorin_ams_db_user',
    'password': 'SblaolzfG7OjzX7kp0IQgvEJyDfYbE3I',
    'host': 'dpg-ctvrieij1k6c73dr4q90-a.oregon-postgres.render.com',
    'port': '5432'
}

# Construct DATABASE_URL
DATABASE_URL = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['dbname']}"

def apply_migrations():
    """Apply all pending migrations"""
    try:
        # Set DATABASE_URL environment variable
        os.environ['DATABASE_URL'] = DATABASE_URL
        
        # Create Alembic configuration
        alembic_cfg = Config("migrations/alembic.ini")
        
        # Override sqlalchemy.url in alembic.ini
        alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL)
        
        # Run migrations
        command.upgrade(alembic_cfg, "head")
        print("Migrations applied successfully!")
        
    except Exception as e:
        print(f"Error applying migrations: {str(e)}")
        raise

if __name__ == '__main__':
    apply_migrations()
