"""WSGI entry point for production."""
from app import create_app
from app.extensions import db
from config import ProductionConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app(ProductionConfig)

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

if __name__ == "__main__":
    app.run()
