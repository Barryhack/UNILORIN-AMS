"""Gunicorn configuration file for production deployment."""
import multiprocessing
import os
import sys

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WEB_CONCURRENCY', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'eventlet'  # Use eventlet for WebSocket support
worker_connections = 1000
timeout = 120  # Increased timeout for long-running operations
keepalive = 5

# Process naming
proc_name = 'attendance_system'

# Logging
accesslog = '-'  # Log to stdout
errorlog = '-'   # Log to stderr
loglevel = os.getenv('LOG_LEVEL', 'info')

# SSL is handled by Render
forwarded_allow_ips = '*'
secure_scheme_headers = {
    'X-Forwarded-Proto': 'https',
}

# Prevent worker timeouts
graceful_timeout = 120
timeout = 120

# Startup and shutdown
def on_starting(server):
    """Log server startup."""
    print("Starting Gunicorn server...", file=sys.stderr)

def on_exit(server):
    """Clean up on server exit."""
    print("Shutting down Gunicorn server...", file=sys.stderr)

def post_fork(server, worker):
    """Reset random seed after fork."""
    import random
    random.seed()

def pre_fork(server, worker):
    """Pre-fork operations."""
    pass

def pre_exec(server):
    """Pre-exec operations."""
    pass

def when_ready(server):
    """Actions to run when server is ready."""
    print("Gunicorn server is ready!", file=sys.stderr)
