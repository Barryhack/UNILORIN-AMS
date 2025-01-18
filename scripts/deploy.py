#!/usr/bin/env python3
"""Deployment script for the Attendance System."""
import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_command(command, cwd=None):
    """Run a shell command and log output."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.info(f"Command succeeded: {command}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {command}")
        logger.error(f"Error output: {e.stderr}")
        return False

def create_directories():
    """Create necessary directories."""
    dirs = ['logs', 'uploads', 'static']
    for dir_name in dirs:
        Path(dir_name).mkdir(exist_ok=True)
        logger.info(f"Created directory: {dir_name}")

def setup_virtual_env():
    """Set up virtual environment and install dependencies."""
    if not run_command("python -m venv venv"):
        return False
    
    # Activate virtual environment and install dependencies
    if sys.platform == "win32":
        if not run_command(r"venv\Scripts\activate && pip install -r requirements.txt"):
            return False
    else:
        if not run_command("source venv/bin/activate && pip install -r requirements.txt"):
            return False
    
    logger.info("Virtual environment setup complete")
    return True

def setup_database():
    """Set up the database."""
    try:
        # Initialize database
        if not run_command("flask db upgrade"):
            return False
        
        logger.info("Database setup complete")
        return True
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        return False

def collect_static():
    """Collect static files."""
    try:
        # Create static directory if it doesn't exist
        static_dir = Path('static')
        static_dir.mkdir(exist_ok=True)

        # Copy static files
        if sys.platform == "win32":
            if not run_command("xcopy /E /I /Y app\\static static"):
                return False
        else:
            if not run_command("cp -r app/static/* static/"):
                return False

        logger.info("Static files collected")
        return True
    except Exception as e:
        logger.error(f"Static file collection failed: {e}")
        return False

def setup_gunicorn():
    """Set up Gunicorn configuration."""
    try:
        # Create logs directory for Gunicorn
        Path('logs').mkdir(exist_ok=True)
        
        # Test Gunicorn configuration
        if not run_command("gunicorn --check-config -c gunicorn_config.py wsgi:app"):
            return False

        logger.info("Gunicorn setup complete")
        return True
    except Exception as e:
        logger.error(f"Gunicorn setup failed: {e}")
        return False

def main():
    """Main deployment function."""
    logger.info("Starting deployment process...")

    # Create necessary directories
    create_directories()

    # Setup virtual environment
    if not setup_virtual_env():
        logger.error("Virtual environment setup failed")
        return False

    # Setup database
    if not setup_database():
        logger.error("Database setup failed")
        return False

    # Collect static files
    if not collect_static():
        logger.error("Static file collection failed")
        return False

    # Setup Gunicorn
    if not setup_gunicorn():
        logger.error("Gunicorn setup failed")
        return False

    logger.info("Deployment completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
