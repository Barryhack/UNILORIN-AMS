"""Schedule regular database backups."""
import os
import sys
import logging
from datetime import datetime
import schedule
import time
from pathlib import Path

# Add parent directory to path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.utils.backup import DatabaseBackup
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def perform_backup():
    """Perform database backup and cleanup old backups."""
    try:
        # Extract database path from URI
        db_path = Config.SQLALCHEMY_DATABASE_URI.replace('sqlite:///', '')
        backup = DatabaseBackup(db_path)
        
        # Create new backup
        backup_path = backup.create_backup(
            note=f"Scheduled backup at {datetime.now().isoformat()}"
        )
        logger.info(f"Created scheduled backup: {backup_path}")
        
        # Cleanup old backups (keep last 30 days)
        backup.cleanup_old_backups(keep_days=30)
        
    except Exception as e:
        logger.error(f"Scheduled backup failed: {e}")

def main():
    """Main function to schedule backups."""
    logger.info("Starting backup scheduler...")
    
    # Schedule daily backup at 3 AM
    schedule.every().day.at("03:00").do(perform_backup)
    
    # Also perform initial backup when starting
    perform_backup()
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    main()
