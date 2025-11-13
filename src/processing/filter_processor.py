"""
Filter Processor - Apply advanced filters to search results
Supports site:, filetype:, date:, and custom filters
"""

from typing import List, Dict, Callable, Optional
from datetime import datetime, timedelta
from urllib.parse import urlparse
import re
import logging

logger = logging.getLogger(__name__)


class FilterProcessor:
    """
    Process and apply advanced filters to search results
    """
    
    def __init__(self):
        """Initialize filter processor"""
        # Register built-in filters
        self.filters: Dict[str, Callable] = {
            'site': self._filter_site,
            'filetype': self._filter_filetype,
            'ext': self._filter_filetype,  # Alias
            'date': self._filter_date,
            'before': self._filter_before,
            'after': self._filter_after,
            'lang': self._filter_language,
            'domain': self._filter_domain
        }
    
    def apply_filters(self, 
                     results: List[Dict], 
                     filters: Dict[str, str]) -> List[Dict]:
        """
        Apply all filters to results
        
        Args:
            results: List of search results
            filters: Dictionary of filters to apply
            
        Returns:
            Filtered results
        """
        if not filters:
            return results
        
        filtered = results
        
        for filter_name, filter_value in filters.items():
            if filter_name in self.filters:
                filter_func = self.filters[filter_name]
                filtered = filter_func(filtered, filter_value)
                logger.info(f"Applied {filter_name}:{filter_value} - {len(filtered)} results remain")
        
        return filtered
    
    def _filter_site(self, results: List[Dict], site: str) -> List[Dict]:
        """
        Filter by site/domain
        
        Examples:
            site:github.com
            site:*.edu
        """
        site = site.lower()
        
        # Handle wildcards
        if site.startswith('*.'):
            # Match any subdomain
            suffix = site[2:]
            return [
                r for r in results
                if r.get('url', '').lower().endswith(suffix) or
                   suffix in urlparse(r.get('url', '')).netloc.lower()
            ]
        else:
            # Exact domain match
            return [
                r for r in results
                if site in urlparse(r.get('url', '')).netloc.lower()
            ]
    
    def _filter_filetype(self, results: List[Dict], filetype: str) -> List[Dict]:
        """
        Filter by file type
        
        Examples:
            filetype:pdf
            filetype:doc
        """
        filetype = filetype.lower()
        
        # Add dot if missing
        if not filetype.startswith('.'):
            filetype = '.' + filetype
        
        return [
            r for r in results
            if r.get('url', '').lower().endswith(filetype)
        ]
    
    def _filter_date(self, results: List[Dict], date_spec: str) -> List[Dict]:
        """
        Filter by date
        
        Examples:
            date:2024
            date:2024-01
            date:2024-01-15
        """
        try:
            # Parse date specification
            if len(date_spec) == 4:  # Year only
                year = int(date_spec)
                return [
                    r for r in results
                    if self._match_year(r.get('published_date'), year)
                ]
            elif len(date_spec) == 7:  # Year-month
                year, month = map(int, date_spec.split('-'))
                return [
                    r for r in results
                    if self._match_year_month(r.get('published_date'), year, month)
                ]
            else:  # Full date
                target_date = datetime.fromisoformat(date_spec).date()
                return [
                    r for r in results
                    if self._match_date(r.get('published_date'), target_date)
                ]
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid date spec: {date_spec} - {e}")
            return results
    
    def _filter_before(self, results: List[Dict], date_spec: str) -> List[Dict]:
        """
        Filter results before a date
        
        Examples:
            before:2024-01-01
        """
        try:
            cutoff_date = datetime.fromisoformat(date_spec).date()
            return [
                r for r in results
                if self._date_before(r.get('published_date'), cutoff_date)
            ]
        except (ValueError, AttributeError):
            logger.warning(f"Invalid date spec: {date_spec}")
            return results
    
    def _filter_after(self, results: List[Dict], date_spec: str) -> List[Dict]:
        """
        Filter results after a date
        
        Examples:
            after:2024-01-01
        """
        try:
            cutoff_date = datetime.fromisoformat(date_spec).date()
            return [
                r for r in results
                if self._date_after(r.get('published_date'), cutoff_date)
            ]
        except (ValueError, AttributeError):
            logger.warning(f"Invalid date spec: {date_spec}")
            return results
    
    def _filter_language(self, results: List[Dict], lang: str) -> List[Dict]:
        """
        Filter by language
        
        Examples:
            lang:en
            lang:es
        """
        lang = lang.lower()
        return [
            r for r in results
            if r.get('language', 'en').lower() == lang
        ]
    
    def _filter_domain(self, results: List[Dict], domain_type: str) -> List[Dict]:
        """
        Filter by domain type
        
        Examples:
            domain:edu
            domain:gov
        """
        domain_type = domain_type.lower()
        return [
            r for r in results
            if urlparse(r.get('url', '')).netloc.endswith(f'.{domain_type}')
        ]
    
    # Helper methods for date filtering
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return None
    
    def _match_year(self, date_str: Optional[str], year: int) -> bool:
        """Check if date matches year"""
        date = self._parse_date(date_str)
        return date is not None and date.year == year
    
    def _match_year_month(self, date_str: Optional[str], year: int, month: int) -> bool:
        """Check if date matches year and month"""
        date = self._parse_date(date_str)
        return date is not None and date.year == year and date.month == month
    
    def _match_date(self, date_str: Optional[str], target_date) -> bool:
        """Check if date matches target date"""
        date = self._parse_date(date_str)
        return date is not None and date.date() == target_date
    
    def _date_before(self, date_str: Optional[str], cutoff_date) -> bool:
        """Check if date is before cutoff"""
        date = self._parse_date(date_str)
        return date is not None and date.date() < cutoff_date
    
    def _date_after(self, date_str: Optional[str], cutoff_date) -> bool:
        """Check if date is after cutoff"""
        date = self._parse_date(date_str)
        return date is not None and date.date() > cutoff_date
    
    def register_filter(self, name: str, filter_func: Callable):
        """
        Register a custom filter
        
        Args:
            name: Filter name
            filter_func: Function(results, value) -> filtered_results
        """
        self.filters[name] = filter_func
        logger.info(f"Registered custom filter: {name}")
    
    def get_available_filters(self) -> Dict[str, str]:
        """
        Get list of available filters
        
        Returns:
            Dictionary of filter names and descriptions
        """
        return {
            'site': 'Filter by domain (site:github.com)',
            'filetype': 'Filter by file type (filetype:pdf)',
            'ext': 'Filter by extension (ext:pdf)',
            'date': 'Filter by date (date:2024)',
            'before': 'Results before date (before:2024-01-01)',
            'after': 'Results after date (after:2024-01-01)',
            'lang': 'Filter by language (lang:en)',
            'domain': 'Filter by domain type (domain:edu)'
        }


# Example usage
if __name__ == "__main__":
    # Sample results
    results = [
        {
            'id': '1',
            'url': 'https://github.com/python/cpython',
            'title': 'Python Source Code',
            'published_date': '2024-01-15'
        },
        {
            'id': '2',
            'url': 'https://docs.python.org/3/tutorial.pdf',
            'title': 'Python Tutorial PDF',
            'published_date': '2023-12-01'
        },
        {
            'id': '3',
            'url': 'https://stackoverflow.com/questions/python',
            'title': 'Python Questions',
            'published_date': '2024-02-20'
        },
        {
            'id': '4',
            'url': 'https://en.wikipedia.org/wiki/Python',
            'title': 'Python Wikipedia',
            'published_date': '2024-01-01'
        }
    ]
    
    processor = FilterProcessor()
    
    print("="*60)
    print("Filter Processor Examples")
    print("="*60)
    
    # Test site filter
    print("\nFilter: site:github.com")
    filtered = processor.apply_filters(results, {'site': 'github.com'})
    for r in filtered:
        print(f"  - {r['title']}: {r['url']}")
    
    # Test filetype filter
    print("\nFilter: filetype:pdf")
    filtered = processor.apply_filters(results, {'filetype': 'pdf'})
    for r in filtered:
        print(f"  - {r['title']}: {r['url']}")
    
    # Test date filter
    print("\nFilter: after:2024-01-01")
    filtered = processor.apply_filters(results, {'after': '2024-01-01'})
    for r in filtered:
        print(f"  - {r['title']}: {r['published_date']}")
    
    # Test combined filters
    print("\nFilter: site:*.org after:2024-01-01")
    filtered = processor.apply_filters(results, {
        'site': '*.org',
        'after': '2024-01-01'
    })
    for r in filtered:
        print(f"  - {r['title']}: {r['url']}")
    
    # List available filters
    print("\n" + "="*60)
    print("Available Filters:")
    print("="*60)
    for name, desc in processor.get_available_filters().items():
        print(f"  {name}: {desc}")