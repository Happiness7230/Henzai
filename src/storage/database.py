"""Storage module: handles saving and loading of indexes and metadata."""
"""Indexing module: builds and manages the inverted index.
    
The inverted index maps terms to lists of (document ID, term frequency) pairs.
    This allows efficient querying by term.
    """

import json
import os
import threading
import tempfile


class Database:
    """Simple JSON-backed storage for the inverted index.

    Provides atomic, thread-safe save/load operations using a lock and
    an atomic replace via a temporary file.
    """

    def __init__(self, filename="index.json"):
        self.filename = filename
        self._lock = threading.Lock()

    def save_index(self, index):
        """Atomically write JSON to disk using a temp file and os.replace.

        The method acquires an internal lock to prevent concurrent writers.
        """
        with self._lock:
            dirpath = os.path.dirname(self.filename) or "."
            # Ensure directory exists
            if dirpath and not os.path.exists(dirpath):
                try:
                    os.makedirs(dirpath, exist_ok=True)
                except OSError:
                    pass

            fd, tmp_path = tempfile.mkstemp(dir=dirpath)
            try:
                with os.fdopen(fd, 'w', encoding='utf-8') as f:
                    # Convert to a plain dict for JSON serialization
                    json.dump(index, f, ensure_ascii=False, indent=2)
                # Atomic replace
                os.replace(tmp_path, self.filename)
            finally:
                # If something failed and tmp file remains, try to remove it
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

    def load_index(self):
        """Load index from disk under lock. Returns {} if file missing or unreadable."""
        with self._lock:
            if not os.path.exists(self.filename):
                return {}
            try:
                with open(self.filename, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (OSError, ValueError):
                # If the file is corrupt or unreadable, return empty index.
                return {}
