"""Error handlers for the application."""
from flask import render_template, jsonify, request
from werkzeug.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

def init_error_handlers(app):
    """Initialize error handlers for the application."""
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 Bad Request errors."""
        logger.error(f'400 Bad Request: {error}')
        if request.is_json:
            return jsonify(error=str(error)), 400
        return render_template('errors/400.html', error=error), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        """Handle 401 Unauthorized errors."""
        logger.error(f'401 Unauthorized: {error}')
        if request.is_json:
            return jsonify(error='Unauthorized'), 401
        return render_template('errors/401.html', error=error), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        logger.error(f'403 Forbidden: {error}')
        if request.is_json:
            return jsonify(error='Forbidden'), 403
        return render_template('errors/403.html', error=error), 403

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        logger.error(f'404 Not Found: {error}')
        if request.is_json:
            return jsonify(error='Not Found'), 404
        return render_template('errors/404.html', error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server Error errors."""
        logger.error(f'500 Internal Server Error: {error}')
        if request.is_json:
            return jsonify(error='Internal Server Error'), 500
        return render_template('errors/500.html', error=error), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions."""
        logger.error(f'Unhandled Exception: {error}', exc_info=True)
        
        # Handle HTTP exceptions
        if isinstance(error, HTTPException):
            if request.is_json:
                return jsonify(error=str(error)), error.code
            return render_template(f'errors/{error.code}.html', error=error), error.code
        
        # Handle non-HTTP exceptions
        if request.is_json:
            return jsonify(error='Internal Server Error'), 500
        return render_template('errors/500.html', error=error), 500
