#!/bin/bash

# Activate virtual environment
source /opt/render/project/src/.venv/bin/activate

# Run Python script to create admin
python3 << END
from app import create_app, db
from app.models.user import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_admin():
    """Create admin user in production"""
    try:
        app = create_app()
        with app.app_context():
            # Check if admin user exists
            admin = User.query.filter_by(id_number='19/52AD001').first()
            
            if admin:
                logger.info("Admin user exists, updating password")
                admin.set_password('Admin@2024')
                db.session.commit()
                logger.info("Admin password updated successfully")
            else:
                logger.info("Creating new admin user")
                admin = User(
                    name='Administrator',
                    email='admin@unilorin.edu.ng',
                    role='admin',
                    id_number='19/52AD001'
                )
                admin.set_password('Admin@2024')
                db.session.add(admin)
                db.session.commit()
                logger.info("Admin user created successfully")
            
            # Verify users in database
            users = User.query.all()
            logger.info(f"Users in database: {[(u.id_number, u.email) for u in users]}")
            
    except Exception as e:
        logger.error(f"Error during admin setup: {str(e)}")
        raise

setup_admin()
END
