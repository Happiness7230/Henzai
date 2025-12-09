from celery import Celery
import logging
import os
from src.jobs.email_notifications import send_job_alert_email, send_price_alert_email

logger = logging.getLogger(__name__)

# --- FIX: Read Redis URL from environment for production deployment ---
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

celery = Celery(
    "search_engine",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery.conf.timezone = "UTC"
celery.conf.enable_utc = True

# --- NEW: Asynchronous Crawl Task ---
@celery.task(name='celery_app.bootstrap_crawl_task')
def bootstrap_crawl_task(urls: list, max_depth: int, max_total_pages: int):
    """
    Long-running background task to perform the initial deep web crawl.
    This runs asynchronously, allowing the web server to start instantly.
    """
    logger.info(f"--- CELERY CRAWL STARTING ---")
    logger.info(f"Task received {len(urls)} starting URLs. Target Depth={max_depth}.")
    
    # CRITICAL: Components must be initialized inside the task worker process
    # as they are independent of the Flask worker process.
    try:
        from src.config.config import Config
        from src.processing.tokenizer import Tokenizer
        from src.indexing.indexer import Indexer
        from src.storage.database import Database
        from src.crawler.spider import Spider
        
        # 1. Initialize core dependencies (must match main.py setup)
        tokenizer = Tokenizer()
        database_path = os.path.join(Config.STORAGE_DATA_DIR, 'index.json')
        database = Database(database_path)
        indexer = Indexer(database, tokenizer)
        
        # 2. Re-load the existing index before crawling (if necessary)
        # Note: If Database is backed by a network service (like Redis/DB), 
        # connection failure here will be caught by the outer try/except.
        if hasattr(database, 'load_index'):
             database.load_index() # Assuming database can load index into indexer/memory
        
        # 3. Initialize Spider
        spider = Spider(
            tokenizer=tokenizer,
            indexer=indexer,
            max_workers=Config.CRAWLER_MAX_WORKERS
            # Note: DocumentStore must also be passed if required by Spider constructor
        )
        logger.info("Celery worker components initialized successfully.")
        
        # 4. Execute the blocking crawl operation
        stats = spider.crawl(
            urls=urls, 
            max_depth=max_depth, 
            max_total_pages=max_total_pages
        )
        
        # 5. Ensure index is persisted after crawl completion
        indexer.flush()
        logger.info(f"--- CELERY CRAWL FINISHED --- Indexed {stats['crawled']} pages.")
        
        return stats

    except Exception as e:
        logger.error(f"Celery crawl task failed fatally. Check if Redis is running and REDIS_URL='{REDIS_URL}' is correct: {e}", exc_info=True)
        # Re-raise the exception so Celery records the failure
        raise


@celery.task(name='celery_app.check_job_alerts')
def check_job_alerts():
    """Background task to check job alerts (existing function)"""
    from src.jobs.job_search_client import JobSearchClient, JobAlertManager
    
    alert_manager = JobAlertManager()
    job_client = JobSearchClient()
    
    alerts = [a for a in alert_manager.alerts.values() if a['is_active']]
    
    for alert in alerts:
        try:
            results = job_client.search_jobs(
                query=alert['keywords'],
                location=alert['location'],
                remote_only=alert['remote_only'],
                min_salary=alert['min_salary'],
                max_results=5
            )
            
            if results['jobs']:
                # Send notification email
                send_job_alert_email(alert, results['jobs'])
                
        except Exception as e:
            logger.error(f"Error checking job alert {alert['id']}: {e}")


# --- NEW: Asynchronous Price Alert Task ---
@celery.task(name='celery_app.check_price_alerts')
def check_price_alerts():
    """Background task to monitor product prices and send alerts if target price is met."""
    from src.marketplace.marketplace_client import MarketplaceClient
    from src.marketplace.price_alerts import PriceAlertManager

    alert_manager = PriceAlertManager()
    marketplace_client = MarketplaceClient()

    alerts = [a for a in alert_manager.alerts.values() if a.get('is_active', True)]

    for alert in alerts:
        try:
            # Note: Assuming PriceAlertManager stores product_id, not just URL.
            # We assume a helper method exists on MarketplaceClient to fetch a single price.
            
            # --- Conceptual Call to External API (or client) ---
            current_price_data = marketplace_client.fetch_product_price(
                product_id=alert.get('product_id'), 
                marketplace=alert.get('marketplace')
            )
            # --- End Conceptual Call ---

            current_price = current_price_data.get('price')

            if current_price and current_price <= alert.get('target_price', float('inf')):
                
                # Price target met!
                logger.info(f"Price alert triggered for {alert['product_name']}. Target met: {current_price}")
                
                # Send notification email (resolves the Pylance warning)
                send_price_alert_email(alert, {
                    'title': alert['product_name'], 
                    'price': current_price,
                    'url': alert.get('product_url', 'N/A')
                })
                
                # Optionally deactivate or log the alert as processed
                # alert_manager.deactivate_alert(alert['id']) 

        except Exception as e:
            logger.error(f"Error checking price alert {alert.get('id', 'N/A')}: {e}")


# Add to beat schedule
celery.conf.beat_schedule = {
    'check-job-alerts-daily': {
        'task': 'celery_app.check_job_alerts',
        'schedule': 86400.0,  # Daily (24 hours)
    },
    'check-price-alerts-hourly': {
        'task': 'celery_app.check_price_alerts',
        'schedule': 3600.0, # Hourly check (1 hour)
    }
}