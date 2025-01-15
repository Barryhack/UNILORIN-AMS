"""WSGI entry point for production."""
from app import create_app
from app.extensions import db
from config import Config
import logging
import sys
import os
from sqlalchemy import text
import traceback

# Force development mode
os.environ['FLASK_ENV'] = 'development'
os.environ['FLASK_DEBUG'] = '1'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Create the application with development config
app = create_app(Config)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        with app.app_context():
            # Log the database URL (without credentials)
            db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if db_url:
                # Mask credentials in URL
                masked_url = db_url.replace('//', '//<credentials>@') if '@' in db_url else db_url
                logger.info(f"Attempting database connection to: {masked_url}")
            
            # Test connection
            db.session.execute(text('SELECT 1'))
            db.session.commit()
            
            # Verify users table
            result = db.session.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'login_id'")
            ).fetchone()
            if not result:
                raise Exception("users table is missing login_id column")
            
            logger.info("Health check passed successfully")
            return {'status': 'healthy', 'database': 'connected'}, 200
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Health check failed: {error_msg}")
        logger.error(traceback.format_exc())
        return {
            'status': 'unhealthy',
            'error': error_msg,
            'database': 'disconnected'
        }, 503

def init_database():
    """Initialize the database with retries."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Database initialization attempt {retry_count + 1}/{max_retries}")
            
            from app.models import User, Department
            
            # Create database tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Create default department if it doesn't exist
            dept = Department.query.filter_by(code='CSC').first()
            if not dept:
                dept = Department(name='Computer Science', code='CSC')
                db.session.add(dept)
                db.session.commit()
                logger.info("Created default department")
            else:
                logger.info("Default department already exists")
            
            # Create default admin user if it doesn't exist
            admin = User.query.filter_by(login_id='ADMIN001').first()
            if not admin:
                admin = User(
                    login_id='ADMIN001',
                    email='admin@example.com',
                    first_name='Admin',
                    last_name='User',
                    role='admin'
                )
                admin.password = 'admin123'
                admin.department_id = dept.id
                db.session.add(admin)
                db.session.commit()
                logger.info("Created default admin user")
            else:
                logger.info("Default admin user already exists")
            
            return True
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Database initialization attempt {retry_count} failed: {str(e)}")
            logger.error(traceback.format_exc())
            if retry_count == max_retries:
                logger.error("Maximum retries reached. Database initialization failed.")
                raise
            db.session.rollback()

# Initialize database in app context
with app.app_context():
    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        logger.error(traceback.format_exc())
        # Don't raise the error here - let the app continue to start
        # The health check endpoint will report the database status

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {str(error)}")
    logger.error(traceback.format_exc())
    return {"error": "Internal Server Error", "message": str(error)}, 500

@app.errorhandler(404)
def not_found_error(error):
    return {"error": "Not Found", "message": str(error)}, 404

if __name__ == "__main__":
    app.run()
