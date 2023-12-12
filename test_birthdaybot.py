import os
import unittest
from unittest.mock import patch
from birthdaybot import download_ics

class TestBirthdayBot(unittest.TestCase):

    @patch('requests.get')
    def test_download_ics_with_valid_url(self, mock_get):
        # Mocking the response to simulate a valid ICS file
        mock_get.return_value.status_code = 200
        mock_get.return_value.headers = {'Content-Type': 'text/calendar'}
        mock_get.return_value.content = b'BEGIN:VCALENDAR\n...END:VCALENDAR'

        ics_content = download_ics(ics_url)
        self.assertIsNotNone(ics_content)
        self.assertTrue(ics_content.startswith(b'BEGIN:VCALENDAR'))
        self.assertTrue(ics_content.endswith(b'END:VCALENDAR'))

    # Additional tests can be added here for other functions...

if __name__ == '__main__':
    ics_url = os.getenv('ICS_URL')
    if not ics_url:
        raise ValueError("ICS URL not provided. Set the ICS_URL environment variable.")
    unittest.main()

