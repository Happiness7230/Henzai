"""Concurrency tests for Indexer: verifies locking and background flusher."""

import unittest
import os
import threading
import time

from src.indexing.indexer import Indexer
from src.storage.database import Database


class TestIndexerConcurrency(unittest.TestCase):
    def setUp(self):
        self.test_path = "test_index_concurrency.json"
        try:
            os.remove(self.test_path)
        except OSError:
            pass
        self.db = Database(self.test_path)
        # tokenizer isn't used by Indexer internals for these tests
        self.indexer = Indexer(None, self.db)

    def tearDown(self):
        try:
            # Ensure background flusher stopped
            self.indexer.stop_auto_flush()
        except Exception:
            pass
        try:
            os.remove(self.test_path)
        except OSError:
            pass

    def test_concurrent_indexing_manual_flush(self):
        def worker(doc_id):
            tokens = ["alpha"] * 3 + ["beta"]
            self.indexer.index_document(doc_id, tokens)

        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(f"doc{i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Persist and verify
        self.indexer.flush()
        index = self.db.load_index()
        self.assertIn("alpha", index)
        postings = index["alpha"]
        self.assertEqual(len(postings), 5)
        freqs = sorted([p[1] for p in postings])
        self.assertEqual(freqs, [3, 3, 3, 3, 3])

    def test_background_flusher(self):
        # replace indexer with auto-flush enabled
        self.indexer.stop_auto_flush()
        self.indexer = Indexer(None, self.db)
        self.indexer.start_auto_flush(interval=0.05)

        def worker(doc_id):
            tokens = ["gamma"]
            self.indexer.index_document(doc_id, tokens)

        threads = []
        for i in range(3):
            t = threading.Thread(target=worker, args=(f"bgdoc{i}",))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # wait for background flusher to run at least once
        time.sleep(0.2)
        index = self.db.load_index()
        self.assertIn("gamma", index)
        postings = index["gamma"]
        self.assertEqual(len(postings), 3)


if __name__ == "__main__":
    unittest.main()
