"""WSGI entry point for production."""
from app import create_app
from app.extensions import db
from config import Config
import logging
import sys
import os
from sqlalchemy import text
import traceback
import time
from sqlalchemy.exc import SQLAlchemyError
from app.models.department import Department
from app.models.user import User
from app.models.course import Course

# Set environment based on ENV variable
flask_env = os.environ.get('FLASK_ENV', 'production')
os.environ['FLASK_DEBUG'] = '1' if flask_env == 'development' else '0'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Create the Flask application
app = create_app(Config)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

@app.before_request
def before_request():
    """Ensure database connection is active."""
    try:
        db.session.execute(text('SELECT 1'))
        db.session.commit()
    except Exception as e:
        logger.error(f"Database connection error: {str(e)}\n{traceback.format_exc()}")
        db.session.rollback()
        try:
            db.session.remove()
            db.engine.dispose()
        except:
            pass
        raise

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Check database connection
        db.session.execute(text('SELECT 1'))
        db.session.commit()
        
        # Check if essential models exist
        dept_count = Department.query.count()
        user_count = User.query.count()
        course_count = Course.query.count()
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'models': {
                'departments': dept_count,
                'users': user_count,
                'courses': course_count
            }
        }, 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}\n{traceback.format_exc()}")
        return {
            'status': 'unhealthy',
            'error': str(e)
        }, 500

def init_database(max_retries=5, retry_delay=5):
    """Initialize database with retry mechanism."""
    retry_count = 0
    while retry_count < max_retries:
        try:
            logger.info("Attempting to initialize database...")
            db.create_all()
            
            # Create default departments if they don't exist
            from app.models.department import create_default_departments
            create_default_departments()
            
            # Create default admin user if it doesn't exist
            from app.models.user import create_default_admin
            create_default_admin()
            
            logger.info("Database initialization successful!")
            return True
        except SQLAlchemyError as e:
            retry_count += 1
            logger.error(f"Database initialization attempt {retry_count} failed: {str(e)}\n{traceback.format_exc()}")
            if retry_count < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                logger.error("Max retries reached. Database initialization failed.")
                raise
        except Exception as e:
            logger.error(f"Unexpected error during database initialization: {str(e)}\n{traceback.format_exc()}")
            raise

# Initialize database in app context
with app.app_context():
    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}\n{traceback.format_exc()}")
        sys.exit(1)

@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors."""
    logger.error(f"Internal Server Error: {str(error)}\n{traceback.format_exc()}")
    db.session.rollback()
    return "Internal Server Error", 500

@app.errorhandler(404)
def not_found_error(error):
    """Handle not found errors."""
    return "Not Found", 404

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
