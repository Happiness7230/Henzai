"""
Search Module
Manages search operations across local and external sources
"""

from .search_manager import SearchManager

def __init__(
    self,
    local_ranker=None,
    serpapi_client=None,
    google_client=None,  # ADD THIS LINE
    cache_manager=None,
    mode: str = 'hybrid'
):
    """
    Initialize Search Manager.
    """
    self.local_ranker = local_ranker
    self.serpapi_client = serpapi_client
    self.google_client = google_client  # ADD THIS LINE
    self.cache_manager = cache_manager
    self.mode = mode or os.getenv('SEARCH_MODE', 'hybrid')
    

__all__ = ['SearchManager']

