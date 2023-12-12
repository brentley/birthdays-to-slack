import unittest
from unittest.mock import patch
from birthdaybot import download_ics

class TestBirthdayBot(unittest.TestCase):

    @patch('requests.get')
    def test_download_ics_with_valid_url(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'Some ICS content'
        ics_content = download_ics('http://example.com/ics')
        self.assertIsNotNone(ics_content)

    # Additional tests here...

if __name__ == '__main__':
    unittest.main()

