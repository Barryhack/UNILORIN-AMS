"""Production deployment script."""
import os
import sys
import subprocess
import logging
from pathlib import Path
import shutil
import argparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/deploy.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class Deployer:
    """Handle production deployment tasks."""
    
    def __init__(self, app_dir):
        """Initialize deployer.
        
        Args:
            app_dir: Application directory path
        """
        self.app_dir = Path(app_dir)
        self.venv_dir = self.app_dir / 'venv'
    
    def setup_directories(self):
        """Create necessary directories."""
        dirs = [
            self.app_dir / 'logs',
            self.app_dir / 'instance',
            self.app_dir / 'backups',
            self.app_dir / 'instance/stats'
        ]
        
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
    
    def setup_virtual_environment(self):
        """Set up Python virtual environment."""
        if not self.venv_dir.exists():
            logger.info("Creating virtual environment...")
            subprocess.run([sys.executable, '-m', 'venv', str(self.venv_dir)], check=True)
        
        # Upgrade pip
        pip_cmd = str(self.venv_dir / 'Scripts' / 'pip.exe')
        subprocess.run([pip_cmd, 'install', '--upgrade', 'pip'], check=True)
        
        # Install requirements
        requirements_file = self.app_dir / 'requirements.txt'
        subprocess.run([pip_cmd, 'install', '-r', str(requirements_file)], check=True)
        logger.info("Installed Python dependencies")
    
    def setup_database(self):
        """Set up the database."""
        from app import create_app
        from app.utils.db_migration import migrate_to_postgres
        
        app = create_app()
        with app.app_context():
            if os.getenv('USE_POSTGRES'):
                logger.info("Migrating to PostgreSQL...")
                migrate_to_postgres(app)
            else:
                logger.info("Using SQLite database")
                from app.extensions import db
                db.create_all()
    
    def setup_ssl(self):
        """Set up SSL certificates using Let's Encrypt."""
        domain = os.getenv('DOMAIN_NAME')
        email = os.getenv('SSL_EMAIL')
        
        if domain and email:
            logger.info("Setting up SSL certificates...")
            try:
                subprocess.run([
                    'certbot', 'certonly',
                    '--standalone',
                    '--agree-tos',
                    '--non-interactive',
                    '--email', email,
                    '-d', domain
                ], check=True)
                logger.info("SSL certificates installed successfully")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install SSL certificates: {e}")
                raise
    
    def setup_nginx(self):
        """Set up Nginx configuration."""
        nginx_conf = self.app_dir / 'nginx.conf'
        nginx_target = Path('/etc/nginx/nginx.conf')
        
        if nginx_conf.exists():
            # Backup existing config
            if nginx_target.exists():
                backup_path = nginx_target.with_suffix('.backup')
                shutil.copy2(nginx_target, backup_path)
                logger.info(f"Backed up existing Nginx config to {backup_path}")
            
            # Copy new config
            shutil.copy2(nginx_conf, nginx_target)
            logger.info("Installed Nginx configuration")
            
            # Test configuration
            try:
                subprocess.run(['nginx', '-t'], check=True)
                subprocess.run(['systemctl', 'restart', 'nginx'], check=True)
                logger.info("Nginx configuration tested and service restarted")
            except subprocess.CalledProcessError as e:
                logger.error(f"Nginx configuration test failed: {e}")
                if backup_path.exists():
                    shutil.copy2(backup_path, nginx_target)
                    logger.info("Restored previous Nginx configuration")
                raise
    
    def setup_monitoring(self):
        """Set up system monitoring."""
        from app.utils.monitoring import SystemMonitor
        from app import create_app
        
        app = create_app()
        monitor = SystemMonitor(app)
        monitor.init_app(app)
        logger.info("System monitoring initialized")
    
    def deploy(self):
        """Run full deployment process."""
        try:
            logger.info("Starting deployment process...")
            
            self.setup_directories()
            self.setup_virtual_environment()
            self.setup_database()
            
            if os.getenv('SETUP_SSL', 'false').lower() == 'true':
                self.setup_ssl()
            
            if os.getenv('SETUP_NGINX', 'false').lower() == 'true':
                self.setup_nginx()
            
            self.setup_monitoring()
            
            logger.info("Deployment completed successfully")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            raise

def main():
    """Main deployment function."""
    parser = argparse.ArgumentParser(description='Deploy Attendance System')
    parser.add_argument('--app-dir', type=str, help='Application directory path')
    args = parser.parse_args()
    
    app_dir = args.app_dir or os.getcwd()
    deployer = Deployer(app_dir)
    deployer.deploy()

if __name__ == '__main__':
    main()
