"""
Monitoring and health check module for the IT-Kurs application.

This module provides health check endpoints and system monitoring
functionality for production deployment.
"""

import logging
import time
from flask import jsonify
from .database import check_database_health
from .config import Config

logger = logging.getLogger(__name__)


def register_monitoring_endpoints(app):
    """Register monitoring endpoints with the Flask application."""
    
    @app.route("/health")
    def health_check():
        """Basic health check endpoint."""
        return jsonify({
            "status": "healthy",
            "timestamp": time.time(),
            "service": "it-kurs-webapp"
        })
    
    @app.route("/health/ready")
    def readiness_check():
        """Readiness check including database connectivity."""
        db_health = check_database_health()
        
        overall_status = "ready" if db_health["available"] else "not_ready"
        status_code = 200 if db_health["available"] else 503
        
        return jsonify({
            "status": overall_status,
            "timestamp": time.time(),
            "checks": {
                "database": db_health
            }
        }), status_code
    
    @app.route("/health/live")  
    def liveness_check():
        """Liveness check for container orchestration."""
        return jsonify({
            "status": "alive",
            "timestamp": time.time()
        })
    
    @app.route("/metrics")
    def basic_metrics():
        """Basic application metrics."""
        # In production, you might want to integrate with Prometheus
        return jsonify({
            "app_name": "it-kurs-webapp",
            "version": "1.0.0",
            "debug_mode": Config.FLASK_DEBUG,
            "timestamp": time.time()
        })
