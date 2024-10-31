import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import json

from transcribe_summarize import get_outline

class TestGetOutline(unittest.TestCase):

    def test_get_outline_valid_description(self):
        # Mock environment variable
        mock_input = json.dumps({
            "timestamps": [
                {"timestamp": "00:01", "topic": "Introduction"},
                {"timestamp": "05:00", "topic": "Main Content"},
                {"timestamp": "10:00", "topic": "Conclusion"}
            ]
        })
        description = "This is a test description with an outline."
        expected_result = {
             "timestamps": [
                {"timestamp": "00:01", "topic": "Introduction"},
                {"timestamp": "05:00", "topic": "Main Content"},
                {"timestamp": "10:00", "topic": "Conclusion"}
             ]
        }

        result = get_outline(description + "\n" + mock_input)
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()