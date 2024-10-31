import unittest
from unittest.mock import patch, MagicMock
from datetime import timedelta
import json
from dotenv import load_dotenv

from YouTube.transcribe_summarize import get_outline



class TestGetOutline(unittest.TestCase):

    @patch('YouTube.transcribe_summarize.OpenAI')
    @patch('YouTube.transcribe_summarize.os.getenv')
    def test_get_outline_with_valid_description(self, mock_getenv, mock_openai):
        mock_getenv.return_value = 'fake_api_key'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "timestamps": [
                {"timestamp": "00:01", "topic": "Introduction"},
                {"timestamp": "00:05", "topic": "Main Content"},
                {"timestamp": "00:10", "topic": "Conclusion"}
            ]
        })
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        description = "This is a test description with an outline."
        expected_output = [
            {"timestamp": timedelta(minutes=0, seconds=1), "topic": "Introduction"},
            {"timestamp": timedelta(minutes=0, seconds=5), "topic": "Main Content"},
            {"timestamp": timedelta(minutes=0, seconds=10), "topic": "Conclusion"}
        ]

        result = get_outline(description)
        self.assertEqual(result, expected_output)

    @patch('YouTube.transcribe_summarize.OpenAI')
    @patch('YouTube.transcribe_summarize.os.getenv')
    def test_get_outline_with_no_outline(self, mock_getenv, mock_openai):
        mock_getenv.return_value = 'fake_api_key'
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({})
        mock_openai.return_value.chat.completions.create.return_value = mock_response

        description = "This is a test description without an outline."
        expected_output = None

        result = get_outline(description)
        self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()