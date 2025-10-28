"""Entry point for the search engine project."""
import logging
import os
import sys
from src.config import Config
from src.crawler.spider import Spider
from src.indexing.indexer import Indexer
from src.processing.tokenizer import Tokenizer
from src.ranking.ranker import Ranker
from src.storage.database import Database
from src.web.app import app

def setup_logging(config: Config) -> None:
    """Configure logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, config.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def ensure_storage_dir(config: Config) -> None:
    """Create storage directory if it doesn't exist."""
    os.makedirs(config.storage_dir, exist_ok=True)

def main():
    # Load and validate configuration
    config = Config.load()
    errors = config.validate()
    if errors:
        print("Configuration errors:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        sys.exit(1)

    # Setup environment
    setup_logging(config)
    ensure_storage_dir(config)
    
    # Initialize components
    tokenizer = Tokenizer()
    database = Database(os.path.join(config.storage_dir, config.index_file))
    indexer = Indexer(tokenizer, database)
    ranker = Ranker(database)
    spider = Spider(
        tokenizer, 
        indexer, 
        max_workers=config.max_workers
    )

    if config.auto_flush:
        indexer.start_auto_flush(interval=config.flush_interval)

    try:
        # Crawl sample URLs (replace with real ones)
        urls = [
            "https://python.org",
            "https://docs.python.org/3/",
            "https://pypi.org"
        ]
        logging.info(f"Starting crawl of {len(urls)} URLs...")
        spider.crawl(urls)
        
        # Ensure index is persisted
        if not config.auto_flush:
            indexer.flush()
        
        # Start web app
        logging.info(f"Starting web interface on port {config.flask_port}")
        app.run(
            host='0.0.0.0', 
            port=config.flask_port,
            debug=config.flask_debug
        )
    finally:
        # Clean shutdown
        if config.auto_flush:
            indexer.stop_auto_flush()
        indexer.flush()

if __name__ == "__main__":
    main()
