"""
Entry point for the search engine project.
This file handles component initialization and injection before the
web server (e.g., Gunicorn) loads the 'app' variable.
"""

from __future__ import annotations

import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Import all necessary classes and the web app components ---
from src.utils.logger import logger
from src.config.config import Config
from src.crawler.spider import Spider
from src.indexing.indexer import Indexer
from src.processing.tokenizer import Tokenizer
from src.ranking.advanced_ranker import AdvancedRanker
from src.storage.database import Database
from celery_app import bootstrap_crawl_task
from src.web.app import app, set_components, initialize_components 

# --- New: Define the Massive Crawl Bootstrap List ---
# This list targets authoritative, deep documentation sites to achieve 
# a high volume of specialized, high-quality documents (targeting 10,000+).
BOOTSTRAP_URLS = [
    # 1. Programming Languages (Deep Authority)
    "https://docs.oracle.com/en/java/javase/index.html",    # Java Docs (Depth 3+)
    "https://www.cppreference.com/",                         # C++ Reference Wiki (Depth 4+)
    "https://doc.rust-lang.org/book/",                      # Rust Book (Depth 3+)
    
    # 2. Web Development (Front-end and Back-end)
    "https://react.dev/reference/react",                    # React Official Docs (Depth 3)
    "https://docs.djangoproject.com/en/stable/",            # Django Backend Framework (Depth 3)
    
    # 3. Mobile Development
    "https://developer.android.com/docs",                   # Android Official Docs (Depth 2)
    
    # 4. Cloud Computing and Services
    "https://docs.microsoft.com/en-us/azure/",              # Azure Documentation (Depth 2 - Broad)
    "https://docs.aws.amazon.com/",                         # AWS Documentation (Depth 2 - Broad)
    "https://kubernetes.io/docs/home/",                     # Kubernetes Docs (Depth 3)

    # 5. Database Management
    "https://www.postgresql.org/docs/",                     # PostgreSQL Docs (Depth 4)

    # 6. Cybersecurity and Information Security
    "https://owasp.org/www-project-top-ten/",               # OWASP Top Ten (Depth 3)
    
    # 7. AI and Machine Learning
    "https://scikit-learn.org/stable/documentation.html",   # Scikit-learn (Depth 4)
    "https://pytorch.org/docs/stable/index.html",           # PyTorch Docs (Depth 3)
    "https://pandas.pydata.org/docs/",                      # Pandas Data Analysis (Depth 3)
    
    # 8. Software Development Methodologies & Version Control
    "https://www.atlassian.com/agile/tutorials",            # Agile/Scrum Tutorials (Depth 3)
    "https://git-scm.com/docs",                             # Git Documentation (Depth 3)
    
    # 9. Technical Writing (Meta-Documentation)
    "https://diataxis.fr/",                                 # Technical Documentation Framework (Depth 3)
    
    # 10. DevOps Tools
    "https://docs.docker.com/",                             # Docker Documentation (Depth 3)
    "https://developer.hashicorp.com/terraform/docs",       # Terraform Docs (Depth 3)

    # 11. Specialized Engineering Blogs (Deep content)
    "https://martinfowler.com/",                            # Software Architecture Essays (Depth 5 - Max depth for content)
]
# --- End Bootstrap List ---


# --- Setup Helpers (same as previous version) ---

def setup_logging(log_level: str = 'INFO') -> None:
    """Configure logging based on settings."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def ensure_storage_dir(storage_dir: str) -> None:
    """Create storage directory if it doesn't exist."""
    os.makedirs(storage_dir, exist_ok=True)


def run_development_server(indexer_instance: Indexer) -> None:
    """
    Starts the Flask application in development mode with cleanup hooks.
    """
    # Start auto-flush if enabled
    if Config.INDEXER_AUTO_FLUSH:
        indexer_instance.start_auto_flush(interval=Config.INDEXER_FLUSH_INTERVAL)
        logger.info("✓ Auto-flush enabled")
    
    try:
        # Ensure index is persisted before starting (if not auto-flushing)
        if not Config.INDEXER_AUTO_FLUSH:
            indexer_instance.flush()
        
        logger.info("="*60)
        logger.info("Starting Web Interface (Development Mode)")
        logger.info(f"Server: http://{Config.WEB_HOST}:{Config.WEB_PORT}")
        logger.info("="*60)
        
        app.run(
            host=Config.WEB_HOST,
            port=Config.WEB_PORT,
            debug=False,
            use_reloader=False
        )
        
    except KeyboardInterrupt:
        logger.info("\nShutdown requested... cleaning up")
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Cleanup
        if indexer_instance and Config.INDEXER_AUTO_FLUSH:
            indexer_instance.stop_auto_flush()
            indexer_instance.flush()
            logger.info("✓ Index flushed and saved")

# ============================================================================
# TOP-LEVEL EXECUTION (Runs on import by production server)
# ============================================================================

# Validate configuration and Setup environment
if not Config.validate():
    logger.error("Configuration validation failed!")
    sys.exit(1)

setup_logging(Config.LOG_LEVEL)
ensure_storage_dir(Config.STORAGE_DATA_DIR)

logger.info("="*60)
logger.info("Initializing Search Engine Components for Web Service")
logger.info("="*60)

logger = logging.getLogger(__name__)

# Initialize all components outside of a function
try:
    # 1. Core components
    tokenizer = Tokenizer()
    database_path = os.path.join(Config.STORAGE_DATA_DIR, 'index.json')
    database = Database(database_path)
    indexer = Indexer(database, tokenizer)
    ranker = AdvancedRanker(indexer)
    spider = Spider(
        tokenizer=tokenizer,
        indexer=indexer,
        max_workers=Config.CRAWLER_MAX_WORKERS
    )
    logger.info("✓ Core components (Tokenizer, Database, Indexer, Ranker, Spider) initialized.")
    
    # 2. External API clients (conditional imports)
    serpapi_client = None
    if Config.SERPAPI_ENABLED and Config.SERPAPI_KEY:
        from src.external.serpapi_client import SerpAPIClient
        serpapi_client = SerpAPIClient(timeout=Config.SERPAPI_TIMEOUT)
        logger.info("✓ SerpAPI client initialized.")
        
    google_client = None
    if Config.GOOGLE_ENABLED and os.getenv('GOOGLE_API_KEY') and os.getenv('GOOGLE_SEARCH_ENGINE_ID'):
        from src.external.google_search_client import GoogleSearchClient
        google_client = GoogleSearchClient()
        logger.info("✓ Google Search client initialized.")
    
    # 3. SearchManager (CRITICAL DEPENDENCY)
    from src.search.search_manager import SearchManager
    search_manager = SearchManager(
        local_ranker=ranker,
        serpapi_client=serpapi_client,
        google_client=google_client,
        mode=Config.SEARCH_MODE
    )
    logger.info("✓ SearchManager initialized in '%s' mode with external clients.", Config.SEARCH_MODE)
    
    # 4. Marketplace and Jobs (conditional imports)
    from src.marketplace.marketplace_client import MarketplaceClient
    from src.marketplace.price_alerts import PriceAlertManager
    from src.jobs.job_search_client import JobSearchClient, JobAlertManager
    
    marketplace_client = MarketplaceClient()
    price_alert_manager = PriceAlertManager()
    job_search_client = JobSearchClient()
    job_alert_manager = JobAlertManager()
    logger.info("✓ Marketplace and Jobs components initialized.")
    
    # 5. Inject components into the Flask app (CRITICAL STEP)
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
    logger.info("✓ All components successfully INJECTED into the Flask application.")

    # 6. --- INITIAL LARGE-SCALE CRAWL EXECUTION (For bootstrapping index) ---
    logger.info(f"Bootstrapping index by crawling {len(BOOTSTRAP_URLS)} starting domains...")

    # 6. --- ASYNCHRONOUS CRAWL TRIGGER ---
    CRAWL_MAX_DEPTH = 3 
    MAX_TOTAL_PAGES = 12000
    
    logger.info("Triggering asynchronous bootstrap crawl via Celery...")
    
    # Call the Celery task non-blocking, so the web server starts immediately
    bootstrap_crawl_task.delay(
        urls=BOOTSTRAP_URLS, 
        max_depth=CRAWL_MAX_DEPTH, 
        max_total_pages=MAX_TOTAL_PAGES
    )
    
    logger.info("✓ Celery task successfully dispatched. Web server will now start.")
    # --- END ASYNCHRONOUS CRAWL TRIGGER ---
except Exception as e:
    logger.error(f"FATAL: Failed to initialize or execute bootstrap crawl: {e}", exc_info=True)
    # Exit cleanly if initialization fails to prevent the web server from starting unconfigured.
    sys.exit(1)


# ============================================================================
# Local Development Entry Point
# ============================================================================

if __name__ == '__main__':
    # We call the helper function here, using the objects we initialized above.
    run_development_server(indexer)