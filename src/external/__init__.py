"""
External API Integration Module
Handles third-party search APIs
"""

from .serpapi_client import SerpAPIClient, SerpAPIException
from .google_search_client import GoogleSearchClient, GoogleSearchException

__all__ = [
    'SerpAPIClient', 
    'SerpAPIException',
    'GoogleSearchClient',
    'GoogleSearchException'
]