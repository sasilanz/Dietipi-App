"""
Test configuration and fixtures for the IT-Kurs application.
"""

import pytest
import tempfile
import os
from unittest.mock import patch
from app.app import app
from app.models import Base
from app.config import create_database_engine, create_session_factory


@pytest.fixture
def client():
    """Create a test client for the Flask application."""
    # Create a temporary database for testing
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    
    # Set test configuration
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Use in-memory SQLite for tests
    test_db_url = 'sqlite:///:memory:'
    
    with patch('app.config.Config.DATABASE_URL', test_db_url):
        engine = create_database_engine()
        if engine:
            Base.metadata.create_all(bind=engine)
        
        with app.test_client() as client:
            with app.app_context():
                yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


@pytest.fixture
def mock_email():
    """Mock email sending for tests."""
    with patch('app.email_service.send_email_api') as mock:
        yield mock


@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return [
        {
            "id": "test-course",
            "label": "Test Course",
            "visible": True,
            "status": "active"
        }
    ]


@pytest.fixture
def mock_courses(sample_course_data):
    """Mock course loading for tests."""
    with patch('app.app.load_courses', return_value=sample_course_data):
        yield
