import psycopg2
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

def update_attendance_table():
    """Update the attendance table schema"""
    try:
        # Connect to the database
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()

        # Drop existing attendances table
        logger.info("Dropping existing attendances table...")
        cur.execute("DROP TABLE IF EXISTS attendances CASCADE")
        
        # Create new attendances table
        logger.info("Creating new attendances table...")
        cur.execute("""
            CREATE TABLE attendances (
                id SERIAL PRIMARY KEY,
                lecture_id INTEGER NOT NULL REFERENCES lectures(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                timestamp TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20),
                marked_by_id INTEGER REFERENCES users(id),
                verification_method VARCHAR(20),
                verification_data TEXT,
                notes TEXT,
                created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Commit the changes
        conn.commit()
        logger.info("Attendance table updated successfully!")
        
    except Exception as e:
        logger.error(f"Error updating attendance table: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    update_attendance_table()
