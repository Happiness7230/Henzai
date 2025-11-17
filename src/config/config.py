"""
Configuration Module
Loads and manages application configuration from environment variables
"""

import os
from typing import Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration manager"""
    
    # Flask Configuration
    FLASK_APP = os.getenv('FLASK_APP', 'main.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # SerpAPI Configuration
    SERPAPI_KEY = os.getenv('SERPAPI_KEY', '')
    SERPAPI_ENABLED = os.getenv('SERPAPI_ENABLED', 'false').lower() == 'true'
    SERPAPI_TIMEOUT = int(os.getenv('SERPAPI_TIMEOUT', 5))
    SERPAPI_MAX_RESULTS = int(os.getenv('SERPAPI_MAX_RESULTS', 10))
    
    # Search Mode Configuration
    SEARCH_MODE = os.getenv('SEARCH_MODE', 'hybrid')  # local, serpapi, hybrid
    
    # Hybrid Search Configuration
    HYBRID_BLEND_RATIO = float(os.getenv('HYBRID_BLEND_RATIO', 0.5))
    HYBRID_LOCAL_BOOST = float(os.getenv('HYBRID_LOCAL_BOOST', 1.2))
    HYBRID_FRESHNESS_BOOST = float(os.getenv('HYBRID_FRESHNESS_BOOST', 1.1))
    HYBRID_DEDUPLICATE = os.getenv('HYBRID_DEDUPLICATE', 'true').lower() == 'true'
    
    # Crawler Settings
    CRAWLER_MAX_WORKERS = int(os.getenv('CRAWLER_MAX_WORKERS', 10))
    CRAWLER_TIMEOUT = int(os.getenv('CRAWLER_TIMEOUT', 10))
    CRAWLER_RESPECT_ROBOTS = os.getenv('CRAWLER_RESPECT_ROBOTS', 'true').lower() == 'true'
    CRAWLER_USER_AGENT = os.getenv('CRAWLER_USER_AGENT', 'CustomSearchBot/1.0')
    
    # Indexer Settings
    INDEXER_AUTO_FLUSH = os.getenv('INDEXER_AUTO_FLUSH', 'true').lower() == 'true'
    INDEXER_FLUSH_INTERVAL = int(os.getenv('INDEXER_FLUSH_INTERVAL', 300))
    
    # Storage Settings
    STORAGE_DATA_DIR = os.getenv('STORAGE_DATA_DIR', './data')
    STORAGE_BACKUP_ENABLED = os.getenv('STORAGE_BACKUP_ENABLED', 'true').lower() == 'true'
    STORAGE_BACKUP_INTERVAL = int(os.getenv('STORAGE_BACKUP_INTERVAL', 3600))
    
    # Redis Cache Settings
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')
    CACHE_ENABLED = os.getenv('CACHE_ENABLED', 'true').lower() == 'true'
    CACHE_TTL_SEARCH = int(os.getenv('CACHE_TTL_SEARCH', 3600))
    CACHE_TTL_SUGGESTIONS = int(os.getenv('CACHE_TTL_SUGGESTIONS', 86400))
    CACHE_TTL_API_RESULTS = int(os.getenv('CACHE_TTL_API_RESULTS', 3600))
    
    # Ranking Settings
    RANKING_MIN_FREQUENCY = int(os.getenv('RANKING_MIN_FREQUENCY', 1))
    RANKING_MAX_RESULTS = int(os.getenv('RANKING_MAX_RESULTS', 100))
    RANKING_BM25_K1 = float(os.getenv('RANKING_BM25_K1', 1.5))
    RANKING_BM25_B = float(os.getenv('RANKING_BM25_B', 0.75))
    
    # Logging Settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', 'json')
    LOG_DIR = os.getenv('LOG_DIR', './logs')
    LOG_ROTATION_SIZE = int(os.getenv('LOG_ROTATION_SIZE', 10485760))
    LOG_ROTATION_BACKUP_COUNT = int(os.getenv('LOG_ROTATION_BACKUP_COUNT', 5))
    
    # Analytics Settings
    ANALYTICS_ENABLED = os.getenv('ANALYTICS_ENABLED', 'true').lower() == 'true'
    ANALYTICS_TRACK_QUERIES = os.getenv('ANALYTICS_TRACK_QUERIES', 'true').lower() == 'true'
    ANALYTICS_TRACK_CLICKS = os.getenv('ANALYTICS_TRACK_CLICKS', 'true').lower() == 'true'
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv('RATE_LIMIT_REQUESTS_PER_MINUTE', 60))
    RATE_LIMIT_BURST = int(os.getenv('RATE_LIMIT_BURST', 10))
    
    # Security
    CORS_ENABLED = os.getenv('CORS_ENABLED', 'true').lower() == 'true'
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if configuration is valid
        """
        errors = []
        
        # Validate SerpAPI configuration
        if cls.SERPAPI_ENABLED and not cls.SERPAPI_KEY:
            errors.append("SERPAPI_KEY is required when SERPAPI_ENABLED is true")
        
        # Validate search mode
        valid_modes = ['local', 'serpapi', 'hybrid']
        if cls.SEARCH_MODE not in valid_modes:
            errors.append(f"SEARCH_MODE must be one of {valid_modes}")
        
        # Validate paths exist
        os.makedirs(cls.STORAGE_DATA_DIR, exist_ok=True)
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        
        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False
        
        return True
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return getattr(cls, key, default)
    
    @classmethod
    def to_dict(cls) -> dict:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
    
    @classmethod
    def print_config(cls):
        """Print current configuration (excluding sensitive data)"""
        sensitive_keys = ['SECRET_KEY', 'SERPAPI_KEY', 'REDIS_PASSWORD']
        
        print("\n" + "="*50)
        print("Current Configuration")
        print("="*50)
        
        for key, value in sorted(cls.to_dict().items()):
            if key in sensitive_keys:
                display_value = '***HIDDEN***' if value else 'Not Set'
            else:
                display_value = value
            print(f"{key}: {display_value}")
        
        print("="*50 + "\n")


# Validate configuration on import
if not Config.validate():
    print("Warning: Configuration validation failed. Please check your .env file.")
    
    # Google Search API
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '')
    GOOGLE_ENABLED = os.getenv('GOOGLE_ENABLED', 'false').lower() == 'true'
    
    # Marketplace APIs
    AMAZON_ACCESS_KEY = os.getenv('AMAZON_ACCESS_KEY', '')
    AMAZON_SECRET_KEY = os.getenv('AMAZON_SECRET_KEY', '')
    AMAZON_PARTNER_TAG = os.getenv('AMAZON_PARTNER_TAG', '')
    EBAY_APP_ID = os.getenv('EBAY_APP_ID', '')
    RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY', '')
    
    # Email Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USER = os.getenv('SMTP_USER', '')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
    
    # Search Engine Configuration
    PRIMARY_SEARCH_ENGINE = os.getenv('PRIMARY_SEARCH_ENGINE', 'google')
    FALLBACK_SEARCH_ENGINE = os.getenv('FALLBACK_SEARCH_ENGINE', 'serpapi')
    
    # Celery
    CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')