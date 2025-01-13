"""WSGI entry point for production."""
from app import create_app
from app.extensions import db
from config import ProductionConfig
import logging
import sys

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
            db.session.execute('SELECT 1')
        return {'status': 'healthy'}, 200
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {'status': 'unhealthy', 'error': str(e)}, 503

# Initialize database in app context
with app.app_context():
    try:
        # Create database tables
        db.create_all()
        logger.info("Database tables created successfully")
        
        # Create default users if needed
        from app.models import User
        User.create_default_users()
        logger.info("Default users created successfully")
    except Exception as e:
        logger.error(f"Error during initialization: {str(e)}")
        raise

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
