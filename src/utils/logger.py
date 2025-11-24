"""
Comprehensive Logging Setup
Professional logging with rotation, structured logging, and multiple handlers
"""

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any
import traceback


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured (JSON) logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Base log data
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors"""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )
        
        return super().format(record)


def setup_logging(
    log_dir: str = 'logs',
    log_level: str = 'INFO',
    console_output: bool = True,
    json_format: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 7
) -> logging.Logger:
    """
    Setup comprehensive logging system
    
    Args:
        log_dir: Directory for log files
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Enable console output
        json_format: Use JSON format for file logs
        max_bytes: Maximum size per log file
        backup_count: Number of backup files to keep
        
    Returns:
        Configured root logger
    """
    # Create logs directory
    os.makedirs(log_dir, exist_ok=True)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # ===== Main Application Log =====
    main_log_path = os.path.join(log_dir, 'search-engine.log')
    main_handler = logging.handlers.RotatingFileHandler(
        main_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    if json_format:
        main_handler.setFormatter(StructuredFormatter())
    else:
        main_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
    
    root_logger.addHandler(main_handler)
    
    # ===== Error Log (ERROR and above only) =====
    error_log_path = os.path.join(log_dir, 'error.log')
    error_handler = logging.handlers.RotatingFileHandler(
        error_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\n'
        'File: %(pathname)s:%(lineno)d\n'
        'Function: %(funcName)s\n'
        '%(message)s\n',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(error_handler)
    
    # ===== Performance Log =====
    perf_log_path = os.path.join(log_dir, 'performance.log')
    perf_handler = logging.handlers.RotatingFileHandler(
        perf_log_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # Only performance-related logs
    perf_handler.addFilter(lambda record: 'performance' in record.getMessage().lower() or hasattr(record, 'duration'))
    perf_handler.setFormatter(StructuredFormatter() if json_format else logging.Formatter(
        '%(asctime)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    root_logger.addHandler(perf_handler)
    
    # ===== Console Output =====
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        ))
        root_logger.addHandler(console_handler)
    
    # Log initial setup
    root_logger.info(f"Logging initialized: level={log_level}, dir={log_dir}")
    
    return root_logger


class PerformanceLogger:
    """
    Context manager for logging performance metrics
    """
    
    def __init__(self, logger: logging.Logger, operation: str, **kwargs):
        """
        Initialize performance logger
        
        Args:
            logger: Logger instance
            operation: Operation name
            **kwargs: Additional context
        """
        self.logger = logger
        self.operation = operation
        self.context = kwargs
        self.start_time = None
    
    def __enter__(self):
        """Start timing"""
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log performance"""
        duration_ms = (datetime.now() - self.start_time).total_seconds() * 1000
        
        log_data = {
            'operation': self.operation,
            'duration_ms': round(duration_ms, 2),
            'success': exc_type is None,
            **self.context
        }
        
        # Create structured log
        message = f"Performance: {self.operation} completed in {duration_ms:.2f}ms"
        
        # Use logger's _log method to add custom attributes
        record = self.logger.makeRecord(
            self.logger.name,
            logging.INFO,
            "",
            0,
            message,
            (),
            None
        )
        record.extra_data = log_data
        self.logger.handle(record)


class RequestLogger:
    """
    Logger for HTTP requests with structured data
    """
    
    def __init__(self, logger: logging.Logger):
        """
        Initialize request logger
        
        Args:
            logger: Logger instance
        """
        self.logger = logger
    
    def log_request(self,
                    method: str,
                    path: str,
                    status_code: int,
                    duration_ms: float,
                    **kwargs):
        """
        Log HTTP request
        
        Args:
            method: HTTP method
            path: Request path
            status_code: Response status code
            duration_ms: Request duration in milliseconds
            **kwargs: Additional context
        """
        log_data = {
            'type': 'http_request',
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': round(duration_ms, 2),
            **kwargs
        }
        
        level = logging.INFO if 200 <= status_code < 400 else logging.WARNING
        message = f"{method} {path} {status_code} {duration_ms:.2f}ms"
        
        record = self.logger.makeRecord(
            self.logger.name,
            level,
            "",
            0,
            message,
            (),
            None
        )
        record.extra_data = log_data
        self.logger.handle(record)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logger = setup_logging(
        log_level='DEBUG',
        console_output=True,
        json_format=False
    )
    
    # Get module logger
    test_logger = get_logger(__name__)
    
    # Test different log levels
    test_logger.debug("This is a debug message")
    test_logger.info("This is an info message")
    test_logger.warning("This is a warning message")
    test_logger.error("This is an error message")
    test_logger.critical("This is a critical message")
    
    # Test performance logging
    print("\nTesting performance logging:")
    with PerformanceLogger(test_logger, "search_query", query="python", results=42):
        import time
        time.sleep(0.1)  # Simulate work
    
    # Test exception logging
    print("\nTesting exception logging:")
    try:
        raise ValueError("This is a test exception")
    except Exception:
        test_logger.exception("An error occurred during processing")
    
    # Test request logging
    print("\nTesting request logging:")
    request_logger = RequestLogger(test_logger)
    request_logger.log_request(
        method="GET",
        path="/search",
        status_code=200,
        duration_ms=45.2,
        user_ip="192.168.1.1",
        query="python tutorial"
    )
    
    print(f"\nLogs written to: logs/")
    print("  - search-engine.log (all logs)")
    print("  - error.log (errors only)")
    print("  - performance.log (performance metrics)")

# Create global logger instance on import
logger = setup_logging(
    log_level='INFO',
    console_output=True,
    json_format=False
)
