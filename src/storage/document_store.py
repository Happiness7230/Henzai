import os
import threading
from flask import json
from datetime import datetime
from typing import Dict, Optional, List


class DocumentStore:
    def __init__(self, filepath: str = 'data/documents.json'):
        """Initialize document store"""
        self.filepath = filepath
        self.documents: Dict[str, Dict] = {}
        self.lock = threading.Lock()
        self._ensure_directory()
        self._load()

    def _ensure_directory(self) -> None:
        """Create directory if it doesn't exist"""
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _load(self) -> None:
        """Load documents from file"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse {self.filepath}, starting fresh")
                self.documents = {}

    def _save(self) -> None:
        """Save documents to file atomically"""
        temp_filepath = self.filepath + '.tmp'
        
        try:
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_filepath, self.filepath)
        except Exception as e:
            print(f"Error saving document store: {e}")
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)

    def add_document(self, doc_id: str, url: str, title: str, 
                     snippet: str, content_length: int) -> None:
        """Add or update a document in the store"""
        with self.lock:
            crawl_count = 1
            if doc_id in self.documents:
                crawl_count = self.documents[doc_id].get('crawl_count', 0) + 1
            
            self.documents[doc_id] = {
                'url': url,
                'title': title,
                'snippet': snippet[:200],
                'content_length': content_length,
                'timestamp': datetime.now().isoformat(),
                'crawl_count': crawl_count
            }
            self._save()

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a document by ID"""
        with self.lock:
            return self.documents.get(doc_id)

    def get_all(self) -> Dict[str, Dict]:
        """Get all documents"""
        with self.lock:
            return self.documents.copy()

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the store"""
        with self.lock:
            if doc_id in self.documents:
                del self.documents[doc_id]
                self._save()
                return True
            return False

    def get_recent_documents(self, limit: int = 10) -> List[Dict]:
        """Get most recently crawled documents"""
        with self.lock:
            docs = [{'id': doc_id, **doc} for doc_id, doc in self.documents.items()]
            docs.sort(key=lambda x: x['timestamp'], reverse=True)
            return docs[:limit]

    def get_statistics(self) -> Dict:
        """Get store statistics"""
        with self.lock:
            total_docs = len(self.documents)
            total_content = sum(doc.get('content_length', 0) for doc in self.documents.values())
            
            return {
                'total_documents': total_docs,
                'total_content_bytes': total_content,
                'average_content_length': total_content // total_docs if total_docs > 0 else 0
            }

    def clear(self) -> None:
        """Clear all documents from the store"""
        with self.lock:
            self.documents = {}
            self._save()