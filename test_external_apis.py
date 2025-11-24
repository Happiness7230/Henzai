#!/usr/bin/env python
"""
Test script to verify external API integrations are working.
Run this to check if SerpAPI, Google, and marketplace APIs are properly connected.
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.config.config import Config
from src.external.serpapi_client import SerpAPIClient, SerpAPIException
from src.external.google_search_client import GoogleSearchClient, GoogleSearchException
from src.search.search_manager import SearchManager
from src.ranking.advanced_ranker import AdvancedRanker
from src.indexing.indexer import Indexer
from src.storage.database import Database
from src.processing.tokenizer import Tokenizer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_serpapi():
    """Test SerpAPI connection and search."""
    print("\n" + "="*70)
    print("TEST 1: SerpAPI Integration")
    print("="*70)
    
    if not Config.SERPAPI_ENABLED:
        print("❌ SerpAPI is disabled (SERPAPI_ENABLED=false)")
        return False
    
    if not Config.SERPAPI_KEY:
        print("❌ SerpAPI key not set (SERPAPI_KEY is empty)")
        return False
    
    try:
        print(f"✓ Config: SERPAPI_ENABLED={Config.SERPAPI_ENABLED}, KEY={'***' + Config.SERPAPI_KEY[-4:] if Config.SERPAPI_KEY else 'NOT SET'}")
        client = SerpAPIClient(timeout=Config.SERPAPI_TIMEOUT)
        print("✓ SerpAPI client initialized")
        
        # Try a test search
        print("Attempting test search on SerpAPI...")
        results = client.search("python programming", max_results=3)
        
        if results and 'organic_results' in results and len(results['organic_results']) > 0:
            print(f"✅ SerpAPI search successful! Got {len(results['organic_results'])} results")
            print(f"   First result: {results['organic_results'][0].get('title', 'N/A')}")
            return True
        else:
            print("❌ SerpAPI returned no results")
            return False
            
    except SerpAPIException as e:
        print(f"❌ SerpAPI error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_google():
    """Test Google Custom Search connection."""
    print("\n" + "="*70)
    print("TEST 2: Google Custom Search Integration")
    print("="*70)
    
    google_enabled = os.getenv('GOOGLE_ENABLED', 'false').lower() == 'true'
    google_key = os.getenv('GOOGLE_API_KEY')
    google_cse = os.getenv('GOOGLE_SEARCH_ENGINE_ID')
    
    if not google_enabled:
        print("❌ Google is disabled (GOOGLE_ENABLED=false)")
        return False
    
    if not google_key or not google_cse:
        print(f"❌ Google credentials not set")
        print(f"   GOOGLE_API_KEY: {'SET' if google_key else 'NOT SET'}")
        print(f"   GOOGLE_SEARCH_ENGINE_ID: {'SET' if google_cse else 'NOT SET'}")
        return False
    
    try:
        print(f"✓ Config: GOOGLE_ENABLED=true")
        client = GoogleSearchClient()
        print("✓ Google Search client initialized")
        
        # Try a test search
        print("Attempting test search on Google Custom Search...")
        results = client.search("python programming", max_results=3)
        
        if results and 'organic_results' in results and len(results['organic_results']) > 0:
            print(f"✅ Google search successful! Got {len(results['organic_results'])} results")
            print(f"   First result: {results['organic_results'][0].get('title', 'N/A')}")
            return True
        else:
            print("❌ Google returned no results")
            return False
            
    except GoogleSearchException as e:
        print(f"❌ Google search error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_search_manager_hybrid():
    """Test SearchManager in hybrid mode."""
    print("\n" + "="*70)
    print("TEST 3: SearchManager Hybrid Mode")
    print("="*70)
    
    try:
        # Initialize local components
        tokenizer = Tokenizer()
        database_path = os.path.join(Config.STORAGE_DATA_DIR, 'index.json')
        database = Database(database_path)
        indexer = Indexer(database, tokenizer)
        ranker = AdvancedRanker(indexer)
        print("✓ Local components initialized")
        
        # Initialize external clients
        serpapi_client = None
        google_client = None
        
        if Config.SERPAPI_ENABLED and Config.SERPAPI_KEY:
            try:
                serpapi_client = SerpAPIClient()
                print("✓ SerpAPI client ready")
            except Exception as e:
                print(f"⚠ SerpAPI not available: {e}")
        
        google_enabled = os.getenv('GOOGLE_ENABLED', 'false').lower() == 'true'
        if google_enabled and os.getenv('GOOGLE_API_KEY') and os.getenv('GOOGLE_SEARCH_ENGINE_ID'):
            try:
                google_client = GoogleSearchClient()
                print("✓ Google Search client ready")
            except Exception as e:
                print(f"⚠ Google Search not available: {e}")
        
        # Initialize SearchManager in hybrid mode
        search_manager = SearchManager(
            local_ranker=ranker,
            serpapi_client=serpapi_client,
            google_client=google_client,
            mode='hybrid'
        )
        print(f"✓ SearchManager initialized in 'hybrid' mode")
        print(f"  - Local ranker: {'✓' if ranker else '✗'}")
        print(f"  - SerpAPI: {'✓' if serpapi_client else '✗'}")
        print(f"  - Google: {'✓' if google_client else '✗'}")
        
        # Try a hybrid search
        print("\nAttempting hybrid search...")
        results = search_manager.search("machine learning", max_results=5)
        
        total = len(results.get('results', []))
        metadata = results.get('metadata', {})
        
        print(f"✅ Hybrid search completed")
        print(f"   Total results: {total}")
        print(f"   Mode: {metadata.get('mode', 'unknown')}")
        print(f"   Local count: {metadata.get('local_count', 0)}")
        print(f"   API count: {metadata.get('api_count', 0)}")
        
        if total > 0:
            print(f"   First result: {results['results'][0].get('title', 'N/A')}")
            return True
        else:
            print("❌ Hybrid search returned no results")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  External API Integration Tests".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    Config.print_config()
    
    results = {
        "SerpAPI": test_serpapi(),
        "Google": test_google(),
        "Hybrid": test_search_manager_hybrid(),
    }
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*70)
    if all_passed:
        print("✅ All tests passed! External APIs are properly integrated.")
    else:
        print("❌ Some tests failed. Check configuration and credentials above.")
        print("\nTo fix:")
        print("1. Ensure SERPAPI_KEY is set in .env (get from https://serpapi.com)")
        print("2. Ensure GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID are set in .env")
        print("3. Run 'source .env' or ensure environment variables are loaded")
        print("4. Set SERPAPI_ENABLED=true or GOOGLE_ENABLED=true in .env")
    print("="*70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
