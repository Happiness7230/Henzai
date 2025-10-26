"""Indexing module: builds and manages the inverted index.
    The inverted index maps terms to lists of (document ID, term frequency) pairs.
    This allows efficient querying by term.

"""

from collections import defaultdict
import threading
import time

class Indexer:
    """Builds and manages an in-memory inverted index.

    This implementation is thread-safe for concurrent updates and provides a
    `flush()` method to persist the current in-memory index to the provided
    Database instance. `index_document` updates only the in-memory structure
    and does not perform I/O (to avoid concurrent file writes).
    """

    def __init__(self, tokenizer, database):
        self.tokenizer = tokenizer
        self.database = database
        # Inverted index: term -> list of [doc_id, freq]
        self.index = defaultdict(list)
        self._lock = threading.Lock()
        # Background flusher settings
        self._auto_flush = False
        self._flush_interval = None
        self._stop_event = threading.Event()
        self._flusher_thread = None

    def index_document(self, doc_id, tokens):
        """Thread-safe update of the in-memory index. Does NOT persist to disk.

        Args:
            doc_id (str): document identifier
            tokens (iterable): token sequence for the document
        """
        term_freq = defaultdict(int)
        for token in tokens:
            term_freq[token] += 1

        with self._lock:
            for term, freq in term_freq.items():
                postings = self.index[term]
                # Try to merge with existing posting for the same doc_id
                for p in postings:
                    if p[0] == doc_id:
                        p[1] += freq
                        break
                else:
                    # store as list so JSON serialization keeps it as array
                    postings.append([doc_id, freq])

    def flush(self):
        """Persist the current in-memory index to storage (thread-safe).

        This method serializes the index to a plain dict and delegates to the
        Database instance to perform an atomic save.
        """
        with self._lock:
            # convert defaultdict to regular dict for serialization
            serializable = {k: v for k, v in self.index.items()}
            self.database.save_index(serializable)

    # --- background flusher API -------------------------------------------------
    def start_auto_flush(self, interval=5.0):
        """Start a background thread that calls `flush()` every `interval` seconds.

        If a flusher is already running this is a no-op.
        """
        if self._flusher_thread and self._flusher_thread.is_alive():
            return
        self._auto_flush = True
        self._flush_interval = float(interval)
        self._stop_event.clear()
        self._flusher_thread = threading.Thread(target=self._auto_flush_loop, daemon=True)
        self._flusher_thread.start()

    def _auto_flush_loop(self):
        # Use wait so we can exit promptly when stop_event is set.
        while not self._stop_event.wait(self._flush_interval):
            try:
                self.flush()
            except Exception:
                # Swallow exceptions in background flusher to avoid thread death.
                pass

    def stop_auto_flush(self, timeout=1.0):
        """Stop the background flusher (if running) and wait up to `timeout` seconds."""
        if not self._flusher_thread:
            return
        self._stop_event.set()
        self._flusher_thread.join(timeout)
        self._flusher_thread = None
        self._auto_flush = False
        self._flush_interval = None
