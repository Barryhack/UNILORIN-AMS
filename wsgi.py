"""WSGI entry point for production."""
from app import create_app
from app.extensions import db
from config import ProductionConfig
import logging
import sys
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/app.log')
    ]
)
logger = logging.getLogger(__name__)

app = create_app(ProductionConfig)

# Health check endpoint
@app.route('/health')
def health_check():
    try:
        # Test database connection
        with app.app_context():
            db.session.execute(text('SELECT 1'))
            # Also verify users table exists and has login_id column
            result = db.session.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'login_id'")
            ).fetchone()
            if not result:
                raise Exception("users table is missing login_id column")
        return {'status': 'healthy'}, 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {'status': 'unhealthy', 'error': str(e)}, 503

def init_database():
    """Initialize the database with retries."""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
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
            
            return True
            
        except Exception as e:
            retry_count += 1
            logger.error(f"Database initialization attempt {retry_count} failed: {str(e)}")
            if retry_count == max_retries:
                logger.error("Maximum retries reached. Database initialization failed.")
                raise
            
# Initialize database in app context
with app.app_context():
    try:
        init_database()
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        # Don't raise the error here, let the app continue to start
        # The health check endpoint will report the database status

# Error handlers
@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal Server Error: {str(error)}")
    return {"error": "Internal Server Error"}, 500

@app.errorhandler(404)
def not_found_error(error):
    return {"error": "Not Found"}, 404

if __name__ == "__main__":
    app.run()
