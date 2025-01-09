"""Application entry point."""
import os
from app import create_app, socketio

app = create_app()

def init_database():
    """Initialize the database with default data."""
    with app.app_context():
        logger = logging.getLogger(__name__)
        logger.info("Creating database tables...")
        db.create_all()
        
        logger.info("Creating default users...")
        from app.models.user import create_default_users, User
        create_default_users()
        
        # Verify users exist
        admin = User.query.filter_by(email='admin@example.com').first()
        lecturer = User.query.filter_by(email='lecturer@example.com').first()
        
        if admin and lecturer:
            logger.info("Default users verified successfully")
        else:
            logger.error("Failed to verify default users!")

if __name__ == '__main__':
    init_database()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port)
