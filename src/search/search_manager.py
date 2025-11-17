"""
Hybrid Search Manager
Orchestrates searches across local index and external APIs
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class SearchManager:
    """
    Manages search operations across multiple sources (local + SerpAPI).
    Handles result blending, deduplication, and re-ranking.
    """
    
    def __init__(
        self,
        local_ranker=None,
        serpapi_client=None,
        cache_manager=None,
        mode: str = 'hybrid'
    ):
        """
        Initialize Search Manager.
        
        Args:
            local_ranker: Local ranking engine instance
            serpapi_client: SerpAPI client instance
            cache_manager: Cache manager instance
            mode: Search mode ('local', 'serpapi', 'hybrid')
        """
        self.local_ranker = local_ranker
        self.serpapi_client = serpapi_client
        self.cache_manager = cache_manager
        self.mode = mode or os.getenv('SEARCH_MODE', 'hybrid')
        
        # Configuration
        self.blend_ratio = float(os.getenv('HYBRID_BLEND_RATIO', 0.5))
        self.local_boost = float(os.getenv('HYBRID_LOCAL_BOOST', 1.2))
        self.freshness_boost = float(os.getenv('HYBRID_FRESHNESS_BOOST', 1.1))
        self.deduplicate = os.getenv('HYBRID_DEDUPLICATE', 'true').lower() == 'true'
        
        # Statistics
        self.stats = {
            'total_searches': 0,
            'local_searches': 0,
            'api_searches': 0,
            'hybrid_searches': 0,
            'cache_hits': 0,
            'avg_response_time': 0
        }
        
        logger.info(f"Search Manager initialized in '{self.mode}' mode")
    
    def search(
        self,
        query: str,
        max_results: int = 10,
        filters: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute search based on configured mode.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters to apply
            **kwargs: Additional search parameters
            
        Returns:
            Unified search results dictionary
        """
        start_time = datetime.now()
        self.stats['total_searches'] += 1
        
        # Check cache first
        cache_key = self._generate_cache_key(query, filters)
        if self.cache_manager:
            cached = self.cache_manager.get(cache_key)
            if cached:
                self.stats['cache_hits'] += 1
                logger.info(f"Cache hit for query: '{query}'")
                return cached
        
        try:
            # Route to appropriate search method
            if self.mode == 'local':
                results = self._search_local(query, max_results, filters)
                self.stats['local_searches'] += 1
                
            elif self.mode == 'serpapi':
                results = self._search_api(query, max_results, filters, **kwargs)
                self.stats['api_searches'] += 1
                
            elif self.mode == 'hybrid':
                results = self._search_hybrid(query, max_results, filters, **kwargs)
                self.stats['hybrid_searches'] += 1
                
            else:
                raise ValueError(f"Invalid search mode: {self.mode}")
            
            # Add metadata
            response_time = (datetime.now() - start_time).total_seconds()
            results['metadata']['response_time'] = response_time
            results['metadata']['mode'] = self.mode
            results['metadata']['timestamp'] = datetime.now().isoformat()
            
            # Update stats
            self._update_stats(response_time)
            
            # Cache results
            if self.cache_manager:
                ttl = int(os.getenv('CACHE_TTL_SEARCH', 3600))
                self.cache_manager.set(cache_key, results, ttl)
            
            logger.info(
                f"Search completed: query='{query}', mode={self.mode}, "
                f"results={len(results['results'])}, time={response_time:.3f}s"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            # Return empty results on error
            return self._empty_results(query, str(e))
    
    def _search_local(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict]
    ) -> Dict[str, Any]:
        """Search using local index only."""
        if not self.local_ranker:
            raise ValueError("Local ranker not configured")
        
        logger.debug(f"Performing local search: '{query}'")
        
        # Execute local search
        local_results = self.local_ranker.rank(query, max_results, filters)
        
        return {
            'query': query,
            'results': self._normalize_local_results(local_results),
            'total': len(local_results),
            'metadata': {
                'source': 'local',
                'search_time': 0
            }
        }
    
    def _search_api(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """Search using SerpAPI only."""
        if not self.serpapi_client:
            raise ValueError("SerpAPI client not configured")
        
        logger.debug(f"Performing API search: '{query}'")
        
        # Execute API search
        api_results = self.serpapi_client.search(
            query=query,
            max_results=max_results,
            safe_search=kwargs.get('safe_search', True),
            region=kwargs.get('region', 'wt-wt'),
            time_period=kwargs.get('time_period')
        )
        
        return {
            'query': query,
            'results': api_results.get('organic_results', []),
            'total': len(api_results.get('organic_results', [])),
            'answer_box': api_results.get('answer_box'),
            'knowledge_graph': api_results.get('knowledge_graph'),
            'related_searches': api_results.get('related_searches', []),
            'metadata': api_results.get('metadata', {})
        }
    
    def _search_hybrid(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search using both local and API, blend results.
        Executes searches in parallel for better performance.
        """
        logger.debug(f"Performing hybrid search: '{query}'")
        
        local_results = []
        api_results = {}
        
        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            
            # Submit local search
            if self.local_ranker:
                futures['local'] = executor.submit(
                    self._search_local, query, max_results, filters
                )
            
            # Submit API search
            if self.serpapi_client:
                futures['api'] = executor.submit(
                    self._search_api, query, max_results, filters, **kwargs
                )
            
            # Collect results
            for source, future in futures.items():
                try:
                    result = future.result(timeout=10)
                    if source == 'local':
                        local_results = result.get('results', [])
                    else:
                        api_results = result
                except Exception as e:
                    logger.warning(f"{source} search failed in hybrid mode: {str(e)}")
        
        # Blend results
        blended = self._blend_results(
            local_results,
            api_results.get('results', []),
            max_results
        )
        
        return {
            'query': query,
            'results': blended,
            'total': len(blended),
            'answer_box': api_results.get('answer_box'),
            'knowledge_graph': api_results.get('knowledge_graph'),
            'related_searches': api_results.get('related_searches', []),
            'metadata': {
                'source': 'hybrid',
                'local_count': len(local_results),
                'api_count': len(api_results.get('results', [])),
                'blended_count': len(blended)
            }
        }
    
    def _blend_results(
        self,
        local_results: List[Dict],
        api_results: List[Dict],
        max_results: int
    ) -> List[Dict]:
        """
        Blend local and API results with scoring and deduplication.
        
        Args:
            local_results: Results from local index
            api_results: Results from SerpAPI
            max_results: Maximum results to return
            
        Returns:
            Blended and scored result list
        """
        # Score and tag results
        scored_results = []
        seen_domains = set()
        
        # Process local results
        for i, result in enumerate(local_results):
            score = result.get('score', 1.0) * self.local_boost
            result['score'] = score
            result['source'] = 'local'
            result['blend_position'] = i
            scored_results.append(result)
            
            if self.deduplicate:
                domain = self._extract_domain(result.get('url', ''))
                if domain:
                    seen_domains.add(domain)
        
        # Process API results
        for i, result in enumerate(api_results):
            # Check for duplicates
            if self.deduplicate:
                domain = self._extract_domain(result.get('url', ''))
                if domain in seen_domains:
                    continue
                if domain:
                    seen_domains.add(domain)
            
            # Score based on position and freshness
            position_score = 1.0 - (i / len(api_results))
            score = position_score * self.freshness_boost
            
            result['score'] = score
            result['source'] = result.get('source', 'serpapi')
            result['blend_position'] = i
            scored_results.append(result)
        
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top results
        return scored_results[:max_results]
    
    def _normalize_local_results(self, results: List[Dict]) -> List[Dict]:
        """Normalize local results to match API format."""
        normalized = []
        for result in results:
            normalized.append({
                'title': result.get('title', 'Untitled'),
                'url': result.get('url', ''),
                'snippet': result.get('snippet', ''),
                'domain': self._extract_domain(result.get('url', '')),
                'score': result.get('score', 0),
                'source': 'local'
            })
        return normalized
    
    def get_suggestions(self, query: str, max_suggestions: int = 10) -> List[str]:
        """
        Get autocomplete suggestions.
        Falls back to local if API fails.
        """
        # Try API first if available
        if self.serpapi_client and self.mode in ['serpapi', 'hybrid']:
            try:
                suggestions = self.serpapi_client.get_suggestions(query, max_suggestions)
                if suggestions:
                    return suggestions
            except Exception as e:
                logger.warning(f"API suggestions failed: {str(e)}")
        
        # Fallback to local suggestions (could be implemented)
        # For now, return empty list
        return []
    
    def set_mode(self, mode: str) -> bool:
        """
        Change search mode at runtime.
        
        Args:
            mode: New search mode ('local', 'serpapi', 'hybrid')
            
        Returns:
            True if mode changed successfully
        """
        valid_modes = ['local', 'serpapi', 'hybrid']
        if mode not in valid_modes:
            logger.error(f"Invalid mode: {mode}")
            return False
        
        self.mode = mode
        logger.info(f"Search mode changed to: {mode}")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        return {
            **self.stats,
            'mode': self.mode,
            'blend_ratio': self.blend_ratio,
            'cache_hit_rate': (
                self.stats['cache_hits'] / self.stats['total_searches'] * 100
                if self.stats['total_searches'] > 0 else 0
            )
        }
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ''
    
    @staticmethod
    def _generate_cache_key(query: str, filters: Optional[Dict]) -> str:
        """Generate cache key for query."""
        import hashlib
        key_parts = [query]
        if filters:
            key_parts.append(str(sorted(filters.items())))
        key_string = '|'.join(key_parts)
        return f"search:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _update_stats(self, response_time: float):
        """Update running statistics."""
        total = self.stats['total_searches']
        current_avg = self.stats['avg_response_time']
        self.stats['avg_response_time'] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    @staticmethod
    def _empty_results(query: str, error: str = '') -> Dict[str, Any]:
        """Return empty results structure."""
        return {
            'query': query,
            'results': [],
            'total': 0,
            'metadata': {
                'source': 'error',
                'error': error,
                'timestamp': datetime.now().isoformat()
            }
        }
    
def search_with_fallback(self, query: str, **kwargs) -> Dict[str, Any]:
    """
    Search with automatic fallback between Google and SerpAPI.
    """
    from src.config.config import Config
    from src.external.google_search_client import GoogleSearchException
    
    primary = Config.PRIMARY_SEARCH_ENGINE
    fallback = Config.FALLBACK_SEARCH_ENGINE
    
    # Try primary engine
    try:
        if primary == 'google' and self.google_client:
            logger.info("Using Google as primary search engine")
            return self._search_google(query, **kwargs)
        elif primary == 'serpapi' and self.serpapi_client:
            logger.info("Using SerpAPI as primary search engine")
            return self._search_api(query, **kwargs)
    except (GoogleSearchException, Exception) as e:
        logger.warning(f"Primary search engine ({primary}) failed: {str(e)}")
        logger.info(f"Falling back to {fallback}")
        
        # Try fallback
        try:
            if fallback == 'google' and self.google_client:
                return self._search_google(query, **kwargs)
            elif fallback == 'serpapi' and self.serpapi_client:
                return self._search_api(query, **kwargs)
        except Exception as e2:
            logger.error(f"Fallback search engine ({fallback}) also failed: {str(e2)}")
            if self.local_ranker:
                return self._search_local(query, kwargs.get('max_results', 10), None)
    
    return self._empty_results(query, "All search engines failed")

def _search_google(self, query: str, **kwargs) -> Dict[str, Any]:
    """Search using Google Custom Search API"""
    if not self.google_client:
        raise ValueError("Google client not configured")
    
    results = self.google_client.search(
        query=query,
        max_results=kwargs.get('max_results', 10),
        safe_search=kwargs.get('safe_search', True),
        date_restrict=self._convert_time_period(kwargs.get('time_period')),
        site_search=kwargs.get('site_search'),
        file_type=kwargs.get('file_type')
    )
    
    return {
        'query': query,
        'results': results.get('organic_results', []),
        'total': len(results.get('organic_results', [])),
        'answer_box': results.get('answer_box'),
        'knowledge_graph': results.get('knowledge_graph'),
        'related_searches': results.get('related_searches', []),
        'metadata': results.get('metadata', {})
    }

@staticmethod
def _convert_time_period(time_period: Optional[str]) -> Optional[str]:
    """Convert time period to Google format"""
    if not time_period:
        return None
    mapping = {
        'd': 'd1',
        'w': 'w1',
        'm': 'm1',
        'y': 'y1'
    }
    return mapping.get(time_period)