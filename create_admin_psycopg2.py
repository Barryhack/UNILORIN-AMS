import psycopg2
from werkzeug.security import generate_password_hash
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_PARAMS = {
    'dbname': 'unilorin_ams_db',
    'user': 'unilorin_ams_db_user',
    'password': 'SblaolzfG7OjzX7kp0IQgvEJyDfYbE3I',
    'host': 'dpg-ctvrieij1k6c73dr4q90-a.oregon-postgres.render.com',
    'port': '5432'
}

def setup_admin():
    """Create admin user in production database"""
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        # Check if admin user exists
        cur.execute("SELECT * FROM users WHERE id_number = %s", ("19/52AD001",))
        admin = cur.fetchone()
        
        # Hash the password
        hashed_password = generate_password_hash('Admin@2024')
        
        if admin:
            logger.info("Admin user exists, updating password and status")
            cur.execute(
                "UPDATE users SET password_hash = %s, is_active = %s WHERE id_number = %s",
                (hashed_password, True, "19/52AD001")
            )
            logger.info("Admin password and status updated successfully")
        else:
            logger.info("Creating new admin user")
            cur.execute("""
                INSERT INTO users (name, email, role, id_number, password_hash, is_active)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                "Administrator",
                "admin@unilorin.edu.ng",
                "admin",
                "19/52AD001",
                hashed_password,
                True
            ))
            logger.info("Admin user created successfully")
        
        # Commit the changes
        conn.commit()
        
        # Verify users in database
        cur.execute("SELECT id_number, email FROM users")
        users = cur.fetchall()
        logger.info(f"Users in database: {users}")
        
    except Exception as e:
        logger.error(f"Error during admin setup: {str(e)}")
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    setup_admin()
