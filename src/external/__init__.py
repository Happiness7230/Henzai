"""
External API Integration Module
Handles third-party search APIs
"""

from .serpapi_client import SerpAPIClient, SerpAPIException

__all__ = ['SerpAPIClient', 'SerpAPIException']