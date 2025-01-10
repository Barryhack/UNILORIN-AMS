import psycopg2
import os
from dotenv import load_dotenv
import logging
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def activate_admin():
    """Activate the admin user account."""
    conn = None
    cur = None
    try:
        # Get database URL from environment
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL not found in environment!")
            return
            
        # Parse the URL
        result = urlparse(db_url)
        db_info = {
            'dbname': result.path[1:],
            'user': result.username,
            'password': result.password,
            'host': result.hostname,
            'port': result.port or '5432'
        }
        
        # Connect to the database
        logger.info(f"Connecting to database at {db_info['host']}...")
        conn = psycopg2.connect(**db_info)
        
        # Create a cursor
        cur = conn.cursor()
        
        # Find admin user
        cur.execute("SELECT id, email, is_active FROM users WHERE id_number = '19/52AD001'")
        admin = cur.fetchone()
        
        if not admin:
            logger.error("Admin user not found!")
            return
            
        logger.info(f"Found admin user: {admin[1]}")
        logger.info(f"Current status: {'Active' if admin[2] else 'Inactive'}")
        
        # Activate the account
        cur.execute("""
            UPDATE users 
            SET is_active = true 
            WHERE id_number = '19/52AD001'
        """)
        
        # Commit the changes
        conn.commit()
        logger.info("Admin account activated successfully!")
        
    except Exception as e:
        logger.error(f"Error activating admin account: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    activate_admin()
