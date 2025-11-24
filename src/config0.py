"""Configuration management for the search engine."""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

from config import config

@dataclass
class Config:
    # Flask Settings
    flask_env: str
    flask_port: 5000
    flask_debug: True
    search_mode: str = "hybrid"
    google_enabled: bool = False
    serpapi_enabled: bool = False
    flask_port: int = 5000
    log_level: str = "INFO"

    # Crawler Settings
    max_workers: int
    crawl_timeout: int
    max_pages_per_domain: int
    respect_robots_txt: bool
    user_agent: str

    # Indexer Settings
    index_file: str
    auto_flush: bool
    flush_interval: int
    max_index_size: int

    # Storage Settings
    storage_dir: str
    backup_enabled: bool
    backup_interval: int

    # Ranking Settings
    min_term_frequency: int
    max_results: 10

    # Debug Settings
    log_level: str
    profile_enabled: bool

    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from environment variables."""
        load_dotenv()  # Load .env file if it exists

        def get_env_bool(key: str, default: bool = False) -> bool:
            return os.getenv(key, str(default)).lower() in ('true', '1', 'yes')

        def get_env_int(key: str, default: int) -> int:
            return int(os.getenv(key, default))

        config = cls(
            # Flask Settings
            flask_env=os.getenv('FLASK_ENV', 'development'),
            flask_port=get_env_int('FLASK_PORT', 5000),
            flask_debug=get_env_bool('FLASK_DEBUG', True),

    # Crawler Settings
            max_workers=get_env_int('MAX_WORKERS', 4),
            crawl_timeout=get_env_int('CRAWL_TIMEOUT', 30),
            max_pages_per_domain=get_env_int('MAX_PAGES_PER_DOMAIN', 100),
            respect_robots_txt=get_env_bool('RESPECT_ROBOTS_TXT', True),
            user_agent=os.getenv('USER_AGENT', 'SearchEngine/1.0'),

    # Indexer Settings
            index_file=os.getenv('INDEX_FILE', 'index.json'),
            auto_flush=get_env_bool('AUTO_FLUSH', True),
            flush_interval=get_env_int('FLUSH_INTERVAL', 5),
            max_index_size=get_env_int('MAX_INDEX_SIZE', 100000),
        
            # Storage Settings
            storage_dir=os.getenv('STORAGE_DIR', 'data'),
            backup_enabled=get_env_bool('BACKUP_ENABLED', True),
            backup_interval=get_env_int('BACKUP_INTERVAL', 3600),

            # Ranking Settings
            min_term_frequency=get_env_int('MIN_TERM_FREQUENCY', 2),
            max_results=get_env_int('MAX_RESULTS', 100),

            # Debug Settings
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            profile_enabled=get_env_bool('PROFILE_ENABLED', False)
)
        # === Search Integration Settings ===
        config.search_mode = os.getenv('SEARCH_MODE', 'hybrid')
        config.google_enabled = get_env_bool('GOOGLE_ENABLED', False)
        config.serpapi_enabled = get_env_bool('SERPAPI_ENABLED', False)
        
        return config

    def validate(self) -> 'list[str]':  # Python 3.8 compatible type hint
        """Validate configuration values and return list of error messages."""
        errors = []

        if self.max_workers < 1:
            errors.append("MAX_WORKERS must be at least 1")
        if self.crawl_timeout < 1:
            errors.append("CRAWL_TIMEOUT must be positive")
        if self.max_pages_per_domain < 1:
            errors.append("MAX_PAGES_PER_DOMAIN must be positive")
        if self.flush_interval < 1:
            errors.append("FLUSH_INTERVAL must be positive")
        if self.max_index_size < 1000:
            errors.append("MAX_INDEX_SIZE must be at least 1000")
        if self.max_results < 1:
            errors.append("MAX_RESULTS must be positive")
        if self.log_level not in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
            errors.append("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")

        return errors