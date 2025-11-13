"""
Performance Metrics Collector
Tracks system health, performance, and usage statistics
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, deque
import statistics


class MetricsCollector:
    """
    Collect and aggregate performance metrics
    """
    
    def __init__(self, history_size: int = 1000):
        """
        Initialize metrics collector
        
        Args:
            history_size: Number of historical data points to keep
        """
        self.history_size = history_size
        self.lock = threading.Lock()
        
        # Request metrics
        self.request_count = 0
        self.request_times = deque(maxlen=history_size)
        self.requests_per_endpoint = defaultdict(int)
        
        # Search metrics
        self.search_count = 0
        self.search_times = deque(maxlen=history_size)
        self.zero_result_searches = 0
        
        # Error metrics
        self.error_count = 0
        self.errors_by_type = defaultdict(int)
        
        # System metrics history
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        
        # Start time
        self.start_time = datetime.now()
    
    def record_request(self, 
                      endpoint: str, 
                      duration_seconds: float,
                      status_code: int):
        """
        Record an HTTP request
        
        Args:
            endpoint: API endpoint
            duration_seconds: Request duration
            status_code: HTTP status code
        """
        with self.lock:
            self.request_count += 1
            self.request_times.append(duration_seconds)
            self.requests_per_endpoint[endpoint] += 1
            
            if status_code >= 400:
                self.error_count += 1
                self.errors_by_type[f"HTTP_{status_code}"] += 1
    
    def record_search(self,
                     duration_seconds: float,
                     result_count: int,
                     cache_hit: bool = False):
        """
        Record a search operation
        
        Args:
            duration_seconds: Search duration
            result_count: Number of results returned
            cache_hit: Whether result came from cache
        """
        with self.lock:
            self.search_count += 1
            self.search_times.append(duration_seconds)
            
            if result_count == 0:
                self.zero_result_searches += 1
    
    def record_error(self, error_type: str):
        """
        Record an error
        
        Args:
            error_type: Type/category of error
        """
        with self.lock:
            self.error_count += 1
            self.errors_by_type[error_type] += 1
    
    def collect_system_metrics(self):
        """Collect current system metrics"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        with self.lock:
            self.cpu_history.append(cpu_percent)
            self.memory_history.append(memory.percent)
    
    def get_percentiles(self, data: List[float]) -> Dict[str, float]:
        """
        Calculate percentiles for a dataset
        
        Args:
            data: List of values
            
        Returns:
            Dictionary with p50, p95, p99 percentiles
        """
        if not data:
            return {'p50': 0, 'p95': 0, 'p99': 0}
        
        sorted_data = sorted(data)
        return {
            'p50': statistics.median(sorted_data),
            'p95': sorted_data[int(len(sorted_data) * 0.95)] if len(sorted_data) > 1 else sorted_data[0],
            'p99': sorted_data[int(len(sorted_data) * 0.99)] if len(sorted_data) > 1 else sorted_data[0]
        }
    
    def get_metrics(self) -> Dict:
        """
        Get all collected metrics
        
        Returns:
            Dictionary with all metrics
        """
        with self.lock:
            # Calculate uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
            
            # Request metrics
            request_percentiles = self.get_percentiles(list(self.request_times))
            
            # Search metrics
            search_percentiles = self.get_percentiles(list(self.search_times))
            zero_result_rate = (
                (self.zero_result_searches / self.search_count * 100)
                if self.search_count > 0 else 0
            )
            
            # System metrics
            current_cpu = psutil.cpu_percent(interval=0)
            current_memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': round(uptime_seconds, 2),
                'requests': {
                    'total': self.request_count,
                    'per_second': round(self.request_count / uptime_seconds, 2) if uptime_seconds > 0 else 0,
                    'latency_ms': {
                        'p50': round(request_percentiles['p50'] * 1000, 2),
                        'p95': round(request_percentiles['p95'] * 1000, 2),
                        'p99': round(request_percentiles['p99'] * 1000, 2)
                    },
                    'by_endpoint': dict(self.requests_per_endpoint)
                },
                'searches': {
                    'total': self.search_count,
                    'zero_results': self.zero_result_searches,
                    'zero_result_rate_percent': round(zero_result_rate, 2),
                    'latency_ms': {
                        'p50': round(search_percentiles['p50'] * 1000, 2),
                        'p95': round(search_percentiles['p95'] * 1000, 2),
                        'p99': round(search_percentiles['p99'] * 1000, 2)
                    }
                },
                'errors': {
                    'total': self.error_count,
                    'by_type': dict(self.errors_by_type)
                },
                'system': {
                    'cpu_percent': round(current_cpu, 2),
                    'memory_percent': round(current_memory.percent, 2),
                    'memory_used_mb': round(current_memory.used / 1024 / 1024, 2),
                    'memory_available_mb': round(current_memory.available / 1024 / 1024, 2),
                    'disk_percent': round(disk.percent, 2),
                    'disk_used_gb': round(disk.used / 1024 / 1024 / 1024, 2),
                    'disk_free_gb': round(disk.free / 1024 / 1024 / 1024, 2)
                }
            }
    
    def get_prometheus_metrics(self) -> str:
        """
        Get metrics in Prometheus format
        
        Returns:
            Prometheus-formatted metrics string
        """
        metrics = self.get_metrics()
        
        lines = [
            '# HELP search_requests_total Total number of search requests',
            '# TYPE search_requests_total counter',
            f'search_requests_total {metrics["requests"]["total"]}',
            '',
            '# HELP search_latency_seconds Search latency in seconds',
            '# TYPE search_latency_seconds histogram',
            f'search_latency_seconds_bucket{{le="0.05"}} {sum(1 for t in self.search_times if t <= 0.05)}',
            f'search_latency_seconds_bucket{{le="0.1"}} {sum(1 for t in self.search_times if t <= 0.1)}',
            f'search_latency_seconds_bucket{{le="0.25"}} {sum(1 for t in self.search_times if t <= 0.25)}',
            f'search_latency_seconds_bucket{{le="0.5"}} {sum(1 for t in self.search_times if t <= 0.5)}',
            f'search_latency_seconds_bucket{{le="+Inf"}} {len(self.search_times)}',
            '',
            '# HELP system_cpu_percent CPU usage percentage',
            '# TYPE system_cpu_percent gauge',
            f'system_cpu_percent {metrics["system"]["cpu_percent"]}',
            '',
            '# HELP system_memory_percent Memory usage percentage',
            '# TYPE system_memory_percent gauge',
            f'system_memory_percent {metrics["system"]["memory_percent"]}',
            '',
            '# HELP errors_total Total number of errors',
            '# TYPE errors_total counter',
            f'errors_total {metrics["errors"]["total"]}',
        ]
        
        return '\n'.join(lines)
    
    def reset(self):
        """Reset all metrics"""
        with self.lock:
            self.request_count = 0
            self.request_times.clear()
            self.requests_per_endpoint.clear()
            self.search_count = 0
            self.search_times.clear()
            self.zero_result_searches = 0
            self.error_count = 0
            self.errors_by_type.clear()
            self.cpu_history.clear()
            self.memory_history.clear()
            self.start_time = datetime.now()


# Global metrics collector instance
metrics_collector = MetricsCollector()


# Convenience functions
def record_request(endpoint: str, duration: float, status_code: int):
    """Record HTTP request"""
    metrics_collector.record_request(endpoint, duration, status_code)


def record_search(duration: float, result_count: int, cache_hit: bool = False):
    """Record search operation"""
    metrics_collector.record_search(duration, result_count, cache_hit)


def record_error(error_type: str):
    """Record error"""
    metrics_collector.record_error(error_type)


def get_metrics() -> Dict:
    """Get all metrics"""
    return metrics_collector.get_metrics()


def get_prometheus_metrics() -> str:
    """Get Prometheus-formatted metrics"""
    return metrics_collector.get_prometheus_metrics()


# Example usage
if __name__ == "__main__":
    import random
    
    print("Testing metrics collector...")
    
    # Simulate some requests
    for i in range(100):
        endpoint = random.choice(['/search', '/status', '/analytics'])
        duration = random.uniform(0.01, 0.5)
        status = random.choice([200, 200, 200, 404, 500])
        
        metrics_collector.record_request(endpoint, duration, status)
        
        if endpoint == '/search':
            results = random.randint(0, 50)
            metrics_collector.record_search(duration, results)
    
    # Get metrics
    print("\n" + "="*60)
    print("Current Metrics:")
    print("="*60)
    
    import json
    metrics = metrics_collector.get_metrics()
    print(json.dumps(metrics, indent=2))
    
    print("\n" + "="*60)
    print("Prometheus Format:")
    print("="*60)
    print(metrics_collector.get_prometheus_metrics())