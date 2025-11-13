"""
Analytics Store - Track search queries and usage patterns
"""

import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict, Counter


class AnalyticsStore:
    """
    Track and analyze search queries and user behavior
    """
    
    def __init__(self, filepath: str = 'data/analytics.json'):
        """
        Initialize analytics store
        
        Args:
            filepath: Path to analytics JSON file
        """
        self.filepath = filepath
        self.lock = threading.Lock()
        
        # In-memory analytics data
        self.query_counts: Counter = Counter()  # query -> count
        self.query_timestamps: Dict[str, List[str]] = defaultdict(list)  # query -> [timestamps]
        self.recent_queries: List[Dict] = []  # Recent query history
        self.total_searches: int = 0
        self.failed_searches: int = 0  # Searches with 0 results
        
        # Performance tracking
        self.search_times: List[float] = []  # Search execution times
        
        self._ensure_directory()
        self._load()
    
    def _ensure_directory(self) -> None:
        """Create directory if it doesn't exist"""
        directory = os.path.dirname(self.filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    def _load(self) -> None:
        """Load analytics from file"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.query_counts = Counter(data.get('query_counts', {}))
                self.query_timestamps = defaultdict(list, data.get('query_timestamps', {}))
                self.recent_queries = data.get('recent_queries', [])
                self.total_searches = data.get('total_searches', 0)
                self.failed_searches = data.get('failed_searches', 0)
                self.search_times = data.get('search_times', [])
                
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not parse analytics file: {e}")
    
    def _save(self) -> None:
        """Save analytics to file"""
        temp_filepath = self.filepath + '.tmp'
        
        try:
            data = {
                'query_counts': dict(self.query_counts),
                'query_timestamps': dict(self.query_timestamps),
                'recent_queries': self.recent_queries[-1000:],  # Keep last 1000
                'total_searches': self.total_searches,
                'failed_searches': self.failed_searches,
                'search_times': self.search_times[-1000:],  # Keep last 1000
                'last_updated': datetime.now().isoformat()
            }
            
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            os.replace(temp_filepath, self.filepath)
            
        except Exception as e:
            print(f"Error saving analytics: {e}")
            if os.path.exists(temp_filepath):
                os.remove(temp_filepath)
    
    def log_search(self, query: str, result_count: int, 
                   search_time: float, user_agent: Optional[str] = None) -> None:
        """
        Log a search query
        
        Args:
            query: Search query string
            result_count: Number of results returned
            search_time: Time taken to execute search (seconds)
            user_agent: User agent string (optional)
        """
        with self.lock:
            # Normalize query
            query = query.strip().lower()
            
            if not query:
                return
            
            # Update counters
            self.query_counts[query] += 1
            self.total_searches += 1
            
            if result_count == 0:
                self.failed_searches += 1
            
            # Track timestamp
            timestamp = datetime.now().isoformat()
            self.query_timestamps[query].append(timestamp)
            
            # Track search time
            self.search_times.append(search_time)
            
            # Add to recent queries (keep last 100)
            self.recent_queries.append({
                'query': query,
                'result_count': result_count,
                'search_time': search_time,
                'timestamp': timestamp,
                'user_agent': user_agent
            })
            
            # Keep only last 100 recent queries
            if len(self.recent_queries) > 100:
                self.recent_queries = self.recent_queries[-100:]
            
            # Save periodically (every 10 searches)
            if self.total_searches % 10 == 0:
                self._save()
    
    def get_popular_queries(self, limit: int = 10, 
                           time_window: Optional[timedelta] = None) -> List[Dict]:
        """
        Get most popular queries
        
        Args:
            limit: Number of queries to return
            time_window: Optional time window (e.g., last 24 hours)
            
        Returns:
            List of {query, count} dictionaries
        """
        with self.lock:
            if time_window:
                # Filter by time window
                cutoff = datetime.now() - time_window
                filtered_counts = Counter()
                
                for query, timestamps in self.query_timestamps.items():
                    recent_count = sum(
                        1 for ts in timestamps
                        if datetime.fromisoformat(ts) > cutoff
                    )
                    if recent_count > 0:
                        filtered_counts[query] = recent_count
                
                top_queries = filtered_counts.most_common(limit)
            else:
                top_queries = self.query_counts.most_common(limit)
            
            return [
                {'query': query, 'count': count}
                for query, count in top_queries
            ]
    
    def get_failed_queries(self, limit: int = 10) -> List[Dict]:
        """
        Get queries that returned no results
        
        Args:
            limit: Number of queries to return
            
        Returns:
            List of failed queries
        """
        with self.lock:
            failed = [
                q for q in self.recent_queries
                if q['result_count'] == 0
            ]
            
            # Get unique queries
            unique_failed = {}
            for q in reversed(failed):  # Most recent first
                if q['query'] not in unique_failed:
                    unique_failed[q['query']] = q
                if len(unique_failed) >= limit:
                    break
            
            return list(unique_failed.values())
    
    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """
        Get recent search queries
        
        Args:
            limit: Number of queries to return
            
        Returns:
            List of recent searches
        """
        with self.lock:
            return self.recent_queries[-limit:][::-1]  # Most recent first
    
    def get_query_suggestions(self, prefix: str, limit: int = 5) -> List[str]:
        """
        Get query suggestions based on prefix
        
        Args:
            prefix: Query prefix to match
            limit: Number of suggestions
            
        Returns:
            List of suggested queries
        """
        with self.lock:
            prefix = prefix.lower().strip()
            
            if not prefix:
                # Return popular queries if no prefix
                return [q['query'] for q in self.get_popular_queries(limit)]
            
            # Find queries starting with prefix
            matching = [
                (query, count) for query, count in self.query_counts.items()
                if query.startswith(prefix)
            ]
            
            # Sort by count (popularity)
            matching.sort(key=lambda x: x[1], reverse=True)
            
            return [query for query, _ in matching[:limit]]
    
    def get_search_trends(self, days: int = 7) -> Dict:
        """
        Get search trends over time
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with trend data
        """
        with self.lock:
            cutoff = datetime.now() - timedelta(days=days)
            
            # Count searches per day
            daily_counts = defaultdict(int)
            
            for query in self.recent_queries:
                timestamp = datetime.fromisoformat(query['timestamp'])
                if timestamp > cutoff:
                    date_key = timestamp.strftime('%Y-%m-%d')
                    daily_counts[date_key] += 1
            
            # Sort by date
            sorted_dates = sorted(daily_counts.items())
            
            return {
                'period_days': days,
                'daily_searches': [
                    {'date': date, 'count': count}
                    for date, count in sorted_dates
                ],
                'total_searches': sum(daily_counts.values()),
                'average_per_day': sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0
            }
    
    def get_statistics(self) -> Dict:
        """
        Get overall analytics statistics
        
        Returns:
            Dictionary with analytics stats
        """
        with self.lock:
            # Calculate average search time
            avg_search_time = (
                sum(self.search_times) / len(self.search_times)
                if self.search_times else 0
            )
            
            # Calculate success rate
            success_rate = (
                ((self.total_searches - self.failed_searches) / self.total_searches * 100)
                if self.total_searches > 0 else 0
            )
            
            return {
                'total_searches': self.total_searches,
                'unique_queries': len(self.query_counts),
                'failed_searches': self.failed_searches,
                'success_rate_percent': round(success_rate, 2),
                'average_search_time_ms': round(avg_search_time * 1000, 2),
                'most_popular_query': (
                    self.query_counts.most_common(1)[0][0]
                    if self.query_counts else None
                )
            }
    
    def clear(self) -> None:
        """Clear all analytics data"""
        with self.lock:
            self.query_counts.clear()
            self.query_timestamps.clear()
            self.recent_queries.clear()
            self.total_searches = 0
            self.failed_searches = 0
            self.search_times.clear()
            self._save()
    
    def export_data(self) -> Dict:
        """
        Export all analytics data
        
        Returns:
            Complete analytics data dictionary
        """
        with self.lock:
            return {
                'statistics': self.get_statistics(),
                'popular_queries': self.get_popular_queries(20),
                'failed_queries': self.get_failed_queries(10),
                'recent_searches': self.get_recent_searches(20),
                'trends': self.get_search_trends(7)
            }