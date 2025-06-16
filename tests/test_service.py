"""Tests for the birthday service module."""

import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock
import ldap3
from birthday_bot.service import BirthdayService


class TestBirthdayService:
    """Test cases for BirthdayService class."""

    def test_init(self, birthday_service):
        """Test service initialization."""
        assert birthday_service.ics_url == 'https://example.com/calendar.ics'
        assert birthday_service.webhook_url == 'https://hooks.slack.com/test/webhook'
        assert birthday_service.ldap_server == 'ldaps://ldap.google.com'
        assert birthday_service.search_base == 'ou=Users,dc=test,dc=com'

    def test_download_ics_success(self, birthday_service, mock_requests, mock_ics_content):
        """Test successful ICS download."""
        mock_response = Mock()
        mock_response.content = mock_ics_content
        mock_response.headers = {'Content-Type': 'text/calendar'}
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        result = birthday_service.download_ics()
        
        assert result == mock_ics_content
        mock_requests.get.assert_called_once_with(
            'https://example.com/calendar.ics', 
            timeout=30
        )

    def test_download_ics_wrong_content_type(self, birthday_service, mock_requests):
        """Test ICS download with wrong content type."""
        mock_response = Mock()
        mock_response.headers = {'Content-Type': 'text/html'}
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        with pytest.raises(ValueError, match="not an ICS file"):
            birthday_service.download_ics()

    def test_download_ics_http_error(self, birthday_service, mock_requests):
        """Test ICS download with HTTP error."""
        mock_requests.get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            birthday_service.download_ics()

    @patch('birthday_bot.service.Calendar')
    def test_get_birthday_events_for_date(self, mock_calendar, birthday_service, mock_ics_content):
        """Test getting birthday events for a specific date."""
        # Mock the ICS download
        with patch.object(birthday_service, 'download_ics', return_value=mock_ics_content):
            # Mock the calendar parsing
            mock_event1 = Mock()
            mock_event1.name = "VEVENT"
            mock_event1.get.side_effect = lambda key: {
                'dtstart': Mock(dt=date(2024, 3, 15)),
                'summary': 'John Doe - Birthday'
            }[key]

            mock_event2 = Mock()
            mock_event2.name = "VEVENT"
            mock_event2.get.side_effect = lambda key: {
                'dtstart': Mock(dt=date(2024, 3, 16)),
                'summary': 'Jane Smith - Birthday'
            }[key]

            mock_calendar_instance = Mock()
            mock_calendar_instance.walk.return_value = [mock_event1, mock_event2]
            mock_calendar.from_ical.return_value = mock_calendar_instance

            # Mock LDAP verification
            with patch.object(birthday_service, 'verify_person_in_ldap', return_value=True):
                events = birthday_service.get_birthday_events_for_date(date(2024, 3, 15))

        assert len(events) == 1
        assert events[0]['name'] == 'John Doe'
        assert events[0]['ldap_valid'] is True
        assert events[0]['will_send'] is True
        assert ':birthday: Happy Birthday John Doe! :tada:' in events[0]['message']

    def test_get_birthday_events_no_dash_in_summary(self, birthday_service):
        """Test handling events without dash in summary."""
        with patch.object(birthday_service, 'download_ics', return_value=b""):
            with patch('birthday_bot.service.Calendar') as mock_calendar:
                mock_event = Mock()
                mock_event.name = "VEVENT"
                mock_event.get.side_effect = lambda key: {
                    'dtstart': Mock(dt=date(2024, 3, 15)),
                    'summary': 'Just a regular event'
                }[key]

                mock_calendar_instance = Mock()
                mock_calendar_instance.walk.return_value = [mock_event]
                mock_calendar.from_ical.return_value = mock_calendar_instance

                events = birthday_service.get_birthday_events_for_date(date(2024, 3, 15))

        assert len(events) == 0

    def test_verify_person_in_ldap_found(self, birthday_service, mock_ldap_connection):
        """Test LDAP verification when person is found."""
        mock_ldap_connection.search.return_value = True
        mock_ldap_connection.entries = [Mock()]  # Non-empty list indicates found

        result = birthday_service.verify_person_in_ldap("John Doe")
        
        assert result is True
        mock_ldap_connection.search.assert_called_once()
        call_args = mock_ldap_connection.search.call_args
        assert call_args[1]['search_filter'] == '(uid=john.doe)'

    def test_verify_person_in_ldap_not_found(self, birthday_service, mock_ldap_connection):
        """Test LDAP verification when person is not found."""
        mock_ldap_connection.search.return_value = True
        mock_ldap_connection.entries = []  # Empty list indicates not found

        result = birthday_service.verify_person_in_ldap("John Doe")
        
        assert result is False

    def test_verify_person_in_ldap_error(self, birthday_service):
        """Test LDAP verification with connection error."""
        with patch('birthday_bot.service.Connection', side_effect=Exception("LDAP error")):
            result = birthday_service.verify_person_in_ldap("John Doe")
        
        assert result is False

    @patch.dict(os.environ, {'SLACK_NOTIFICATIONS_ENABLED': 'true'})
    def test_send_slack_message_enabled(self, birthday_service, mock_requests):
        """Test sending Slack message when notifications are enabled."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_requests.post.return_value = mock_response

        birthday_service.send_slack_message("Test message")

        mock_requests.post.assert_called_once_with(
            'https://hooks.slack.com/test/webhook',
            json={'text': 'Test message'},
            timeout=10
        )

    @patch.dict(os.environ, {'SLACK_NOTIFICATIONS_ENABLED': 'false'})
    def test_send_slack_message_disabled(self, birthday_service, mock_requests):
        """Test Slack message is not sent when notifications are disabled."""
        birthday_service.send_slack_message("Test message")

        mock_requests.post.assert_not_called()

    def test_send_slack_message_no_webhook(self, birthday_service, mock_requests):
        """Test handling when no webhook URL is configured."""
        birthday_service.webhook_url = None
        birthday_service.send_slack_message("Test message")

        mock_requests.post.assert_not_called()

    def test_send_birthday_messages(self, birthday_service):
        """Test sending birthday messages for a date."""
        mock_events = [
            {
                'name': 'John Doe',
                'will_send': True,
                'message': ':birthday: Happy Birthday John Doe! :tada:'
            },
            {
                'name': 'Jane Smith',
                'will_send': False,
                'message': None
            }
        ]

        with patch.object(birthday_service, 'get_birthday_events_for_date', return_value=mock_events):
            with patch.object(birthday_service, 'send_slack_message') as mock_send:
                messages = birthday_service.send_birthday_messages(date(2024, 3, 15))

        assert len(messages) == 1
        assert messages[0] == ':birthday: Happy Birthday John Doe! :tada:'
        mock_send.assert_called_once_with(':birthday: Happy Birthday John Doe! :tada:')

    def test_get_service_status(self, birthday_service):
        """Test getting service status."""
        status = birthday_service.get_service_status()

        assert status['ics_url_configured'] is True
        assert status['webhook_url_configured'] is True
        assert status['ldap_server_configured'] is True
        assert status['search_base_configured'] is True

    def test_get_service_status_missing_config(self):
        """Test service status with missing configuration."""
        service = BirthdayService(
            ics_url=None,
            webhook_url=None,
            ldap_server=None,
            search_base=None
        )
        status = service.get_service_status()

        assert status['ics_url_configured'] is False
        assert status['webhook_url_configured'] is False
        assert status['ldap_server_configured'] is False
        assert status['search_base_configured'] is False


import os  # Add this import at the top of the file