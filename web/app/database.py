"""
Database utilities for the IT-Kurs application.

This module provides improved database session management,
connection handling, and utility functions.
"""

import logging
from contextlib import contextmanager
from typing import Optional, Generator
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)

# Global session factory - will be set by app.py
SessionLocal = None


def set_session_factory(session_factory):
    """
    Set the global session factory.
    
    Args:
        session_factory: SQLAlchemy session factory
    """
    global SessionLocal
    SessionLocal = session_factory


@contextmanager
def get_db_session() -> Generator[Optional[Session], None, None]:
    """
    Context manager for database sessions with proper error handling.
    
    Yields:
        Session: Database session or None if unavailable
    """
    if not SessionLocal:
        logger.error("Database session factory not available")
        yield None
        return
    
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except SQLAlchemyError as e:
        logger.error(f"Database error occurred: {e}")
        session.rollback()
        raise
    except Exception as e:
        logger.error(f"Unexpected error during database operation: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def check_database_health() -> dict:
    """
    Check database connectivity and health.
    
    Returns:
        dict: Health status information
    """
    if not SessionLocal:
        return {
            "status": "unhealthy",
            "message": "Database not configured",
            "available": False
        }
    
    try:
        with get_db_session() as session:
            if session is None:
                return {
                    "status": "unhealthy", 
                    "message": "Cannot create session",
                    "available": False
                }
            
            # Simple connectivity test  
            from sqlalchemy import text
            session.execute(text("SELECT 1"))
            return {
                "status": "healthy",
                "message": "Database connection OK",
                "available": True
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Database error: {str(e)}",
            "available": False
        }


def safe_db_operation(func):
    """
    Decorator for safe database operations with automatic error handling.
    
    Args:
        func: Function that takes a session as first argument
    """
    def wrapper(*args, **kwargs):
        with get_db_session() as session:
            if session is None:
                return {"error": "Database not available"}, 500
            try:
                return func(session, *args, **kwargs)
            except SQLAlchemyError as e:
                logger.error(f"Database operation failed: {e}")
                return {"error": "Database operation failed"}, 500
            except Exception as e:
                logger.error(f"Unexpected error in database operation: {e}")
                return {"error": "An unexpected error occurred"}, 500
    return wrapper
