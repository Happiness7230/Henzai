"""
Hybrid Search Manager
Orchestrates searches across local index and external APIs (Google + SerpAPI)
Includes full normalization, blending, and fallback support
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
    Manages search operations across multiple sources (local + SerpAPI + Google).
    Handles result blending, deduplication, re-ranking, and normalization.
    """
    
    def __init__(
        self,
        google_client=None,
        local_ranker=None,
        serpapi_client=None,
        cache_manager=None,
        mode: str = "hybrid",
    ):
        """
        Initialize Search Manager.
        
        Args:
            google_client: Google Search client instance
            local_ranker: Local ranking engine instance
            serpapi_client: SerpAPI client instance
            cache_manager: Cache manager instance
            mode: Search mode ('local', 'serpapi', 'google', 'hybrid')
        """
        self.google_client = google_client
        self.local_ranker = local_ranker
        self.serpapi_client = serpapi_client
        self.cache_manager = cache_manager
        self.mode = mode 

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
            'google_searches': 0,
            'hybrid_searches': 0,
            'cache_hits': 0,
            'avg_response_time': 0
        }
        
        logger.info(f"Search Manager initialized in '{self.mode}' mode")
    
    def search(
        self,
        query: str,
        max_results: int = None,
        filters: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute search based on configured mode.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters to apply
            **kwargs: Additional search parameters (safe_search, region, time_period, etc.)
            
        Returns:
            Unified search results dictionary with normalized structure
        """
        if max_results is None:
            from src.config.config import Config
            max_results = Config.DEFAULT_MAX_RESULTS

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
            
            elif self.mode == 'google':
                results = self._search_google(query, max_results, filters, **kwargs)
                self.stats['google_searches'] += 1
                
            elif self.mode == 'hybrid':
                results = self._search_hybrid(query, max_results, filters, **kwargs)
                self.stats['hybrid_searches'] += 1
                
            else:
                raise ValueError(f"Invalid search mode: {self.mode}")
            
            # CRITICAL: Normalize the response structure
            # This ensures 'organic_results' becomes 'results' and all keys exist
            results = self._normalize_response(results)
            
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
            logger.error(f"Search failed: {str(e)}", exc_info=True)
            # Return empty results on error
            return self._empty_results(query, str(e))
    
    def _search_local(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict]
    ) -> Dict[str, Any]:
        """
        Search using local index only.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters
            
        Returns:
            Dictionary with search results
        """
        if not self.local_ranker:
            raise ValueError("Local ranker not configured")
        
        logger.debug(f"Performing local search: '{query}'")
        
        # Execute local search (rank() only accepts query and top_k)
        local_results = self.local_ranker.rank(query, top_k=max_results)
        
        # Normalize local results using existing method
        normalized_results = self._normalize_local_results(local_results)
        
        return {
            'query': query,
            'results': normalized_results,
            'total': len(normalized_results),
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
        """
        Search using SerpAPI only.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with search results
        """
        if not self.serpapi_client:
            raise ValueError("SerpAPI client not configured")
        
        logger.debug(f"Performing SerpAPI search: '{query}'")
        
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
    
    def _search_google(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search using Google Custom Search API.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with normalized search results
        """
        if not self.google_client:
            raise ValueError("Google client not configured")

        logger.debug(f"Performing Google search: '{query}'")

        # Convert time period if provided
        date_restrict = self._convert_time_period(kwargs.get('time_period'))

        # Call Google client
        google_results = self.google_client.search(
            query=query,
            max_results=max_results or 10,
            safe_search=kwargs.get('safe_search', True),
            date_restrict=date_restrict,
            site_search=kwargs.get('site_search'),
            file_type=kwargs.get('file_type'),
            language=kwargs.get('language', 'en')
        )

        # Ensure normalized structure
        return {
            'query': query,
            'results': google_results.get('organic_results', []) if isinstance(google_results, dict) else [],
            'total': len(google_results.get('organic_results', [])) if isinstance(google_results, dict) else 0,
            'answer_box': google_results.get('answer_box') if isinstance(google_results, dict) else None,
            'knowledge_graph': google_results.get('knowledge_graph') if isinstance(google_results, dict) else None,
            'related_searches': google_results.get('related_searches', []) if isinstance(google_results, dict) else [],
            'metadata': google_results.get('metadata', {}) if isinstance(google_results, dict) else {}
        }
    
    def _search_hybrid(
        self,
        query: str,
        max_results: int,
        filters: Optional[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search using both local and APIs (Google + SerpAPI), blend results.
        Executes searches in parallel for better performance.
        
        Args:
            query: Search query
            max_results: Maximum results to return
            filters: Optional filters
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with blended search results from all sources
        """
        logger.debug(f"Performing hybrid search: '{query}'")
        
        local_results = []
        google_results = {}
        serpapi_results = {}
        all_api_results = []
        answer_box = None
        knowledge_graph = None
        related_searches = []
        
        # Execute searches in parallel (local + Google + SerpAPI)
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            
            # Submit local search
            if self.local_ranker:
                futures['local'] = executor.submit(
                    self._search_local, query, max_results, filters
                )
            
            # Submit Google search
            if self.google_client:
                futures['google'] = executor.submit(
                    self._search_google, query, max_results, filters, **kwargs
                )
            
            # Submit SerpAPI search
            if self.serpapi_client:
                futures['serpapi'] = executor.submit(
                    self._search_api, query, max_results, filters, **kwargs
                )
            
            # Collect results from all futures
            for source, future in futures.items():
                try:
                    result = future.result(timeout=10)
                    if source == 'local':
                        local_results = result.get('results', [])
                    elif source == 'google':
                        google_results = result
                        all_api_results.extend(result.get('results', []))
                        answer_box = answer_box or result.get('answer_box')
                        knowledge_graph = knowledge_graph or result.get('knowledge_graph')
                        related_searches = related_searches or result.get('related_searches', [])
                    elif source == 'serpapi':
                        serpapi_results = result
                        all_api_results.extend(result.get('results', []))
                        answer_box = answer_box or result.get('answer_box')
                        knowledge_graph = knowledge_graph or result.get('knowledge_graph')
                        related_searches = related_searches or result.get('related_searches', [])
                except Exception as e:
                    logger.warning(f"{source} search failed in hybrid mode: {str(e)}")
        
        # If both sources failed to produce results, try a direct local fallback
        if (not local_results or len(local_results) == 0) and self.local_ranker:
            try:
                logger.debug("Hybrid: local results empty, attempting direct local fallback")
                local_fallback = self._search_local(query, max_results, filters)
                local_results = local_fallback.get('results', []) or []
            except Exception as e:
                logger.warning(f"Local fallback failed in hybrid mode: {str(e)}")

        # Blend results from all sources
        blended = self._blend_results(
            local_results,
            all_api_results,
            max_results
        )
        
        return {
            'query': query,
            'results': blended,
            'total': len(blended),
            'answer_box': answer_box,
            'knowledge_graph': knowledge_graph,
            'related_searches': related_searches,
            'metadata': {
                'source': 'hybrid',
                'local_count': len(local_results),
                'google_count': len(google_results.get('results', [])),
                'serpapi_count': len(serpapi_results.get('results', [])),
                'api_count': len(all_api_results),
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
            api_results: Results from SerpAPI or Google
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
            position_score = 1.0 - (i / len(api_results)) if api_results else 1.0
            score = position_score * self.freshness_boost
            
            result['score'] = score
            result['source'] = result.get('source', 'api')
            result['blend_position'] = i
            scored_results.append(result)
        
        # Sort by score
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Guard max_results
        try:
            m = int(max_results) if max_results else None
        except Exception:
            m = None

        if not m or m <= 0:
            # Respect a sane default
            from src.config.config import Config
            m = getattr(Config, 'DEFAULT_MAX_RESULTS', 10)

        # Return top results
        return scored_results[:m]
    
    def _normalize_local_results(self, results: List[Dict]) -> List[Dict]:
        """
        Normalize local results to match API format.
        
        Supports multiple input formats:
        - dict-like results with keys (title, url, snippet, score)
        - tuple/list results from rankers: (doc_id, score)
        - other formats (stringified)
        
        Args:
            results: Raw local search results
            
        Returns:
            List of normalized result dictionaries
        """
        normalized = []
        for result in results:
            # Support two local result formats:
            # 1) dict-like results with keys (title, url, snippet, score)
            # 2) tuple/list results from rankers: (doc_id, score)
            if isinstance(result, (list, tuple)) and len(result) >= 2:
                doc_id, score = result[0], result[1]
                normalized.append({
                    'title': str(doc_id),
                    'url': str(doc_id),
                    'snippet': '',
                    'domain': self._extract_domain(str(doc_id)),
                    'score': float(score),
                    'source': 'local'
                })
            elif isinstance(result, dict):
                normalized.append({
                    'title': result.get('title', 'Untitled'),
                    'url': result.get('url', ''),
                    'snippet': result.get('snippet', ''),
                    'domain': self._extract_domain(result.get('url', '')),
                    'score': result.get('score', 0),
                    'source': 'local'
                })
            else:
                # Fallback: stringify the result
                normalized.append({
                    'title': str(result),
                    'url': str(result),
                    'snippet': '',
                    'domain': self._extract_domain(str(result)),
                    'score': 0,
                    'source': 'local'
                })
        return normalized
    
    def _normalize_response(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure response has consistent structure for frontend.
        
        This method handles the following normalizations:
        1. Converts 'organic_results' key to 'results' (for Google/SerpAPI responses)
        2. Ensures all required keys exist (results, metadata, total, etc.)
        3. Maintains backward compatibility with existing code
        
        Args:
            results: Raw search results from any search method
            
        Returns:
            Normalized results dictionary with consistent structure
        """
        # If results already has 'results' key, ensure it's valid
        if 'results' in results:
            # Make sure it's a list
            if not isinstance(results['results'], list):
                results['results'] = []
            return self._ensure_metadata(results)
        
        # If it has 'organic_results', rename it to 'results'
        if 'organic_results' in results:
            results['results'] = results.pop('organic_results')
            return self._ensure_metadata(results)
        
        # If no results key at all, create empty results
        results['results'] = []
        return self._ensure_metadata(results)

    def _ensure_metadata(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all required metadata keys exist in the response.
        
        Args:
            results: Results dictionary
            
        Returns:
            Results with complete metadata
        """
        # Ensure metadata exists
        if 'metadata' not in results:
            results['metadata'] = {}
        
        # Ensure total exists
        if 'total' not in results:
            results['total'] = len(results.get('results', []))
        
        # Ensure query exists
        if 'query' not in results:
            results['query'] = ''
        
        # Ensure optional fields have default values
        if 'answer_box' not in results:
            results['answer_box'] = None
        
        if 'knowledge_graph' not in results:
            results['knowledge_graph'] = None
        
        if 'related_searches' not in results:
            results['related_searches'] = []
        
        return results
    
    def get_suggestions(self, query: str, max_suggestions: int = 10) -> List[str]:
        """
        Get autocomplete suggestions.
        Tries multiple sources in order of preference, falls back gracefully.
        
        Priority order:
        1. Google (if in google/hybrid mode)
        2. SerpAPI (if in serpapi/hybrid mode)
        3. Local (future implementation)
        
        Args:
            query: Partial search query
            max_suggestions: Maximum number of suggestions to return
            
        Returns:
            List of suggestion strings
        """
        # Try Google first if available and in appropriate mode
        if self.google_client and self.mode in ['google', 'hybrid']:
            try:
                suggestions = self.google_client.get_suggestions(query, max_suggestions)
                if suggestions:
                    logger.debug(f"Got {len(suggestions)} suggestions from Google")
                    return suggestions
            except Exception as e:
                logger.warning(f"Google suggestions failed: {str(e)}")
        
        # Try SerpAPI if available
        if self.serpapi_client and self.mode in ['serpapi', 'hybrid']:
            try:
                suggestions = self.serpapi_client.get_suggestions(query, max_suggestions)
                if suggestions:
                    logger.debug(f"Got {len(suggestions)} suggestions from SerpAPI")
                    return suggestions
            except Exception as e:
                logger.warning(f"SerpAPI suggestions failed: {str(e)}")
        
        # Fallback to local suggestions (could be implemented in the future)
        logger.debug("No suggestions available from any source")
        return []
    
    def set_mode(self, mode: str) -> bool:
        """
        Change search mode at runtime.
        
        Args:
            mode: New search mode ('local', 'serpapi', 'google', 'hybrid')
            
        Returns:
            True if mode changed successfully, False otherwise
        """
        valid_modes = ['local', 'serpapi', 'google', 'hybrid']
        if mode not in valid_modes:
            logger.error(f"Invalid mode: {mode}. Valid modes: {valid_modes}")
            return False
        
        old_mode = self.mode
        self.mode = mode
        logger.info(f"Search mode changed from '{old_mode}' to '{mode}'")
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get search statistics.
        
        Returns:
            Dictionary with statistics including cache hit rate
        """
        return {
            **self.stats,
            'mode': self.mode,
            'blend_ratio': self.blend_ratio,
            'cache_hit_rate': (
                self.stats['cache_hits'] / self.stats['total_searches'] * 100
                if self.stats['total_searches'] > 0 else 0
            )
        }
    
    def search_with_fallback(self, query: str, **kwargs) -> Dict[str, Any]:
        """
        Search with automatic fallback between Google and SerpAPI.
        Uses configuration to determine primary and fallback engines.
        
        Args:
            query: Search query
            **kwargs: Additional search parameters
            
        Returns:
            Search results from primary or fallback engine
        """
        from src.config.config import Config
        from src.external.google_search_client import GoogleSearchException

        primary = Config.PRIMARY_SEARCH_ENGINE
        fallback = Config.FALLBACK_SEARCH_ENGINE

        max_results = kwargs.get('max_results', 10)
        filters = kwargs.get('filters')

        # Try primary engine
        try:
            if primary == 'google' and self.google_client:
                logger.info(f"Using primary search engine: {primary}")
                return self._search_google(query, max_results, filters, **kwargs)
            elif primary == 'serpapi' and self.serpapi_client:
                logger.info(f"Using primary search engine: {primary}")
                return self._search_api(query, max_results, filters, **kwargs)
        except (GoogleSearchException, Exception) as e:
            logger.warning(f"Primary search engine ({primary}) failed: {str(e)}, switching to fallback: {fallback}")

            # Try fallback engine
            try:
                if fallback == 'google' and self.google_client:
                    logger.info(f"Using fallback search engine: {fallback}")
                    return self._search_google(query, max_results, filters, **kwargs)
                elif fallback == 'serpapi' and self.serpapi_client:
                    logger.info(f"Using fallback search engine: {fallback}")
                    return self._search_api(query, max_results, filters, **kwargs)
            except Exception as e:
                logger.error(f"Fallback search engine ({fallback}) also failed: {str(e)}")

        # Both engines failed
        return self._empty_results(query, "All search engines failed")
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """
        Extract domain from URL.
        
        Args:
            url: Full URL string
            
        Returns:
            Domain name (e.g., 'example.com')
        """
        try:
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ''
    
    @staticmethod
    def _generate_cache_key(query: str, filters: Optional[Dict]) -> str:
        """
        Generate cache key for query.
        
        Args:
            query: Search query
            filters: Optional filters
            
        Returns:
            MD5 hash-based cache key
        """
        import hashlib
        key_parts = [query]
        if filters:
            key_parts.append(str(sorted(filters.items())))
        key_string = '|'.join(key_parts)
        return f"search:{hashlib.md5(key_string.encode()).hexdigest()}"
    
    def _update_stats(self, response_time: float):
        """
        Update running statistics with new response time.
        
        Args:
            response_time: Response time in seconds
        """
        total = self.stats['total_searches']
        current_avg = self.stats['avg_response_time']
        self.stats['avg_response_time'] = (
            (current_avg * (total - 1) + response_time) / total
        )
    
    @staticmethod
    def _empty_results(query: str, error: str = '') -> Dict[str, Any]:
        """
        Return empty results structure for error cases.
        
        Args:
            query: Original search query
            error: Error message
            
        Returns:
            Empty results dictionary
        """
        return {
            'query': query,
            'results': [],
            'total': 0,
            'answer_box': None,
            'knowledge_graph': None,
            'related_searches': [],
            'metadata': {
                'source': 'error',
                'error': error,
                'timestamp': datetime.now().isoformat()
            }
        }
    
    @staticmethod
    def _convert_time_period(time_period: Optional[str]) -> Optional[str]:
        """
        Convert time period to Google Custom Search format.
        
        Args:
            time_period: Time period code ('d', 'w', 'm', 'y')
            
        Returns:
            Google API format ('d1', 'w1', 'm1', 'y1') or None
        """
        if not time_period:
            return None
        mapping = {
            'd': 'd1',  # Past day
            'w': 'w1',  # Past week
            'm': 'm1',  # Past month
            'y': 'y1'   # Past year
        }
        return mapping.get(time_period)