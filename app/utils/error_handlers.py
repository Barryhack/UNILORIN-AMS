from flask import render_template, request, current_app, g
from werkzeug.exceptions import HTTPException
import traceback
from datetime import datetime
import json
import os
import time

def log_error(app, error, error_type="Error", include_traceback=True):
    """
    Log error details to both file and console
    """
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Prepare error details
    error_details = {
        'timestamp': datetime.utcnow().isoformat(),
        'error_type': error_type,
        'error_message': str(error),
        'endpoint': request.endpoint,
        'url': request.url,
        'method': request.method,
        'ip_address': request.remote_addr,
        'user_agent': str(request.user_agent)
    }
    
    if include_traceback:
        error_details['traceback'] = traceback.format_exc()
    
    # Log to application logger
    app.logger.error(json.dumps(error_details, indent=2))
    
    # Also log to a separate error log file
    error_log_path = os.path.join('logs', 'error.log')
    with open(error_log_path, 'a') as f:
        f.write(json.dumps(error_details, indent=2) + "\n\n")

def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.before_request
    def before_request():
        g.start_time = time.time()

    @app.errorhandler(400)
    def bad_request_error(error):
        log_error(app, error, "Bad Request", include_traceback=False)
        return render_template('errors/400.html'), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        log_error(app, error, "Unauthorized", include_traceback=False)
        return render_template('errors/401.html'), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        log_error(app, error, "Forbidden", include_traceback=False)
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        log_error(app, error, "Not Found", include_traceback=False)
        return render_template('errors/404.html'), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        log_error(app, error, "Method Not Allowed", include_traceback=False)
        return render_template('errors/405.html'), 405

    @app.errorhandler(429)
    def too_many_requests_error(error):
        log_error(app, error, "Too Many Requests", include_traceback=False)
        return render_template('errors/429.html'), 429

    @app.errorhandler(500)
    def internal_error(error):
        log_error(app, error, "Internal Server Error")
        # Only show detailed error info in development
        context = {
            'error_details': traceback.format_exc() if app.debug else None
        }
        return render_template('errors/500.html', **context), 500

    @app.errorhandler(Exception)
    def unhandled_exception(error):
        if not isinstance(error, HTTPException):
            log_error(app, error, "Unhandled Exception")
            # Only show detailed error info in development
            context = {
                'error_details': traceback.format_exc() if app.debug else None
            }
            return render_template('errors/500.html', **context), 500
        return error

    # After request handler to log response times
    @app.after_request
    def after_request(response):
        if response.status_code >= 400:
            # Log response time for errors
            if hasattr(g, 'start_time'):
                elapsed = time.time() - g.start_time
                current_app.logger.warning(
                    f'Request to {request.path} took {elapsed:.2f}s and returned {response.status_code}'
                )
        return response
