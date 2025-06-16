"""Tests for the Flask application."""

import pytest
import json
import os
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
from birthday_bot import app as app_module


class TestFlaskApp:
    """Test cases for Flask application."""

    def test_app_config(self, app):
        """Test Flask app configuration."""
        assert app.config['TESTING'] is True
        assert app.config['SECRET_KEY'] == 'test-secret-key'

    def test_index_route(self, client):
        """Test the index route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Birthday Bot Dashboard' in response.data

    @patch('birthday_bot.app.birthday_cache', {'2024-03-15': {'events': []}})
    def test_api_birthdays_empty(self, client):
        """Test birthdays API with empty cache."""
        with patch('birthday_bot.app.cache_lock'):
            response = client.get('/api/birthdays')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '2024-03-15' in data

    @patch('birthday_bot.app.birthday_cache')
    def test_api_birthdays_with_events(self, mock_cache, client):
        """Test birthdays API with events."""
        mock_cache.__getitem__.side_effect = lambda k: {
            '2024-03-15': {
                'events': [{
                    'name': 'John Doe',
                    'ldap_valid': True,
                    'message': 'Happy Birthday!'
                }]
            }
        }[k]
        mock_cache.items.return_value = [
            ('2024-03-15', {
                'events': [{
                    'name': 'John Doe',
                    'ldap_valid': True,
                    'message': 'Happy Birthday!'
                }]
            })
        ]

        with patch('birthday_bot.app.cache_lock'):
            response = client.get('/api/birthdays')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert '2024-03-15' in data
        assert data['2024-03-15']['day_of_week'] == 'Friday'

    @patch.dict(os.environ, {'SLACK_NOTIFICATIONS_ENABLED': 'true'})
    def test_api_status_slack_enabled(self, client):
        """Test status API with Slack notifications enabled."""
        with patch('birthday_bot.app.birthday_service', Mock()):
            with patch('birthday_bot.app.birthday_cache', {}):
                response = client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'running'
        assert data['slack_notifications_enabled'] is True
        assert data['service_initialized'] is True

    @patch.dict(os.environ, {'SLACK_NOTIFICATIONS_ENABLED': 'false'})
    def test_api_status_slack_disabled(self, client):
        """Test status API with Slack notifications disabled."""
        with patch('birthday_bot.app.birthday_service', None):
            with patch('birthday_bot.app.birthday_cache', {'key': 'value'}):
                response = client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['slack_notifications_enabled'] is False
        assert data['cache_size'] == 1
        assert data['service_initialized'] is False

    @patch('birthday_bot.app.birthday_service')
    def test_update_birthday_cache_success(self, mock_service):
        """Test successful birthday cache update."""
        mock_service.get_birthday_events_for_date.return_value = [
            {'name': 'John Doe', 'ldap_valid': True}
        ]

        with patch('birthday_bot.app.birthday_cache', {}) as mock_cache:
            with patch('birthday_bot.app.cache_lock'):
                app_module.update_birthday_cache()

        # Should be called 22 times (today + next 21 days)
        assert mock_service.get_birthday_events_for_date.call_count == 22

    def test_update_birthday_cache_no_service(self):
        """Test cache update when service is not initialized."""
        with patch('birthday_bot.app.birthday_service', None):
            with patch('birthday_bot.app.logger') as mock_logger:
                app_module.update_birthday_cache()
        
        mock_logger.error.assert_called_with("Birthday service not initialized")

    def test_update_birthday_cache_exception(self):
        """Test cache update with exception."""
        with patch('birthday_bot.app.birthday_service') as mock_service:
            mock_service.get_birthday_events_for_date.side_effect = Exception("Test error")
            with patch('birthday_bot.app.logger') as mock_logger:
                app_module.update_birthday_cache()
        
        mock_logger.error.assert_called()

    @patch('birthday_bot.app.birthday_service')
    def test_send_daily_birthdays_success(self, mock_service):
        """Test successful daily birthday sending."""
        mock_service.send_birthday_messages.return_value = ["Message sent"]
        
        with patch('birthday_bot.app.update_birthday_cache') as mock_update:
            app_module.send_daily_birthdays()
        
        mock_service.send_birthday_messages.assert_called_once()
        mock_update.assert_called_once()

    def test_send_daily_birthdays_no_service(self):
        """Test daily birthdays when service is not initialized."""
        with patch('birthday_bot.app.birthday_service', None):
            with patch('birthday_bot.app.logger') as mock_logger:
                app_module.send_daily_birthdays()
        
        mock_logger.error.assert_called_with("Birthday service not initialized")

    def test_initialize_service(self):
        """Test service initialization."""
        env_vars = {
            'ICS_URL': 'https://example.com/cal.ics',
            'WEBHOOK_URL': 'https://slack.com/webhook',
            'LDAP_SERVER': 'ldaps://ldap.google.com',
            'SEARCH_BASE': 'ou=Users,dc=test,dc=com'
        }
        
        with patch.dict(os.environ, env_vars):
            app_module.initialize_service()
        
        assert app_module.birthday_service is not None
        assert app_module.birthday_service.ics_url == env_vars['ICS_URL']

    @patch('birthday_bot.app.BackgroundScheduler')
    def test_start_scheduler(self, mock_scheduler_class):
        """Test scheduler startup."""
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler
        
        app_module.start_scheduler()
        
        assert mock_scheduler.add_job.call_count == 2  # Daily check + cache update
        mock_scheduler.start.assert_called_once()

    def test_static_files(self, client):
        """Test that static files are accessible."""
        # Test CSS file
        response = client.get('/static/css/style.css')
        assert response.status_code == 200
        assert response.content_type.startswith('text/css')
        
        # Test JS file
        response = client.get('/static/js/app.js')
        assert response.status_code == 200
        assert response.content_type.startswith(('application/javascript', 'text/javascript'))

    def test_404_error(self, client):
        """Test 404 error handling."""
        response = client.get('/non-existent-route')
        assert response.status_code == 404

