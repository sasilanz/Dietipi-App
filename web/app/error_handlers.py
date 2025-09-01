"""
Error handling module for the IT-Kurs application.

This module provides comprehensive error handling including
custom error pages, logging, and graceful degradation.
"""

import logging
from flask import render_template, request, jsonify
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register error handlers with the Flask application."""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors."""
        logger.info(f"404 error: {request.url}")
        if request.content_type == 'application/json':
            return jsonify({"error": "Resource not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        logger.error(f"500 error: {error}", exc_info=True)
        if request.content_type == 'application/json':
            return jsonify({"error": "Internal server error"}), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors."""
        logger.warning(f"403 error - Access denied to {request.url} from {request.remote_addr}")
        if request.content_type == 'application/json':
            return jsonify({"error": "Access forbidden"}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        """Handle database-related errors."""
        logger.error(f"Database error: {error}", exc_info=True)
        if request.content_type == 'application/json':
            return jsonify({"error": "Database error occurred"}), 500
        return render_template("errors/database.html"), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {error}", exc_info=True)
        if request.content_type == 'application/json':
            return jsonify({"error": "An unexpected error occurred"}), 500
        return render_template("errors/500.html"), 500
