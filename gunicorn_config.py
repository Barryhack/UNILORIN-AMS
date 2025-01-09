"""Gunicorn configuration file for production deployment."""
import multiprocessing
import os

# Server socket
bind = os.getenv('GUNICORN_BIND', '0.0.0.0:8000')
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'eventlet'  # Use eventlet for WebSocket support
worker_connections = 1000
timeout = 30
keepalive = 2

# Process naming
proc_name = 'attendance_system'

# Logging
accesslog = 'logs/gunicorn_access.log'
errorlog = 'logs/gunicorn_error.log'
loglevel = 'info'

# SSL (uncomment and configure in production)
# keyfile = 'path/to/keyfile'
# certfile = 'path/to/certfile'
# ssl_version = 'TLS'
# cert_reqs = 'CERT_REQUIRED'
# ca_certs = 'path/to/ca_certs'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
daemon = False
pidfile = 'attendance_system.pid'
user = None
group = None
umask = 0
tmp_upload_dir = None

# Server hooks
def on_starting(server):
    """Log server startup."""
    server.log.info("Starting Attendance System server")

def on_exit(server):
    """Clean up on server exit."""
    server.log.info("Shutting down Attendance System server")

def post_fork(server, worker):
    """Reset random seed after fork."""
    import random
    random.seed()

def pre_fork(server, worker):
    """Pre-fork operations."""
    pass

def pre_exec(server):
    """Pre-exec operations."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """Actions to run when server is ready."""
    server.log.info("Server is ready. Spawning workers")
