"""
Google Custom Search API Client
Official Google Search API integration with fallback support
"""

import os
import logging
from typing import Dict, List, Optional, Any
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class GoogleSearchException(Exception):
    """Custom exception for Google Search errors"""
    pass


class GoogleSearchClient:
    """
    Client for Google Custom Search API with quota management.
    Falls back to SerpAPI when quota is exceeded.
    """
    
    def __init__(self, api_key: Optional[str] = None, cse_id: Optional[str] = None):
        """
        Initialize Google Search client.
        
        Args:
            api_key: Google API key
            cse_id: Custom Search Engine ID
        """
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        # Support both naming conventions: GOOGLE_CSE_ID and GOOGLE_SEARCH_ENGINE_ID
        self.cse_id = cse_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID') or os.getenv('GOOGLE_CSE_ID')
        
        if not self.api_key or not self.cse_id:
            raise ValueError("GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID (or GOOGLE_CSE_ID) are required")
        
        try:
            self.service = build("customsearch", "v1", developerKey=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Google Search: {str(e)}")
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'quota_exceeded': 0,
            'total_results_returned': 0
        }
        
        logger.info("Google Custom Search client initialized")
    
    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5)
    )
    def search(
        self,
        query: str,
        max_results: int = 10,
        safe_search: bool = True,
        date_restrict: Optional[str] = None,
        site_search: Optional[str] = None,
        file_type: Optional[str] = None,
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Perform search using Google Custom Search API with pagination support.
        
        Args:
            query: Search query
            max_results: Maximum results (can be > 10 through pagination)
            safe_search: Enable safe search
            date_restrict: Date restriction (d[number], w[number], m[number], y[number])
            site_search: Restrict to specific site
            file_type: Filter by file type (pdf, doc, etc.)
            language: Language code (en, es, fr, etc.)
            
        Returns:
            Normalized search results with multiple pages if needed
        """
        self.stats['total_requests'] += 1
        
        try:
            all_results = []
            results_per_page = 10  # Google CSE returns 10 results per request
            
            # Calculate number of pages needed
            num_pages = (max_results + 9) // 10  # Round up
            
            # Fetch multiple pages if needed
            for page in range(num_pages):
                start_index = page * results_per_page + 1  # Google uses 1-based indexing
                
                # Build search parameters
                params = {
                    'q': query,
                    'cx': self.cse_id,
                    'num': 10,  # Always request 10 per page
                    'start': start_index,  # Google's pagination parameter
                    'safe': 'active' if safe_search else 'off',
                    'lr': f'lang_{language}'
                }
                
                # Add optional filters
                if date_restrict:
                    params['dateRestrict'] = date_restrict
                if site_search:
                    params['siteSearch'] = site_search
                if file_type:
                    params['fileType'] = file_type
                
                logger.info(f"Executing Google search: query='{query}', page={page+1}")
                
                # Execute search
                result = self.service.cse().list(**params).execute()
                
                # Check if we got any results
                items = result.get('items', [])
                if not items:
                    break  # No more results available
                
                all_results.extend(items)
                
                # Stop if we have enough results
                if len(all_results) >= max_results:
                    all_results = all_results[:max_results]
                    break
            
            # Normalize results (using combined results)
            normalized = self._normalize_results_paginated(result, query, all_results)
            
            self.stats['successful_requests'] += 1
            self.stats['total_results_returned'] += len(normalized['organic_results'])
            
            logger.info(f"Google search successful: {len(normalized['organic_results'])} results")
            
            return normalized
            
        except HttpError as e:
            self.stats['failed_requests'] += 1
            
            # Check if quota exceeded
            if e.resp.status == 429 or 'quotaExceeded' in str(e):
                self.stats['quota_exceeded'] += 1
                logger.warning("Google API quota exceeded")
                raise GoogleSearchException("Quota exceeded")
            
            logger.error(f"Google search error: {str(e)}")
            raise GoogleSearchException(f"Search failed: {str(e)}")
        
        except Exception as e:
            self.stats['failed_requests'] += 1
            logger.error(f"Google search error: {str(e)}")
            raise GoogleSearchException(f"Search failed: {str(e)}")
    
    def _normalize_results(self, raw_results: Dict, query: str) -> Dict[str, Any]:
        """
        Normalize Google results to match internal format.
        
        Args:
            raw_results: Raw results from Google API
            query: Original query
            
        Returns:
            Normalized results dictionary
        """
        return self._normalize_results_paginated(raw_results, query, raw_results.get('items', []))
    
    def _normalize_results_paginated(self, raw_results: Dict, query: str, items: List[Dict]) -> Dict[str, Any]:
        """
        Normalize Google results to match internal format.
        
        Args:
            raw_results: Raw results from Google API
            query: Original query
            items: List of items from all pages
            
        Returns:
            Normalized results dictionary
        """
        normalized = {
            'query': query,
            'organic_results': [],
            'related_searches': [],
            'answer_box': None,
            'knowledge_graph': None,
            'metadata': {
                'total_results': 0,
                'search_time': 0,
                'source': 'google',
                'engine': 'google_custom_search'
            }
        }
        
        # Get search information
        search_info = raw_results.get('searchInformation', {})
        normalized['metadata']['total_results'] = int(search_info.get('totalResults', 0))
        normalized['metadata']['search_time'] = float(search_info.get('searchTime', 0))
        
        # Process organic results from all pages
        for i, item in enumerate(items):
            result = {
                'title': item.get('title', ''),
                'url': item.get('link', ''),
                'snippet': item.get('snippet', ''),
                'domain': self._extract_domain(item.get('link', '')),
                'position': i + 1,
                'source': 'google'
            }
            
            # Add additional metadata if available
            if 'pagemap' in item:
                pagemap = item['pagemap']
                
                # Extract favicon
                if 'cse_image' in pagemap:
                    result['favicon'] = pagemap['cse_image'][0].get('src')
                
                # Extract meta description
                if 'metatags' in pagemap and pagemap['metatags']:
                    metatags = pagemap['metatags'][0]
                    result['meta_description'] = metatags.get('og:description', '')
                    result['date'] = metatags.get('article:published_time', '')
            
            normalized['organic_results'].append(result)
        
        # Extract knowledge graph if available
        if 'knowledgeGraph' in raw_results:
            kg = raw_results['knowledgeGraph']
            normalized['knowledge_graph'] = {
                'title': kg.get('name', ''),
                'type': kg.get('@type', ''),
                'description': kg.get('description', ''),
                'image': kg.get('image', {}).get('contentUrl', ''),
                'website': kg.get('url', '')
            }
        
        return normalized
    
    def get_stats(self) -> Dict[str, Any]:
        """Get client statistics."""
        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_requests'] / self.stats['total_requests'] * 100
                if self.stats['total_requests'] > 0 else 0
            ),
            'quota_exceeded_rate': (
                self.stats['quota_exceeded'] / self.stats['total_requests'] * 100
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
        Perform health check.
        
        Returns:
            True if API is accessible
        """
        try:
            # Perform a simple test search
            result = self.search("test", max_results=1)
            return True
        except GoogleSearchException:
            return False
        except:
            return False