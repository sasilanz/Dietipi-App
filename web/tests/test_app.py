"""
Basic tests for the IT-Kurs application routes and functionality.
"""

import pytest
from unittest.mock import patch


def test_index_page(client, mock_courses):
    """Test that the index page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Willkommen' in response.data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    
    json_data = response.get_json()
    assert json_data['status'] == 'healthy'
    assert 'timestamp' in json_data


def test_readiness_check(client):
    """Test the readiness check endpoint."""
    response = client.get('/health/ready')
    # May be 200 or 503 depending on database availability
    assert response.status_code in [200, 503]
    
    json_data = response.get_json()
    assert 'status' in json_data
    assert 'checks' in json_data


def test_kursliste_page(client, mock_courses):
    """Test the course list page."""
    response = client.get('/kursliste')
    assert response.status_code == 200


def test_kursleitung_page(client):
    """Test the course leadership page."""
    response = client.get('/kursleitung')
    assert response.status_code == 200


def test_payment_page(client):
    """Test the payment information page."""
    response = client.get('/zahlung')
    assert response.status_code == 200


def test_registration_form_get(client, mock_courses):
    """Test that the registration form loads."""
    response = client.get('/anmeldung')
    assert response.status_code == 200
    assert b'anmeldung' in response.data.lower() or b'registr' in response.data.lower()


def test_registration_form_post_valid(client, mock_courses, mock_email):
    """Test valid registration form submission."""
    form_data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': 'test@example.com',
        'phone': '0123456789',
        'course_id': 'test-course'
    }
    
    response = client.post('/anmeldung', data=form_data, follow_redirects=True)
    assert response.status_code == 200
    # Should redirect to success page
    assert b'success' in response.data.lower() or b'erfolgreich' in response.data.lower()


def test_404_error(client):
    """Test that 404 errors are handled properly."""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404


def test_admin_access_without_token(client):
    """Test that admin pages require authentication."""
    response = client.get('/_admin')
    assert response.status_code == 403


def test_admin_access_with_token(client):
    """Test admin access with valid token."""
    with patch('app.config.Config.ADMIN_TOKEN', 'test-token'):
        response = client.get('/_admin?admin=test-token')
        assert response.status_code == 200


def test_participant_count_endpoint(client):
    """Test participant count endpoint."""
    response = client.get('/teilnehmende/count')
    assert response.status_code in [200, 500]  # 500 if DB not available
    
    if response.status_code == 200:
        json_data = response.get_json()
        assert 'participants' in json_data


def test_security_headers(client):
    """Test that security headers are applied."""
    response = client.get('/')
    
    # Check for security headers
    assert 'X-Content-Type-Options' in response.headers
    assert 'X-Frame-Options' in response.headers
    assert 'Content-Security-Policy' in response.headers


def test_rate_limiting():
    """Test rate limiting functionality."""
    from app.security import RateLimiter
    
    limiter = RateLimiter()
    
    # Test normal usage
    for i in range(5):
        assert limiter.is_allowed('test-key', limit=5, window=60) is True
    
    # Test limit exceeded
    assert limiter.is_allowed('test-key', limit=5, window=60) is False


def test_input_sanitization():
    """Test input sanitization functionality."""
    from app.security import sanitize_input
    
    # Test normal input
    assert sanitize_input('Hello World') == 'Hello World'
    
    # Test HTML escaping
    assert sanitize_input('<script>alert("xss")</script>') != '<script>alert("xss")</script>'
    
    # Test empty input
    assert sanitize_input('') == ''
    assert sanitize_input(None) == ''


def test_email_validation():
    """Test email validation functionality."""
    from app.security import validate_email
    
    # Valid emails
    assert validate_email('test@example.com') is True
    assert validate_email('user.name@domain.co.uk') is True
    
    # Invalid emails
    assert validate_email('invalid-email') is False
    assert validate_email('') is False
    assert validate_email(None) is False
