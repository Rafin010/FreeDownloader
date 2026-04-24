import sys
import unittest
import json
import logging

logging.basicConfig(level=logging.INFO)

# Add directory to path
sys.path.insert(0, "e:\\_free downloader Projext\\yt_d")
import app as backend_app

class TestYouTubeAlternative(unittest.TestCase):
    def setUp(self):
        backend_app.app.testing = True
        self.client = backend_app.app.test_client()

    def test_trending(self):
        print("Testing /api/trending...")
        response = self.client.get('/api/trending')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)
        if len(data['results']) > 0:
            print("Trending returned {} items".format(len(data['results'])))
        else:
            print("Expected trending items, got 0. This may happen if Invidious is rate limited.")

    def test_search(self):
        print("Testing /api/search?q=test...")
        response = self.client.get('/api/search?q=test')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('results', data)
        self.assertIsInstance(data['results'], list)
        if len(data['results']) > 0:
            print("Search returned {} items".format(len(data['results'])))
        else:
            print("Expected search items, got 0.")

if __name__ == '__main__':
    unittest.main()
