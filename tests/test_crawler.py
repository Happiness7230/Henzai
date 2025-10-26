"""Unit tests for crawler module."""

import unittest
from unittest.mock import patch
from src.crawler.spider import Spider
from src.processing.tokenizer import Tokenizer
from src.indexing.indexer import Indexer
from src.storage.database import Database

class TestCrawler(unittest.TestCase):
    def setUp(self):
        self.tokenizer = Tokenizer()
        self.database = Database("test_index.json")
        self.indexer = Indexer(self.tokenizer, self.database)
        self.spider = Spider(self.tokenizer, self.indexer)

    @patch('requests.get')
    def test_crawl(self, mock_get):
        mock_get.return_value.text = "<html><body>Test content</body></html>"
        self.spider.crawl(["http://example.com"])
        index = self.database.load_index()
        self.assertIn("test", index)

if __name__ == "__main__":
    unittest.main()
