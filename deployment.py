"""Deployment script for render.com."""
from app import create_app
from app.extensions import db
from config import ProductionConfig
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def deploy():
    """Initialize the application for deployment."""
    app = create_app(ProductionConfig)
    
    try:
        with app.app_context():
            # Create database tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Create default users if needed
            from app.models import User
            User.create_default_users()
            logger.info("Default users created successfully")
            
    except Exception as e:
        logger.error(f"Error during deployment: {str(e)}")
        raise

if __name__ == '__main__':
    deploy()
