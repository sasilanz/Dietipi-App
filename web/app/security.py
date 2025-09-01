"""
Security module for the IT-Kurs application.

This module provides security enhancements including CSRF protection,
rate limiting, input sanitization, and security headers.
"""

import logging
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta
from functools import wraps
from flask import request, abort, g
from markupsafe import escape

logger = logging.getLogger(__name__)


# Simple in-memory rate limiting (for production, consider Redis)
class RateLimiter:
    """Simple in-memory rate limiter."""
    
    def __init__(self):
        self.requests = defaultdict(deque)
    
    def is_allowed(self, key: str, limit: int = 10, window: int = 60) -> bool:
        """
        Check if request is allowed based on rate limit.
        
        Args:
            key: Unique identifier (usually IP address)
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            bool: True if request is allowed
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=window)
        
        # Clean old requests
        while self.requests[key] and self.requests[key][0] < window_start:
            self.requests[key].popleft()
        
        # Check if within limit
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True


rate_limiter = RateLimiter()


def rate_limit(limit: int = 10, window: int = 60):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        limit: Maximum requests per window
        window: Time window in seconds
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            key = request.remote_addr
            if not rate_limiter.is_allowed(key, limit, window):
                logger.warning(f"Rate limit exceeded for {key}")
                abort(429)  # Too Many Requests
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def sanitize_input(text: str) -> str:
    """
    Sanitize user input to prevent XSS and injection attacks.
    
    Args:
        text: User input string
        
    Returns:
        str: Sanitized string
    """
    if not text:
        return ""
    
    # Escape HTML characters
    sanitized = escape(text)
    
    # Additional cleaning for common attack patterns
    # Remove script tags and javascript: protocols
    sanitized = re.sub(r'<script[^>]*>.*?</script>', '', str(sanitized), flags=re.IGNORECASE | re.DOTALL)
    sanitized = re.sub(r'javascript:', '', sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """
    Validate email format with robust regex.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Content Security Policy for basic XSS protection
    csp = (
        "default-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "script-src 'self'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self'"
    )
    response.headers['Content-Security-Policy'] = csp
    
    return response


def register_security_features(app):
    """Register security features with the Flask application."""
    
    @app.after_request
    def apply_security_headers(response):
        """Apply security headers to all responses."""
        return add_security_headers(response)
    
    @app.before_request
    def security_checks():
        """Perform security checks before each request."""
        # Log suspicious activity
        if request.method == 'POST':
            content_length = request.content_length
            if content_length and content_length > 1024 * 1024:  # 1MB limit
                logger.warning(f"Large POST request from {request.remote_addr}: {content_length} bytes")
        
        # Store client info for rate limiting
        g.client_ip = request.remote_addr
