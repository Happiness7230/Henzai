"""
SerpAPI Client Module
Handles all interactions with SerpAPI (DuckDuckGo) for live web search
"""

import os
import time
import logging
from typing import Dict, List, Optional, Any
from serpapi import GoogleSearch
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from ratelimit import limits, sleep_and_retry
import requests

logger = logging.getLogger(__name__)


class SerpAPIException(Exception):
    """Custom exception for SerpAPI errors"""
    pass


class SerpAPIClient:
    """
    Client for interacting with SerpAPI using DuckDuckGo engine.
    Includes rate limiting, retry logic, and error handling.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 5):
        """
        Initialize SerpAPI client.
        
        Args:
            api_key: SerpAPI key (reads from env if not provided)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv('SERPAPI_KEY')
        if not self.api_key:
            raise ValueError("SERPAPI_KEY not found in environment variables")
        
        self.timeout = timeout
        self.base_params = {
            'api_key': self.api_key,
            'engine': 'duckduckgo',  # Using DuckDuckGo engine
            'no_cache': False  # Use SerpAPI's cache when available
        }
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'total_results_returned': 0
        }
        
        logger.info("SerpAPI client initialized with DuckDuckGo engine")
    
    @sleep_and_retry
    @limits(calls=100, period=60)  # 100 calls per minute rate limit
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, SerpAPIException))
    )
    def search(
        self,
        query: str,
        max_results: int = 10,
        safe_search: bool = True,
        region: str = 'wt-wt',  # wt-wt = worldwide
        time_period: Optional[str] = None  # 'd' (day), 'w' (week), 'm' (month), 'y' (year)
    ) -> Dict[str, Any]:
        """
        Perform web search using SerpAPI with pagination support.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (supports up to 20+)
            safe_search: Enable safe search filtering
            region: Region code (e.g., 'us-en', 'uk-en')
            time_period: Time filter for results
            
        Returns:
            Normalized search results dictionary with up to max_results
        """
        self.stats['total_requests'] += 1
        
        try:
            all_results = []
            results_per_page = 10  # SerpAPI returns 10 results per request
            num_pages = (max_results + 9) // 10  # Round up to get enough pages
            
            # Fetch multiple pages if needed to reach max_results
            for page in range(num_pages):
                start = page * results_per_page
                
                params = {
                    **self.base_params,
                    'q': query,
                    'kl': region,
                    'safe': '1' if safe_search else '-1',
                    'start': start  # SerpAPI pagination parameter
                }
                
                if time_period:
                    params['df'] = time_period
                
                logger.info(f"Executing SerpAPI search: query='{query}', page={page+1}, region={region}")
                
                search = GoogleSearch(params)
                results = search.get_dict()
                
                # Check for errors
                if 'error' in results:
                    self.stats['failed_requests'] += 1
                    raise SerpAPIException(f"SerpAPI error: {results['error']}")
                
                # Get organic results from this page
                page_results = results.get('organic_results', [])
                if not page_results:
                    break  # No more results available
                
                all_results.extend(page_results)
                
                # Stop if we have enough results
                if len(all_results) >= max_results:
                    all_results = all_results[:max_results]
                    break
            
            # Normalize and structure the response
            normalized = self._normalize_results({'organic_results': all_results}, max_results)
            
            self.stats['successful_requests'] += 1
            self.stats['total_results_returned'] += len(normalized['organic_results'])
            
            logger.info(f"SerpAPI search successful: {len(normalized['organic_results'])} results")
            
            return normalized
            
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"SerpAPI search failed: {str(e)}")
            raise SerpAPIException(f"Search failed: {str(e)}") from e
    
    def _normalize_results(self, raw_results: Dict, max_results: int) -> Dict[str, Any]:
        """
        Normalize SerpAPI results to match internal format.
        
        Args:
            raw_results: Raw results from SerpAPI
            max_results: Maximum results to include
            
        Returns:
            Normalized results dictionary
        """
        normalized = {
            'query': raw_results.get('search_parameters', {}).get('q', ''),
            'organic_results': [],
            'related_searches': [],
            'answer_box': None,
            'knowledge_graph': None,
            'metadata': {
                'total_results': 0,
                'search_time': 0,
                'source': 'serpapi',
                'engine': 'duckduckgo'
            }
        }
        
        # Process organic results
        organic = raw_results.get('organic_results', [])[:max_results]
        for result in organic:
            normalized['organic_results'].append({
                'title': result.get('title', ''),
                'url': result.get('link', ''),
                'snippet': result.get('snippet', ''),
                'domain': self._extract_domain(result.get('link', '')),
                'position': result.get('position', 0),
                'favicon': result.get('favicon'),
                'date': result.get('date'),
                'source': 'serpapi'
            })
        
        # Process answer box (featured snippet)
        if 'answer_box' in raw_results:
            normalized['answer_box'] = {
                'title': raw_results['answer_box'].get('title', ''),
                'answer': raw_results['answer_box'].get('answer', ''),
                'snippet': raw_results['answer_box'].get('snippet', ''),
                'link': raw_results['answer_box'].get('link', '')
            }
        
        # Process knowledge graph
        if 'knowledge_graph' in raw_results:
            kg = raw_results['knowledge_graph']
            normalized['knowledge_graph'] = {
                'title': kg.get('title', ''),
                'type': kg.get('type', ''),
                'description': kg.get('description', ''),
                'image': kg.get('image', ''),
                'website': kg.get('website', '')
            }
        
        # Process related searches
        related = raw_results.get('related_searches', [])
        for item in related:
            if isinstance(item, dict):
                normalized['related_searches'].append(item.get('query', ''))
            else:
                normalized['related_searches'].append(str(item))
        
        # Add metadata
        search_meta = raw_results.get('search_metadata', {})
        normalized['metadata']['search_time'] = search_meta.get('total_time_taken', 0)
        
        return normalized
    
    def get_suggestions(self, query: str, max_suggestions: int = 10) -> List[str]:
        """
        Get autocomplete suggestions for a query.
        
        Args:
            query: Partial search query
            max_suggestions: Maximum suggestions to return
            
        Returns:
            List of suggestion strings
        """
        try:
            params = {
                **self.base_params,
                'q': query,
                'engine': 'duckduckgo_suggestions'
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            suggestions = results.get('suggestions', [])[:max_suggestions]
            return [s.get('value', s) if isinstance(s, dict) else s for s in suggestions]
            
        except Exception as e:
            logger.error(f"Failed to get suggestions: {str(e)}")
            return []
    
    def search_news(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search for news articles.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            News results dictionary
        """
        try:
            params = {
                **self.base_params,
                'q': query,
                'tbm': 'nws'  # News search
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            news_results = []
            for item in results.get('news_results', [])[:max_results]:
                news_results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'source': item.get('source', ''),
                    'date': item.get('date', ''),
                    'thumbnail': item.get('thumbnail'),
                    'type': 'news'
                })
            
            return {
                'query': query,
                'results': news_results,
                'total': len(news_results)
            }
            
        except Exception as e:
            logger.error(f"News search failed: {str(e)}")
            return {'query': query, 'results': [], 'total': 0}
    
    def search_images(self, query: str, max_results: int = 20) -> Dict[str, Any]:
        """
        Search for images.
        
        Args:
            query: Search query
            max_results: Maximum results
            
        Returns:
            Image results dictionary
        """
        try:
            params = {
                **self.base_params,
                'q': query,
                'tbm': 'isch'  # Image search
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            image_results = []
            for item in results.get('images_results', [])[:max_results]:
                image_results.append({
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'thumbnail': item.get('thumbnail', ''),
                    'source': item.get('source', ''),
                    'width': item.get('original_width'),
                    'height': item.get('original_height'),
                    'type': 'image'
                })
            
            return {
                'query': query,
                'results': image_results,
                'total': len(image_results)
            }
            
        except Exception as e:
            logger.error(f"Image search failed: {str(e)}")
            return {'query': query, 'results': [], 'total': 0}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_requests'] / self.stats['total_requests'] * 100
                if self.stats['total_requests'] > 0 else 0
            )
        }
    
    @staticmethod
    def _extract_domain(url: str) -> str:
        """Extract domain from URL."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.netloc
        except:
            return ''
    
    def health_check(self) -> bool:
        """
        Perform a health check on the API.
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            # Perform a simple test search
            result = self.search("test", max_results=1)
            return len(result.get('organic_results', [])) >= 0
        except:
            return False