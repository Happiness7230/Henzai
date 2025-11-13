"""Initialize the search engine database and document store with sample data."""
import os
from src.config import Config
from src.storage.database import Database
from src.storage.document_store import DocumentStore

def init_db():
    # Load config
    config = Config.load()
    
    # Ensure data directory exists
    os.makedirs(config.storage_dir, exist_ok=True)
    
    # Initialize database with sample data
    db_path = os.path.join(config.storage_dir, config.index_file)
    db = Database(db_path)
    
    # Add some sample documents
    docs = [
        {
            'url': 'https://example.com/python',
            'title': 'Python Programming Language',
            'content': 'Python is a high-level programming language.',
            'snippet': 'Python is a high-level programming language.'
        },
        {
            'url': 'https://example.com/flask',
            'title': 'Flask Web Framework',
            'content': 'Flask is a lightweight web framework for Python.',
            'snippet': 'Flask is a lightweight web framework for Python.'
        }
    ]
    
    # Initialize document store
    doc_store = DocumentStore(os.path.join(config.storage_dir, 'documents.json'))
    
    # Add documents
    for i, doc in enumerate(docs, 1):
        doc_id = f'doc{i}'
        doc_store.add_document(doc_id, doc)
        # Add to index
        db.insert(doc_id, doc['content'])
    
    print(f"Initialized database at {db_path}")
    print(f"Added {len(docs)} sample documents")

if __name__ == '__main__':
    init_db()