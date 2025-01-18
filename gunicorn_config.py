"""Gunicorn configuration for production."""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = 'logs/access.log'
errorlog = 'logs/error.log'
loglevel = 'info'

# Process naming
proc_name = 'attendance_system'

# SSL Configuration (if using SSL directly in Gunicorn)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Server Mechanics
daemon = False
pidfile = 'attendance_system.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL Configuration
keyfile = None
certfile = None

# Server hooks
def on_starting(server):
    """Log when the server starts."""
    server.log.info("Starting Attendance System server")

def on_reload(server):
    """Log when the server reloads."""
    server.log.info("Reloading Attendance System server")

def on_exit(server):
    """Log when the server exits."""
    server.log.info("Stopping Attendance System server")
