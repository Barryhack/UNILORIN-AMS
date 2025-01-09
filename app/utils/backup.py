"""Database backup utilities."""
import os
import shutil
import logging
from datetime import datetime
import sqlite3
import json
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseBackup:
    """Handle database backup operations."""
    
    def __init__(self, db_path, backup_dir='backups'):
        """Initialize backup utility.
        
        Args:
            db_path: Path to the database file
            backup_dir: Directory to store backups
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, note=None):
        """Create a new backup of the database.
        
        Args:
            note: Optional note about the backup
            
        Returns:
            Path to the backup file
        """
        try:
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_name
            
            # Create backup using SQLite's backup API
            with sqlite3.connect(self.db_path) as source, \
                 sqlite3.connect(backup_path) as target:
                source.backup(target)
            
            # Create metadata file
            metadata = {
                'original_db': str(self.db_path),
                'backup_time': datetime.now().isoformat(),
                'note': note
            }
            metadata_path = backup_path.with_suffix('.json')
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Created backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            raise
    
    def restore_backup(self, backup_path):
        """Restore database from backup.
        
        Args:
            backup_path: Path to the backup file to restore
        """
        try:
            backup_path = Path(backup_path)
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_path}")
            
            # Create backup of current database first
            self.create_backup(note="Auto-backup before restore")
            
            # Restore using SQLite's backup API
            with sqlite3.connect(backup_path) as source, \
                 sqlite3.connect(self.db_path) as target:
                source.backup(target)
            
            logger.info(f"Restored backup: {backup_path}")
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
    
    def list_backups(self):
        """List all available backups.
        
        Returns:
            List of dictionaries containing backup information
        """
        backups = []
        for backup_file in self.backup_dir.glob('backup_*.db'):
            metadata_file = backup_file.with_suffix('.json')
            
            backup_info = {
                'file': str(backup_file),
                'size': backup_file.stat().st_size,
                'created': datetime.fromtimestamp(backup_file.stat().st_mtime)
            }
            
            # Add metadata if available
            if metadata_file.exists():
                with open(metadata_file) as f:
                    backup_info.update(json.load(f))
            
            backups.append(backup_info)
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)
    
    def cleanup_old_backups(self, keep_days=30):
        """Remove backups older than specified days.
        
        Args:
            keep_days: Number of days to keep backups
        """
        try:
            cutoff = datetime.now().timestamp() - (keep_days * 86400)
            
            for backup_file in self.backup_dir.glob('backup_*.db'):
                if backup_file.stat().st_mtime < cutoff:
                    # Remove both backup and metadata files
                    backup_file.unlink()
                    metadata_file = backup_file.with_suffix('.json')
                    if metadata_file.exists():
                        metadata_file.unlink()
                    
                    logger.info(f"Removed old backup: {backup_file}")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
            raise
