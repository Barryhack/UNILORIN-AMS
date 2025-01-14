import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_database():
    try:
        # Connect to PostgreSQL server
        conn = psycopg2.connect(
            dbname='postgres',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        
        # Create a cursor object
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'attendance'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Creating database 'attendance'...")
            cursor.execute('CREATE DATABASE attendance')
            print("Database created successfully!")
        else:
            print("Database 'attendance' already exists.")
        
        cursor.close()
        conn.close()
        
        print("Testing connection to new database...")
        # Test connection to the new database
        test_conn = psycopg2.connect(
            dbname='attendance',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        test_conn.close()
        print("Successfully connected to the database!")
        return True
        
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return False

if __name__ == '__main__':
    create_database()
