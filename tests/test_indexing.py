"""Unit tests for indexing module."""

import unittest
import os
from src.indexing.indexer import Indexer
from src.processing.tokenizer import Tokenizer
from src.storage.database import Database


class TestIndexing(unittest.TestCase):
      def setUp(self):
            self.tokenizer = Tokenizer()
            self.test_path = "test_index.json"
            # ensure no leftover file
            try:
                  os.remove(self.test_path)
            except OSError:
                  pass
            self.database = Database(self.test_path)
            self.indexer = Indexer(self.tokenizer, self.database)

      def tearDown(self):
            try:
                  os.remove(self.test_path)
            except OSError:
                  pass

      def test_index_document(self):
            tokens = ["hello", "world"]
            self.indexer.index_document("doc1", tokens)
            # explicitly persist changes
            self.indexer.flush()
            index = self.database.load_index()
            self.assertIn("hello", index)
            self.assertEqual(index["hello"], [["doc1", 1]])


if __name__ == "__main__":
      unittest.main()
  