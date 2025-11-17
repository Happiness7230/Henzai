"""
Flask Web Application - Phase 2 Update
Updated with SerpAPI integration and new search endpoints
"""

import os, sys
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
# Import Phase 1 components
from src.config.config import Config
from src.external.serpapi_client import SerpAPIClient, SerpAPIException
from src.search.search_manager import SearchManager
from dataclasses import asdict
from src.external.google_search_client import GoogleSearchClient
from src.marketplace.marketplace_client import MarketplaceClient
from src.marketplace.price_alerts import PriceAlertManager
from src.jobs.job_search_client import JobSearchClient, JobAlertManager

from src.search.search_manager import SearchManager
from src.external.google_search_client import GoogleSearchClient

google_client = GoogleSearchClient()
search_manager = SearchManager(google_client=GoogleSearchClient())

# Import existing components (assuming they exist)
try:
    from src.ranking.advanced_ranker import AdvancedRanker
except ImportError:
    AdvancedRanker = None

try:
    from src.caching.cache_manager import CacheManager
except ImportError:
    CacheManager = None

try:
    from src.storage.analytics_store import AnalyticsStore
except ImportError:
    AnalyticsStore = None

try:
    from src.monitoring.metrics import MetricsCollector
except ImportError:
    MetricsCollector = None

try:
    from src.crawler.spider import Spider
except ImportError:
    Spider = None

logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['JSON_SORT_KEYS'] = False

# Enable CORS if configured
if Config.CORS_ENABLED:
    CORS(app, origins=Config.CORS_ORIGINS)

# Initialize components
cache_manager = None
local_ranker = None
serpapi_client = None
search_manager = None
analytics_store = None
metrics_collector = None
spider = None

def initialize_components():
    """Initialize all application components"""
    global cache_manager, local_ranker, serpapi_client, search_manager
    global analytics_store, metrics_collector, spider
    
    logger.info("Initializing application components...")
    
    # Initialize cache
    if CacheManager and Config.CACHE_ENABLED:
        try:
            cache_manager = CacheManager()
            logger.info("✓ Cache manager initialized")
        except Exception as e:
            logger.warning(f"Cache initialization failed: {e}")
    
    # Initialize tokenizer and indexer (required for ranker and spider)
    tokenizer = None
    indexer = None
    try:
        from src.processing.tokenizer import Tokenizer
        from src.indexing.indexer import Indexer
        from src.storage.database import Database
        
        tokenizer = Tokenizer()
        database = Database(os.path.join(Config.STORAGE_DATA_DIR, 'index.json'))
        indexer = Indexer(database, tokenizer)
        logger.info("✓ Tokenizer and indexer initialized")
    except Exception as e:
        logger.warning(f"Tokenizer/Indexer initialization failed: {e}")
    
    # Initialize local ranker (requires indexer)
    if AdvancedRanker and indexer:
        try:
            local_ranker = AdvancedRanker(indexer)
            logger.info("✓ Local ranker initialized")
        except Exception as e:
            logger.warning(f"Local ranker initialization failed: {e}")
    
    # Initialize SerpAPI client
    if Config.SERPAPI_ENABLED:
        try:
            serpapi_client = SerpAPIClient(timeout=Config.SERPAPI_TIMEOUT)
            if serpapi_client.health_check():
                logger.info("✓ SerpAPI client initialized and connected")
            else:
                logger.warning("SerpAPI health check failed")
                serpapi_client = None
        except Exception as e:
            logger.error(f"SerpAPI initialization failed: {e}")
            serpapi_client = None
    
    # Initialize search manager
    search_manager = SearchManager(
        local_ranker=local_ranker,
        serpapi_client=serpapi_client,
        cache_manager=cache_manager,
        mode=Config.SEARCH_MODE
    )
    logger.info(f"✓ Search manager initialized in '{Config.SEARCH_MODE}' mode")
    
    # Initialize analytics
    if AnalyticsStore and Config.ANALYTICS_ENABLED:
        try:
            analytics_store = AnalyticsStore()
            logger.info("✓ Analytics store initialized")
        except Exception as e:
            logger.warning(f"Analytics initialization failed: {e}")
    
    # Initialize metrics
    if MetricsCollector:
        try:
            metrics_collector = MetricsCollector()
            logger.info("✓ Metrics collector initialized")
        except Exception as e:
            logger.warning(f"Metrics initialization failed: {e}")
    
    # Initialize crawler (requires tokenizer and indexer)
    if Spider and tokenizer and indexer:
        try:
            spider = Spider(tokenizer, indexer, max_workers=Config.CRAWLER_MAX_WORKERS)
            logger.info("✓ Spider initialized")
        except Exception as e:
            logger.warning(f"Spider initialization failed: {e}")
    
    logger.info("Application initialization complete!")

# existing global services
db = None
search_engine = None
metrics = None

# ADD these after existing global variables ⬇
search_manager = None
google_client = None
marketplace_client = None
price_alert_manager = None
job_search_client = None
job_alert_manager = None

# Initialize on startup

def initialize_components():
    """Initialize all application components"""
    global cache_manager, local_ranker, serpapi_client, search_manager
    global analytics_store, metrics_collector, spider
    global google_client, marketplace_client, price_alert_manager  # ADD THIS LINE
    global job_search_client, job_alert_manager  # ADD THIS LINE
    
    logger.info("Initializing application components...")
    
    initialize_components()
    
    # ADD THESE NEW SECTIONS:
    
    # Initialize Google Search client
    if Config.GOOGLE_ENABLED:
        try:
            google_client = GoogleSearchClient()
            if google_client.health_check():
                logger.info("✓ Google Search client initialized and connected")
            else:
                logger.warning("Google Search health check failed")
                google_client = None
        except Exception as e:
            logger.error(f"Google Search initialization failed: {e}")
            google_client = None
    
    # Initialize Marketplace client
    try:
        marketplace_client = MarketplaceClient()
        logger.info("✓ Marketplace client initialized")
    except Exception as e:
        logger.warning(f"Marketplace initialization failed: {e}")
    
    # Initialize Price Alert Manager
    try:
        price_alert_manager = PriceAlertManager()
        logger.info("✓ Price alert manager initialized")
    except Exception as e:
        logger.warning(f"Price alert manager initialization failed: {e}")
    
    # Initialize Job Search client
    try:
        job_search_client = JobSearchClient()
        logger.info("✓ Job search client initialized")
    except Exception as e:
        logger.warning(f"Job search initialization failed: {e}")
    
    # Initialize Job Alert Manager
    try:
        job_alert_manager = JobAlertManager()
        logger.info("✓ Job alert manager initialized")
    except Exception as e:
        logger.warning(f"Job alert manager initialization failed: {e}")
    
    # UPDATE Search Manager initialization to include google_client:
    search_manager = SearchManager(
        local_ranker=local_ranker,
        serpapi_client=serpapi_client,
        google_client=google_client,  # ADD THIS LINE
        cache_manager=cache_manager,
        mode=Config.SEARCH_MODE
    )
    logger.info(f"✓ Search manager initialized in '{Config.SEARCH_MODE}' mode")
    


# ============================================================================
# ROUTES - Homepage & UI
# ============================================================================

@app.route('/')
def index():
    """Render search homepage"""
    return render_template('search.html')


@app.route('/results')
def results():
    """Render results page"""
    query = request.args.get('q', '')
    return render_template('results.html', query=query)


# ============================================================================
# ROUTES - Search API (NEW)
# ============================================================================

@app.route('/api/search', methods=['GET', 'POST'])
def api_search():
    """
    Unified search endpoint
    
    Query Parameters / JSON Body:
        q (str): Search query
        max_results (int): Maximum results (default: 10)
        mode (str): Search mode override (local/serpapi/hybrid)
        safe_search (bool): Enable safe search
        region (str): Region code (e.g., 'us-en')
        time_period (str): Time filter (d/w/m/y)
        filters (dict): Advanced filters
    
    Returns:
        JSON with search results
    """
    start_time = datetime.now()
    
    try:
        # Get parameters
        if request.method == 'POST':
            data = request.get_json() or {}
        else:
            data = request.args.to_dict()
        
        query = data.get('q', '').strip()
        if not query:
            return jsonify({
                'error': 'Query parameter "q" is required',
                'status': 'error'
            }), 400
        
        max_results = int(data.get('max_results', 10))
        mode_override = data.get('mode')
        safe_search = data.get('safe_search', 'true').lower() == 'true'
        region = data.get('region', 'wt-wt')
        time_period = data.get('time_period')
        filters = data.get('filters', {})
        
        # Temporarily override mode if requested
        original_mode = search_manager.mode
        if mode_override and mode_override in ['local', 'serpapi', 'hybrid']:
            search_manager.set_mode(mode_override)
        
        # Perform search
        results = search_manager.search(
            query=query,
            max_results=max_results,
            filters=filters,
            safe_search=safe_search,
            region=region,
            time_period=time_period
        )
        
        # Restore original mode
        if mode_override:
            search_manager.set_mode(original_mode)
        
        # Track analytics
        if analytics_store:
            analytics_store.track_search(
                query=query,
                results_count=len(results.get('results', [])),
                response_time=results['metadata'].get('response_time', 0),
                mode=results['metadata'].get('mode', 'unknown')
            )
        
        # Track metrics
        if metrics_collector:
            metrics_collector.record_search(
                query_length=len(query),
                results_count=len(results.get('results', [])),
                response_time=(datetime.now() - start_time).total_seconds()
            )
        
        return jsonify({
            'status': 'success',
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Search error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'error': str(e),
            'query': query if 'query' in locals() else None
        }), 500


@app.route('/api/suggestions', methods=['GET'])
def api_suggestions():
    """
    Get autocomplete suggestions
    
    Query Parameters:
        q (str): Partial query
        max (int): Maximum suggestions (default: 10)
    
    Returns:
        JSON with suggestion list
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400
        
        max_suggestions = int(request.args.get('max', 10))
        
        # Get suggestions from search manager
        suggestions = search_manager.get_suggestions(query, max_suggestions)
        
        return jsonify({
            'status': 'success',
            'query': query,
            'suggestions': suggestions
        })
    
    except Exception as e:
        logger.error(f"Suggestions error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/search/news', methods=['GET'])
def api_search_news():
    """
    Search for news articles
    
    Query Parameters:
        q (str): Search query
        max_results (int): Maximum results (default: 10)
    
    Returns:
        JSON with news results
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400
        
        max_results = int(request.args.get('max_results', 10))
        
        if not serpapi_client:
            return jsonify({
                'status': 'error',
                'error': 'News search requires SerpAPI to be enabled'
            }), 503
        
        # Search news
        results = serpapi_client.search_news(query, max_results)
        
        return jsonify({
            'status': 'success',
            'data': results
        })
    
    except Exception as e:
        logger.error(f"News search error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/search/images', methods=['GET'])
def api_search_images():
    """
    Search for images
    
    Query Parameters:
        q (str): Search query
        max_results (int): Maximum results (default: 20)
    
    Returns:
        JSON with image results
    """
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400
        
        max_results = int(request.args.get('max_results', 20))
        
        if not serpapi_client:
            return jsonify({
                'status': 'error',
                'error': 'Image search requires SerpAPI to be enabled'
            }), 503
        
        # Search images
        results = serpapi_client.search_images(query, max_results)
        
        return jsonify({
            'status': 'success',
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Image search error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/search/mode', methods=['POST'])
def api_set_search_mode():
    """
    Change search mode at runtime
    
    JSON Body:
        mode (str): New search mode (local/serpapi/hybrid)
    
    Returns:
        JSON with success status
    """
    try:
        data = request.get_json() or {}
        mode = data.get('mode', '').lower()
        
        if not mode:
            return jsonify({
                'status': 'error',
                'error': 'Mode parameter is required'
            }), 400
        
        if search_manager.set_mode(mode):
            return jsonify({
                'status': 'success',
                'mode': mode,
                'message': f'Search mode changed to {mode}'
            })
        else:
            return jsonify({
                'status': 'error',
                'error': f'Invalid mode: {mode}. Must be local, serpapi, or hybrid'
            }), 400
    
    except Exception as e:
        logger.error(f"Mode change error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ============================================================================
# ROUTES - Crawling (Updated)
# ============================================================================

@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    """
    Crawl URLs and add to index
    
    JSON Body:
        urls (list): List of URLs to crawl
        max_depth (int): Maximum crawl depth (default: 1)
    
    Returns:
        JSON with crawl status
    """
    try:
        if not spider:
            return jsonify({
                'status': 'error',
                'error': 'Crawler not initialized'
            }), 503
        
        data = request.get_json() or {}
        urls = data.get('urls', [])
        max_depth = int(data.get('max_depth', 1))
        
        if not urls:
            return jsonify({
                'status': 'error',
                'error': 'URLs list is required'
            }), 400
        
        # Start crawling
        results = spider.crawl(urls, max_depth=max_depth)
        
        return jsonify({
            'status': 'success',
            'message': f'Crawled {len(results)} pages',
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Crawl error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ============================================================================
# ROUTES - Analytics & Statistics (NEW)
# ============================================================================

@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    """
    Get search analytics
    
    Returns:
        JSON with analytics data
    """
    try:
        analytics = {
            'search_manager': search_manager.get_stats() if search_manager else {},
            'serpapi': serpapi_client.get_stats() if serpapi_client else {},
            'cache': cache_manager.get_stats() if cache_manager else {}
        }
        
        # Add analytics store data if available
        if analytics_store:
            analytics['queries'] = analytics_store.get_popular_queries(limit=10)
            analytics['recent'] = analytics_store.get_recent_searches(limit=20)
        
        return jsonify({
            'status': 'success',
            'data': analytics
        })
    
    except Exception as e:
        logger.error(f"Analytics error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """
    Get system statistics
    
    Returns:
        JSON with system stats
    """
    try:
        stats = {
            'search_mode': search_manager.mode if search_manager else 'unknown',
            'serpapi_enabled': Config.SERPAPI_ENABLED,
            'cache_enabled': Config.CACHE_ENABLED,
            'analytics_enabled': Config.ANALYTICS_ENABLED,
            'components': {
                'search_manager': search_manager is not None,
                'serpapi_client': serpapi_client is not None,
                'local_ranker': local_ranker is not None,
                'cache_manager': cache_manager is not None,
                'analytics_store': analytics_store is not None,
                'spider': spider is not None
            }
        }
        
        if search_manager:
            stats['search_stats'] = search_manager.get_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
    
    except Exception as e:
        logger.error(f"Stats error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ============================================================================
# ROUTES - Health & Monitoring (Updated)
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    
    Returns:
        JSON with health status
    """
    try:
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Check SerpAPI
        if serpapi_client:
            health['components']['serpapi'] = serpapi_client.health_check()
        
        # Check cache
        if cache_manager:
            health['components']['cache'] = True
        
        # Check search manager
        if search_manager:
            health['components']['search_manager'] = True
        
        # Overall status
        all_healthy = all(health['components'].values())
        health['status'] = 'healthy' if all_healthy else 'degraded'
        
        status_code = 200 if all_healthy else 503
        
        return jsonify(health), status_code
    
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500


@app.route('/api/metrics', methods=['GET'])
def api_metrics():
    """
    Prometheus-style metrics endpoint
    
    Returns:
        Plain text metrics
    """
    try:
        metrics = []
        
        # Search metrics
        if search_manager:
            stats = search_manager.get_stats()
            metrics.append(f'search_total_searches {stats.get("total_searches", 0)}')
            metrics.append(f'search_cache_hits {stats.get("cache_hits", 0)}')
            metrics.append(f'search_avg_response_time {stats.get("avg_response_time", 0)}')
        
        # SerpAPI metrics
        if serpapi_client:
            stats = serpapi_client.get_stats()
            metrics.append(f'serpapi_total_requests {stats.get("total_requests", 0)}')
            metrics.append(f'serpapi_successful_requests {stats.get("successful_requests", 0)}')
            metrics.append(f'serpapi_failed_requests {stats.get("failed_requests", 0)}')
        
        return '\n'.join(metrics), 200, {'Content-Type': 'text/plain'}
    
    except Exception as e:
        logger.error(f"Metrics error: {str(e)}")
        return str(e), 500


# ============================================================================
# ROUTES - Cache Management (NEW)
# ============================================================================

@app.route('/api/cache/stats', methods=['GET'])
def api_cache_stats():
    """Get cache statistics"""
    try:
        if not cache_manager:
            return jsonify({
                'status': 'error',
                'error': 'Cache not enabled'
            }), 503
        
        stats = cache_manager.get_stats()
        
        return jsonify({
            'status': 'success',
            'data': stats
        })
    
    except Exception as e:
        logger.error(f"Cache stats error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/cache/clear', methods=['POST'])
def api_cache_clear():
    """Clear cache"""
    try:
        if not cache_manager:
            return jsonify({
                'status': 'error',
                'error': 'Cache not enabled'
            }), 503
        
        cache_manager.clear()
        
        return jsonify({
            'status': 'success',
            'message': 'Cache cleared successfully'
        })
    
    except Exception as e:
        logger.error(f"Cache clear error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'status': 'error',
        'error': 'Not found',
        'code': 404
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        'status': 'error',
        'error': 'Internal server error',
        'code': 500
    }), 500


@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all uncaught exceptions"""
    logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
    return jsonify({
        'status': 'error',
        'error': str(error)
    }), 500


# ============================================================================
# Application Entry Point
# ============================================================================

if __name__ == '__main__':
    # Print configuration
    logger.info("Starting Flask application...")
    Config.print_config()
    
    # Run app
    app.run(
        host='0.0.0.0',
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
# Initialize job search components
job_search_client = None
job_alert_manager = None

def initialize_job_components():
    global job_search_client, job_alert_manager
    
    from src.jobs.job_search_client import JobSearchClient, JobAlertManager
    
    try:
        job_search_client = JobSearchClient()
        logger.info("✓ Job search client initialized")
    except Exception as e:
        logger.warning(f"Job search initialization failed: {e}")
    
    try:
        job_alert_manager = JobAlertManager()
        logger.info("✓ Job alert manager initialized")
    except Exception as e:
        logger.warning(f"Job alert manager initialization failed: {e}")

# Call in initialize_components()
initialize_job_components()

# === JOB SEARCH ENDPOINTS ===

@app.route('/api/jobs/search', methods=['GET', 'POST'])
def api_job_search():
    """Search for jobs"""
    try:
        if not job_search_client:
            return jsonify({
                'status': 'error',
                'error': 'Job search not available'
            }), 503
        
        if request.method == 'POST':
            data = request.get_json() or {}
        else:
            data = request.args.to_dict()
        
        query = data.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400
        
        results = job_search_client.search_jobs(
            query=query,
            location=data.get('location', ''),
            max_results=int(data.get('max_results', 20)),
            remote_only=data.get('remote_only', 'false').lower() == 'true',
            min_salary=int(data['min_salary']) if data.get('min_salary') else None,
            experience_level=data.get('experience_level'),
            job_type=data.get('job_type'),
            sources=data.get('sources', '').split(',') if data.get('sources') else None
        )
        
        return jsonify({
            'status': 'success',
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Job search error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/jobs/alerts', methods=['GET', 'POST'])
def api_job_alerts():
    """Get or create job alerts"""
    try:
        if not job_alert_manager:
            return jsonify({
                'status': 'error',
                'error': 'Job alerts not available'
            }), 503
        
        if request.method == 'GET':
            email = request.args.get('email')
            if not email:
                return jsonify({
                    'status': 'error',
                    'error': 'Email parameter is required'
                }), 400
            
            alerts = job_alert_manager.get_user_alerts(email)
            return jsonify({
                'status': 'success',
                'data': alerts
            })
        
        else:  # POST
            data = request.get_json() or {}
            required = ['email', 'keywords', 'location']
            
            for field in required:
                if field not in data:
                    return jsonify({
                        'status': 'error',
                        'error': f'Missing required field: {field}'
                    }), 400
            
            alert_id = job_alert_manager.create_alert(
                user_email=data['email'],
                keywords=data['keywords'],
                location=data['location'],
                remote_only=data.get('remote_only', False),
                min_salary=int(data['min_salary']) if data.get('min_salary') else None
            )
            
            return jsonify({
                'status': 'success',
                'alert_id': alert_id,
                'message': 'Job alert created successfully'
            })
    
    except Exception as e:
        logger.error(f"Job alert error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500
    
# === MARKETPLACE ENDPOINTS ===

@app.route('/marketplace')
def marketplace_page():
    """Render marketplace search page"""
    query = request.args.get('q', '')
    return render_template('marketplace.html', query=query)


@app.route('/api/marketplace/search', methods=['GET', 'POST'])
def api_marketplace_search():
    """Search across multiple marketplaces"""
    try:
        if not marketplace_client:
            return jsonify({
                'status': 'error',
                'error': 'Marketplace search not available'
            }), 503
        
        if request.method == 'POST':
            data = request.get_json() or {}
        else:
            data = request.args.to_dict()
        
        query = data.get('q', '').strip()
        if not query:
            return jsonify({
                'status': 'error',
                'error': 'Query parameter "q" is required'
            }), 400
        
        max_results = int(data.get('max_results', 10))
        marketplaces = data.get('marketplaces', '').split(',') if data.get('marketplaces') else None
        min_price = float(data['min_price']) if data.get('min_price') else None
        max_price = float(data['max_price']) if data.get('max_price') else None
        sort_by = data.get('sort_by', 'relevance')
        
        results = marketplace_client.search_all(
            query=query,
            max_results=max_results,
            marketplaces=marketplaces,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by
        )
        
        return jsonify({
            'status': 'success',
            'data': results
        })
    
    except Exception as e:
        logger.error(f"Marketplace search error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/marketplace/compare', methods=['POST'])
def api_marketplace_compare():
    """Compare multiple products"""
    try:
        if not marketplace_client:
            return jsonify({
                'status': 'error',
                'error': 'Product comparison not available'
            }), 503
        
        data = request.get_json() or {}
        product_ids = data.get('product_ids', [])
        
        if not product_ids:
            return jsonify({
                'status': 'error',
                'error': 'product_ids array is required'
            }), 400
        
        comparison = marketplace_client.compare_products(product_ids)
        
        return jsonify({
            'status': 'success',
            'data': comparison
        })
    
    except Exception as e:
        logger.error(f"Product comparison error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/alerts', methods=['GET', 'POST'])
def api_price_alerts():
    """Get or create price alerts"""
    try:
        if not price_alert_manager:
            return jsonify({
                'status': 'error',
                'error': 'Price alerts not available'
            }), 503
        
        if request.method == 'GET':
            email = request.args.get('email')
            if not email:
                return jsonify({
                    'status': 'error',
                    'error': 'Email parameter is required'
                }), 400
            
            alerts = price_alert_manager.get_user_alerts(email)
            return jsonify({
                'status': 'success',
                'data': [asdict(a) for a in alerts]
            })
        
        else:  # POST
            data = request.get_json() or {}
            required = ['email', 'product_name', 'product_url', 'marketplace', 'target_price', 'current_price']
            
            for field in required:
                if field not in data:
                    return jsonify({
                        'status': 'error',
                        'error': f'Missing required field: {field}'
                    }), 400
            
            alert_id = price_alert_manager.create_alert(
                user_email=data['email'],
                product_name=data['product_name'],
                product_url=data['product_url'],
                marketplace=data['marketplace'],
                target_price=float(data['target_price']),
                current_price=float(data['current_price'])
            )
            
            return jsonify({
                'status': 'success',
                'alert_id': alert_id,
                'message': 'Price alert created successfully'
            })
    
    except Exception as e:
        logger.error(f"Price alert error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/alerts/<alert_id>', methods=['GET', 'PUT', 'DELETE'])
def api_price_alert_detail(alert_id):
    """Get, update, or delete a specific alert"""
    try:
        if not price_alert_manager:
            return jsonify({
                'status': 'error',
                'error': 'Price alerts not available'
            }), 503
        
        if request.method == 'GET':
            alert = price_alert_manager.get_alert(alert_id)
            if not alert:
                return jsonify({
                    'status': 'error',
                    'error': 'Alert not found'
                }), 404
            
            return jsonify({
                'status': 'success',
                'data': asdict(alert)
            })
        
        elif request.method == 'PUT':
            data = request.get_json() or {}
            target_price = float(data.get('target_price'))
            
            if price_alert_manager.update_alert(alert_id, target_price):
                return jsonify({
                    'status': 'success',
                    'message': 'Alert updated'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Alert not found'
                }), 404
        
        else:  # DELETE
            if price_alert_manager.delete_alert(alert_id):
                return jsonify({
                    'status': 'success',
                    'message': 'Alert deleted'
                })
            else:
                return jsonify({
                    'status': 'error',
                    'error': 'Alert not found'
                }), 404
    
    except Exception as e:
        logger.error(f"Price alert detail error: {str(e)}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

