"""Application monitoring utilities."""
import logging
import psutil
import time
from datetime import datetime
import threading
from flask import current_app
import os
import json

logger = logging.getLogger(__name__)

class SystemMonitor:
    """Monitor system resources and application health."""
    
    def __init__(self, app=None, check_interval=60):
        """Initialize system monitor.
        
        Args:
            app: Flask application instance
            check_interval: Interval between checks in seconds
        """
        self.app = app
        self.check_interval = check_interval
        self.monitoring = False
        self.stats = {
            'start_time': datetime.now().isoformat(),
            'cpu_usage': [],
            'memory_usage': [],
            'disk_usage': [],
            'active_connections': 0,
            'requests_per_minute': 0,
            'errors_per_minute': 0
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        
        # Create stats directory if it doesn't exist
        stats_dir = os.path.join(app.instance_path, 'stats')
        os.makedirs(stats_dir, exist_ok=True)
        
        # Start monitoring in a separate thread
        if not self.monitoring:
            thread = threading.Thread(target=self._monitor_loop, daemon=True)
            thread.start()
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        self.monitoring = True
        while self.monitoring:
            try:
                self._collect_stats()
                self._save_stats()
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    def _collect_stats(self):
        """Collect system statistics."""
        try:
            # System stats
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Update stats
            timestamp = datetime.now().isoformat()
            
            self.stats['cpu_usage'].append({
                'timestamp': timestamp,
                'value': cpu_percent
            })
            
            self.stats['memory_usage'].append({
                'timestamp': timestamp,
                'total': memory.total,
                'available': memory.available,
                'percent': memory.percent
            })
            
            self.stats['disk_usage'].append({
                'timestamp': timestamp,
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percent': disk.percent
            })
            
            # Keep only last 24 hours of data
            max_entries = (24 * 60 * 60) // self.check_interval
            for key in ['cpu_usage', 'memory_usage', 'disk_usage']:
                self.stats[key] = self.stats[key][-max_entries:]
            
            # Log warning if resources are running low
            if cpu_percent > 80:
                logger.warning(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 80:
                logger.warning(f"High memory usage: {memory.percent}%")
            if disk.percent > 80:
                logger.warning(f"High disk usage: {disk.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting system stats: {e}")
    
    def _save_stats(self):
        """Save statistics to file."""
        try:
            stats_file = os.path.join(
                self.app.instance_path,
                'stats',
                f"stats_{datetime.now().strftime('%Y%m%d')}.json"
            )
            
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
            
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def get_system_health(self):
        """Get current system health status.
        
        Returns:
            dict: System health information
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'status': 'healthy' if all(x < 80 for x in [cpu_percent, memory.percent, disk.percent]) else 'warning',
                'cpu': {
                    'usage_percent': cpu_percent,
                    'status': 'ok' if cpu_percent < 80 else 'warning'
                },
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'usage_percent': memory.percent,
                    'status': 'ok' if memory.percent < 80 else 'warning'
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'usage_percent': disk.percent,
                    'status': 'ok' if disk.percent < 80 else 'warning'
                },
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def stop(self):
        """Stop monitoring."""
        self.monitoring = False
