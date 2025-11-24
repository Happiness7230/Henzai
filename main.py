"""
Entry point for the search engine project.
"""

from __future__ import annotations

import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.utils.logger import logger
from src.config.config import Config
from src.crawler.spider import Spider
from src.indexing.indexer import Indexer
from src.processing.tokenizer import Tokenizer
from src.ranking.advanced_ranker import AdvancedRanker
from src.storage.database import Database
from src.web.app import app, set_components


def setup_logging(log_level: str = 'INFO') -> None:
    """Configure logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def ensure_storage_dir(storage_dir: str) -> None:
    """Create storage directory if it doesn't exist."""
    os.makedirs(storage_dir, exist_ok=True)

def main() -> None:
    """Main entry point for the search engine."""
    
    # Validate configuration
    if not Config.validate():
        logger.error("Configuration validation failed!")
        sys.exit(1)
    
    # Setup environment
    setup_logging(Config.LOG_LEVEL)
    ensure_storage_dir(Config.STORAGE_DATA_DIR)
    
    logger.info("="*60)
    logger.info("Initializing Search Engine Components")
    logger.info("="*60)
    
    # Initialize core components
    tokenizer = None
    database = None
    indexer = None
    ranker = None
    spider = None
    search_manager = None

    # Initialize external API clients
    serpapi_client = None
    google_client = None
    
    try:
        tokenizer = Tokenizer()
        logger.info("✓ Tokenizer initialized")
        
        database_path = os.path.join(Config.STORAGE_DATA_DIR, 'index.json')
        database = Database(database_path)
        logger.info("✓ Database initialized")
        
        indexer = Indexer(database, tokenizer)
        logger.info("✓ Indexer initialized")
        
        ranker = AdvancedRanker(indexer)
        logger.info("✓ Ranker initialized")
        
        spider = Spider(
            tokenizer=tokenizer,
            indexer=indexer,
            max_workers=Config.CRAWLER_MAX_WORKERS
        )
        logger.info("✓ Spider initialized")
        
        # Initialize SerpAPI client
        if Config.SERPAPI_ENABLED and Config.SERPAPI_KEY:
            try:
                from src.external.serpapi_client import SerpAPIClient
                serpapi_client = SerpAPIClient(timeout=Config.SERPAPI_TIMEOUT)
                logger.info("✓ SerpAPI client initialized")
            except Exception as e:
                logger.warning(f"SerpAPI initialization failed: {e}")
                serpapi_client = None
        
        # Initialize Google Search client
        if Config.GOOGLE_ENABLED and os.getenv('GOOGLE_API_KEY') and os.getenv('GOOGLE_SEARCH_ENGINE_ID'):
            try:
                from src.external.google_search_client import GoogleSearchClient
                google_client = GoogleSearchClient()
                logger.info("✓ Google Search client initialized")
            except Exception as e:
                logger.warning(f"Google Search initialization failed: {e}")
                google_client = None
        
        # Initialize SearchManager with external clients
        from src.search.search_manager import SearchManager
        search_manager = SearchManager(
            local_ranker=ranker,
            serpapi_client=serpapi_client,
            google_client=google_client,
            mode=Config.SEARCH_MODE  # 'local', 'serpapi', 'google', 'hybrid'
        )
        logger.info("✓ SearchManager initialized in '%s' mode with external clients", Config.SEARCH_MODE)
        
        # Initialize Marketplace client
        marketplace_client = None
        price_alert_manager = None
        try:
            from src.marketplace.marketplace_client import MarketplaceClient
            from src.marketplace.price_alerts import PriceAlertManager
            marketplace_client = MarketplaceClient()
            price_alert_manager = PriceAlertManager()
            logger.info("✓ Marketplace client and price alerts initialized")
        except Exception as e:
            logger.warning(f"Marketplace initialization failed: {e}")
        
        # Initialize Job Search client
        job_search_client = None
        job_alert_manager = None
        try:
            from src.jobs.job_search_client import JobSearchClient, JobAlertManager
            job_search_client = JobSearchClient()
            job_alert_manager = JobAlertManager()
            logger.info("✓ Job search client and alerts initialized")
        except Exception as e:
            logger.warning(f"Job search initialization failed: {e}")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}", exc_info=True)
        sys.exit(1)
    
    # Start auto-flush if enabled
    if Config.INDEXER_AUTO_FLUSH:
        indexer.start_auto_flush(interval=Config.INDEXER_FLUSH_INTERVAL)
        logger.info("✓ Auto-flush enabled")
    
    try:
        # Optional: Crawl sample URLs
        # Uncomment if you want to crawl on startup
        """
        urls = [
            "https://python.org",
            "https://docs.python.org/3/",
        ]
        logger.info(f"Crawling {len(urls)} URLs...")
        spider.crawl(urls)
        logger.info("✓ Crawling complete")
        """
        
        # Ensure index is persisted
        if not Config.INDEXER_AUTO_FLUSH:
            indexer.flush()
        
        from src.web.app import app, set_components
        set_components(
            tokenizer=tokenizer,
            database=database,
            indexer=indexer,
            ranker=ranker,
            spider=spider,
            search_manager_instance=search_manager,
            marketplace_client_instance=marketplace_client,
            job_search_client_instance=job_search_client,
            price_alert_manager_instance=price_alert_manager,
            job_alert_manager_instance=job_alert_manager
        )
        
        # Start the Flask application
        logger.info("="*60)
        logger.info("Starting Web Interface")
        logger.info(f"Server: http://localhost:{Config.WEB_PORT}")
        logger.info("="*60)
        
        app.run(
            host=Config.WEB_HOST,
            port=Config.WEB_PORT,
            debug=Config.WEB_DEBUG
        )
        
    except KeyboardInterrupt:
        logger.info("\nShutdown requested... cleaning up")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if indexer and Config.INDEXER_AUTO_FLUSH:
            indexer.stop_auto_flush()
            indexer.flush()
            logger.info("✓ Index flushed and saved")


if __name__ == '__main__':
    main()
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)