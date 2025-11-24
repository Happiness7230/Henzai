"""Integration test for the search engine."""
import os
import unittest
import pytest
import sys
import tempfile
import shutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))),

from src.config import Config
from src.crawler.spider import Spider
from src.indexing.indexer import Indexer
from src.processing.tokenizer import Tokenizer
from src.ranking.ranker import Ranker
from src.storage.database import Database
from src.storage.document_store import DocumentStore

class TestIntegration:
    """Integration tests for search engine"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def search_engine(self, temp_dir):
        """Create search engine components for testing"""
        # Initialize components with temp directory
        tokenizer = Tokenizer()
        database = Database(filename=os.path.join(temp_dir, 'index.json'))
        indexer = Indexer(database, tokenizer)
        ranker = Ranker(indexer)
        document_store = DocumentStore(filepath=os.path.join(temp_dir, 'documents.json'))
        
        return {
            'tokenizer': tokenizer,
            'database': database,
            'indexer': indexer,
            'ranker': ranker,
            'document_store': document_store
        }
    
    def test_basic_indexing_and_search(self, search_engine):
        """Test basic document indexing and search"""
        indexer = search_engine['indexer']
        ranker = search_engine['ranker']
        tokenizer = search_engine['tokenizer']
        doc_store = search_engine['document_store']
        
        # Add test documents
        doc1 = "Python is a popular programming language"
        doc2 = "Java is used for enterprise applications"
        doc3 = "Python programming is fun and easy"
        
        # Tokenize and index
        tokens1 = tokenizer.tokenize(doc1)
        tokens2 = tokenizer.tokenize(doc2)
        tokens3 = tokenizer.tokenize(doc3)
        
        indexer.add_document("doc1", tokens1)
        indexer.add_document("doc2", tokens2)
        indexer.add_document("doc3", tokens3)
        
        # Add metadata
        doc_store.add_document("doc1", "http://example.com/python1", 
                              "Python Programming", doc1, len(doc1))
        doc_store.add_document("doc2", "http://example.com/java", 
                              "Java Enterprise", doc2, len(doc2))
        doc_store.add_document("doc3", "http://example.com/python2", 
                              "Python Fun", doc3, len(doc3))
        
        # Search for "python"
        results = ranker.rank("python", top_k=10)
        
        # Verify results
        assert len(results) == 2  # doc1 and doc3 contain "python"
        assert results[0][0] in ["doc1", "doc3"]  # Top result is a Python doc
        
        # Verify metadata
        top_doc_id = results[0][0]
        metadata = doc_store.get_document(top_doc_id)
        assert metadata is not None
        assert "python" in metadata['url'].lower() or "python" in metadata['title'].lower()
    
    def test_search_ranking_order(self, search_engine):
        """Test that search results are properly ranked"""
        indexer = search_engine['indexer']
        ranker = search_engine['ranker']
        tokenizer = search_engine['tokenizer']
        
        # Document with "machine learning" mentioned once
        doc1 = "This article discusses various topics including machine learning"
        
        # Document with "machine learning" mentioned multiple times
        doc2 = "Machine learning is transforming AI. Machine learning algorithms are powerful. Machine learning is the future."
        
        # Document without the search term
        doc3 = "This is about something completely different"
        
        tokens1 = tokenizer.tokenize(doc1)
        tokens2 = tokenizer.tokenize(doc2)
        tokens3 = tokenizer.tokenize(doc3)
        
        indexer.add_document("doc1", tokens1)
        indexer.add_document("doc2", tokens2)
        indexer.add_document("doc3", tokens3)
        
        # Search for "machine learning"
        results = ranker.rank("machine learning", top_k=10)
        
        # doc2 should rank higher than doc1 (more mentions)
        assert len(results) == 2  # Only doc1 and doc2 contain the terms
        assert results[0][0] == "doc2"  # doc2 should be first
        assert results[1][0] == "doc1"  # doc1 should be second
        
        # Scores should be different
        assert results[0][1] > results[1][1]
    
    def test_empty_search(self, search_engine):
        """Test search with no matching documents"""
        indexer = search_engine['indexer']
        ranker = search_engine['ranker']
        tokenizer = search_engine['tokenizer']
        
        doc1 = "This is about cats and dogs"
        tokens1 = tokenizer.tokenize(doc1)
        indexer.add_document("doc1", tokens1)
        
        # Search for term not in any document
        results = ranker.rank("quantum physics", top_k=10)
        
        assert len(results) == 0
    
    def test_document_store_operations(self, search_engine):
        """Test document store CRUD operations"""
        doc_store = search_engine['document_store']
        
        # Add document
        doc_store.add_document(
            doc_id="test_doc",
            url="https://example.com/test",
            title="Test Document",
            snippet="This is a test snippet",
            content_length=1000
        )
        
        # Retrieve document
        doc = doc_store.get_document("test_doc")
        assert doc is not None
        assert doc['url'] == "https://example.com/test"
        assert doc['title'] == "Test Document"
        assert doc['content_length'] == 1000
        
        # Update document (re-add with same ID)
        doc_store.add_document(
            doc_id="test_doc",
            url="https://example.com/test-updated",
            title="Updated Test Document",
            snippet="Updated snippet",
            content_length=1500
        )
        
        # Verify update
        updated_doc = doc_store.get_document("test_doc")
        assert updated_doc['url'] == "https://example.com/test-updated"
        assert updated_doc['crawl_count'] == 2  # Incremented
        
        # Delete document
        deleted = doc_store.delete_document("test_doc")
        assert deleted is True
        
        # Verify deletion
        doc = doc_store.get_document("test_doc")
        assert doc is None
    
    def test_persistence(self, search_engine, temp_dir):
        """Test that data persists across instances"""
        indexer = search_engine['indexer']
        tokenizer = search_engine['tokenizer']
        
        # Add document
        doc = "Test document for persistence"
        tokens = tokenizer.tokenize(doc)
        indexer.add_document("persist_doc", tokens)
        indexer.flush()  # Save to disk
        
        # Create new components with same files
        database = Database(filename=os.path.join(temp_dir, 'index.json'))
        new_indexer = Indexer(database, tokenizer)
        new_ranker = Ranker(new_indexer)
        
        # Search should find the document
        results = new_ranker.rank("test document", top_k=10)
        assert len(results) > 0
        assert results[0][0] == "persist_doc"
    
    def test_concurrent_indexing(self, search_engine):
        """Test thread-safe concurrent indexing"""
        import threading
        
        indexer = search_engine['indexer']
        tokenizer = search_engine['tokenizer']
        
        def add_docs(start_id, count):
            for i in range(count):
                doc_id = f"doc_{start_id + i}"
                text = f"This is document number {start_id + i}"
                tokens = tokenizer.tokenize(text)
                indexer.add_document(doc_id, tokens)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=add_docs, args=(i * 10, 10))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Verify all documents were indexed
        indexer.flush()
        ranker = search_engine['ranker']
        results = ranker.rank("document number", top_k=100)
        
        # Should have 50 documents total (5 threads x 10 docs)
        assert len(results) == 50
    
    def test_statistics(self, search_engine):
        """Test statistics gathering"""
        indexer = search_engine['indexer']
        tokenizer = search_engine['tokenizer']
        doc_store = search_engine['document_store']
        
        # Add some documents
        for i in range(5):
            doc = f"Test document number {i} with content"
            tokens = tokenizer.tokenize(doc)
            indexer.add_document(f"doc{i}", tokens)
            doc_store.add_document(
                doc_id=f"doc{i}",
                url=f"https://example.com/doc{i}",
                title=f"Document {i}",
                snippet=doc,
                content_length=len(doc)
            )
        
        # Get statistics
        stats = doc_store.get_statistics()
        
        assert stats['total_documents'] == 5
        assert stats['total_content_bytes'] > 0
        assert stats['average_content_length'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])