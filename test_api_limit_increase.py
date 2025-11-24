#!/usr/bin/env python
"""
Test script to verify SerpAPI and Google CSE can return 20 results
Tests pagination support for both APIs
"""

import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.external.serpapi_client import SerpAPIClient
from src.external.google_search_client import GoogleSearchClient
from src.config.config import Config

def test_serpapi_20_results():
    """Test SerpAPI with max_results=20 (requires pagination)"""
    print("\n" + "="*60)
    print("Testing SerpAPI with max_results=20 (pagination)")
    print("="*60)
    
    try:
        client = SerpAPIClient(api_key=Config.SERPAPI_KEY)
        
        # Test query
        query = "python programming tutorial"
        
        print(f"Query: '{query}'")
        print(f"Requesting: 20 results (requires 2 pages)")
        
        start_time = time.time()
        result = client.search(query, max_results=20)
        elapsed = time.time() - start_time
        
        results = result.get('organic_results', [])
        print(f"✅ SUCCESS: Got {len(results)} results in {elapsed:.2f}s")
        
        # Print sample results
        print(f"\nFirst 3 results:")
        for i, r in enumerate(results[:3], 1):
            print(f"  {i}. {r.get('title', 'N/A')[:50]}...")
            print(f"     URL: {r.get('url', 'N/A')[:60]}...")
        
        if len(results) > 10:
            print(f"\nResult 11-13 (from 2nd page):")
            for i, r in enumerate(results[10:13], 11):
                print(f"  {i}. {r.get('title', 'N/A')[:50]}...")
        
        print(f"\nStats: {client.get_stats()}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_google_20_results():
    """Test Google Custom Search with max_results=20 (requires pagination)"""
    print("\n" + "="*60)
    print("Testing Google Custom Search with max_results=20 (pagination)")
    print("="*60)
    
    try:
        client = GoogleSearchClient(
            api_key=Config.GOOGLE_API_KEY,
            cse_id=Config.GOOGLE_SEARCH_ENGINE_ID
        )
        
        # Test query
        query = "artificial intelligence"
        
        print(f"Query: '{query}'")
        print(f"Requesting: 20 results (requires 2 pages)")
        
        start_time = time.time()
        result = client.search(query, max_results=20)
        elapsed = time.time() - start_time
        
        results = result.get('organic_results', [])
        print(f"✅ SUCCESS: Got {len(results)} results in {elapsed:.2f}s")
        
        # Print sample results
        print(f"\nFirst 3 results:")
        for i, r in enumerate(results[:3], 1):
            print(f"  {i}. {r.get('title', 'N/A')[:50]}...")
            print(f"     URL: {r.get('url', 'N/A')[:60]}...")
        
        if len(results) > 10:
            print(f"\nResult 11-13 (from 2nd page):")
            for i, r in enumerate(results[10:13], 11):
                print(f"  {i}. {r.get('title', 'N/A')[:50]}...")
        
        print(f"\nStats: {client.get_stats()}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_mode_20_results():
    """Test hybrid search with both APIs returning 20 results each"""
    print("\n" + "="*60)
    print("Testing Hybrid Search with 20 results from both APIs")
    print("="*60)
    
    try:
        from src.ranking.ranker import Ranker
        from src.search.search_manager import SearchManager
        
        # Initialize clients
        serpapi = SerpAPIClient(api_key=Config.SERPAPI_KEY)
        google = GoogleSearchClient(
            api_key=Config.GOOGLE_API_KEY,
            cse_id=Config.GOOGLE_SEARCH_ENGINE_ID
        )
        
        # Initialize ranker (no local data, but won't error)
        try:
            ranker = Ranker()
            ranker.load()
        except:
            print("⚠️ Warning: Could not load local index, hybrid will use API only")
            ranker = None
        
        # Initialize search manager
        manager = SearchManager(
            google_client=google,
            local_ranker=ranker,
            serpapi_client=serpapi,
            mode='hybrid'
        )
        
        # Test query
        query = "machine learning applications"
        
        print(f"Query: '{query}'")
        print(f"Requesting: 20 results from hybrid (local + API)")
        
        start_time = time.time()
        result = manager.search(query, max_results=20)
        elapsed = time.time() - start_time
        
        results = result.get('results', [])
        print(f"✅ SUCCESS: Got {len(results)} blended results in {elapsed:.2f}s")
        
        metadata = result.get('metadata', {})
        print(f"\nBlended sources:")
        print(f"  Local: {metadata.get('local_count', 0)} results")
        print(f"  API: {metadata.get('api_count', 0)} results")
        print(f"  Total: {metadata.get('blended_count', 0)} results")
        
        # Print sample results
        print(f"\nFirst 3 blended results:")
        for i, r in enumerate(results[:3], 1):
            source = r.get('source', 'unknown')
            print(f"  {i}. [{source}] {r.get('title', 'N/A')[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("\n")
    print("🔧 TESTING API RESULT LIMITS (20 results with pagination)")
    print("="*60)
    
    print(f"\nConfiguration:")
    print(f"  SERPAPI_KEY: {Config.SERPAPI_KEY[:20]}...")
    print(f"  SERPAPI_MAX_RESULTS: {Config.SERPAPI_MAX_RESULTS}")
    print(f"  GOOGLE_MAX_RESULTS: {Config.GOOGLE_MAX_RESULTS}")
    print(f"  DEFAULT_MAX_RESULTS: {Config.DEFAULT_MAX_RESULTS}")
    
    results = []
    
    # Test SerpAPI
    if Config.SERPAPI_ENABLED:
        results.append(("SerpAPI 20 results", test_serpapi_20_results()))
    else:
        print("\n⚠️ SerpAPI disabled in config")
    
    # Test Google CSE
    if Config.GOOGLE_ENABLED:
        results.append(("Google CSE 20 results", test_google_20_results()))
    else:
        print("\n⚠️ Google CSE disabled in config")
    
    # Test hybrid
    if Config.SEARCH_MODE == 'hybrid':
        results.append(("Hybrid 20 results", test_hybrid_mode_20_results()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result for _, result in results)
    print("\n" + ("✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"))
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
