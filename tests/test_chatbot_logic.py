import unittest
import sys
import os

# Add the src directory to the Python path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.model.nlp_utils import find_pictogram

class TestChatbotLogic(unittest.TestCase):

    def setUp(self):
        """Set up dummy data for tests."""
        self.dummy_pictograms = [
            {
                "_id": 1,
                "keywords": [{"keyword": "hola"}]
            },
            {
                "_id": 2,
                "keywords": [{"keyword": "adiós"}]
            },
            {
                "_id": 3,
                "keywords": [{"keyword": "gato"}]
            }
        ]

    def test_find_pictogram(self):
        """Test the find_pictogram function."""
        self.assertIsNotNone(find_pictogram("gato", self.dummy_pictograms))
        self.assertIsNone(find_pictogram("perro", self.dummy_pictograms))
        # Test case sensitivity (should be handled by the caller)
        self.assertIsNotNone(find_pictogram("Gato", self.dummy_pictograms))


if __name__ == '__main__':
    unittest.main()
