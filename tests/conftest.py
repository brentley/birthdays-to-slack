"""Pytest configuration and shared fixtures."""

import os
import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch, MagicMock
from birthday_bot.service import BirthdayService
from birthday_bot.app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing."""
    flask_app.config['TESTING'] = True
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    return flask_app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def birthday_service():
    """Create a BirthdayService instance for testing."""
    return BirthdayService(
        ics_url='https://example.com/calendar.ics',
        webhook_url='https://hooks.slack.com/test/webhook',
        ldap_server='ldaps://ldap.google.com',
        search_base='ou=Users,dc=test,dc=com'
    )


@pytest.fixture
def mock_ics_content():
    """Sample ICS content for testing."""
    return b"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Test//Test Calendar//EN
BEGIN:VEVENT
DTSTART:20240315
SUMMARY:John Doe - Birthday
UID:1234567890@test.com
END:VEVENT
BEGIN:VEVENT
DTSTART:20240316
SUMMARY:Jane Smith - Birthday
UID:0987654321@test.com
END:VEVENT
END:VCALENDAR"""


@pytest.fixture
def mock_ldap_connection():
    """Mock LDAP connection for testing."""
    with patch('birthday_bot.service.Connection') as mock_conn:
        mock_instance = MagicMock()
        mock_conn.return_value.__enter__.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_requests():
    """Mock requests for HTTP calls."""
    with patch('birthday_bot.service.requests') as mock_req:
        yield mock_req


@pytest.fixture
def mock_scheduler():
    """Mock APScheduler for testing."""
    with patch('birthday_bot.app.BackgroundScheduler') as mock_sched:
        yield mock_sched


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables for each test."""
    original_env = os.environ.copy()
    yield
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def enable_slack_notifications():
    """Enable Slack notifications for testing."""
    os.environ['SLACK_NOTIFICATIONS_ENABLED'] = 'true'
    yield
    os.environ.pop('SLACK_NOTIFICATIONS_ENABLED', None)


@pytest.fixture
def disable_slack_notifications():
    """Disable Slack notifications for testing."""
    os.environ['SLACK_NOTIFICATIONS_ENABLED'] = 'false'
    yield
    os.environ.pop('SLACK_NOTIFICATIONS_ENABLED', None)