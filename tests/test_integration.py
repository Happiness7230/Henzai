"""Integration test for the search engine."""
import os
import unittest
from src.config import Config
from src.crawler.spider import Spider
from src.indexing.indexer import Indexer
from src.processing.tokenizer import Tokenizer
from src.ranking.ranker import Ranker
from src.storage.database import Database

class TestSearchIntegration(unittest.TestCase):
    def setUp(self):
        # Load config
        self.config = Config.load()
        self.config.index_file = "test_integration_index.json"
        
        # Initialize components
        self.tokenizer = Tokenizer()
        self.database = Database(self.config.index_file)
        self.indexer = Indexer(self.tokenizer, self.database)
        self.ranker = Ranker(self.database)
        self.spider = Spider(self.tokenizer, self.indexer, max_workers=2)
        
        # Enable auto-flush
        self.indexer.start_auto_flush(interval=1)

    def tearDown(self):
        self.indexer.stop_auto_flush()
        try:
            os.remove(self.config.index_file)
        except OSError:
            pass

    def test_search_flow(self):
        # Index some test content
        test_docs = {
            "doc1": "Python is a great programming language",
            "doc2": "Programming in Python is fun and productive",
            "doc3": "The python snake is a reptile"
        }
        
        for doc_id, content in test_docs.items():
            tokens = self.tokenizer.tokenize(content)
            self.indexer.index_document(doc_id, tokens)
        
        # Force flush
        self.indexer.flush()
        
        # Test search
        query = "python programming"
        query_tokens = self.tokenizer.tokenize(query)
        index = self.database.load_index()
        results = self.ranker.rank(query_tokens, index)
        
        # Verify results
        self.assertTrue(len(results) > 0, "Should find results")
        # doc1 and doc2 should rank higher than doc3 for "python programming"
        doc_ids = [doc_id for doc_id, score in results]
        self.assertTrue(
            doc_ids.index("doc1") < doc_ids.index("doc3") and 
            doc_ids.index("doc2") < doc_ids.index("doc3"),
            "Programming-related documents should rank higher"
        )

if __name__ == '__main__':
    unittest.main()