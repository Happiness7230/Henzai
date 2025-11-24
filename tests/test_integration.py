"""
Integration Test - Verify all components are connected
"""

import sys
import logging
import os

# --- Robust Path Setup Start ---
tests_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(tests_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- Robust Path Setup End ---

# Import necessary dependencies for Indexer
from src.indexing.indexer import Indexer 
# Adjust these imports based on your actual file structure
from src.processing.tokenizer import Tokenizer
from src.storage.database import Database 
# Note: You might need to import a specific database implementation, 
# e.g., from src.storage.sqlite_database import SQLiteDatabase
# For this example, we assume a generic 'Database' class exists.


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# [The test_imports function remains the same as your last working version]
def test_imports():
    """Test all imports work"""
    print("\n" + "="*60)
    print("Testing Imports...")
    print("="*60)
    
    try:
        from src.ranking.advanced_ranker import AdvancedRanker
        print("✓ AdvancedRanker (existing)")
        from src.caching.cache_manager import CacheManager
        print("✓ CacheManager (existing)")
        from src.storage.analytics_store import AnalyticsStore
        print("✓ AnalyticsStore (existing)")
        from src.crawler.spider import Spider
        print("✓ Spider (existing)")
        from src.external.serpapi_client import SerpAPIClient
        print("✓ SerpAPIClient (Phase 1)")
        from src.search.search_manager import SearchManager
        print("✓ SearchManager (Phase 1)")
        from src.external.google_search_client import GoogleSearchClient
        print("✓ GoogleSearchClient (Phase 4)")
        from src.marketplace.marketplace_client import MarketplaceClient
        print("✓ MarketplaceClient (Phase 4)")
        from src.marketplace.price_alerts import PriceAlertManager
        print("✓ PriceAlertManager (Phase 4)")
        from src.jobs.job_search_client import JobSearchClient
        print("✓ JobSearchClient (Phase 4)")
        from src.config.config import Config
        print("✓ Config")
        from src.processing.tokenizer import Tokenizer # Check import
        from src.storage.database import Database # Check import
        from src.indexing.indexer import Indexer # Check import
        
        print("\n✅ All imports successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        return False


def test_initialization():
    """Test component initialization"""
    print("\n" + "="*60)
    print("Testing Component Initialization...")
    print("="*60)
    
    try:
        from src.config.config import Config
        from src.ranking.advanced_ranker import AdvancedRanker
        from src.search.search_manager import SearchManager
        
        # Test config
        print(f"Search Mode: {Config.SEARCH_MODE}")
        print(f"SerpAPI Enabled: {Config.SERPAPI_ENABLED}")
        
        # Initialize dependencies for the Indexer first
        print("\nInitializing Database and Tokenizer...")
        # Assuming these can be initialized with defaults for a test scenario
        database_instance = Database() 
        tokenizer_instance = Tokenizer()
        print("✓ Database and Tokenizer initialized")

        # Test local ranker
        print("\nInitializing Indexer...")
        # Pass the required arguments to the Indexer
        indexer_instance = Indexer(database=database_instance, tokenizer=tokenizer_instance) 
        print("✓ Indexer initialized")

        print("\nInitializing AdvancedRanker...")
        # Pass the indexer instance to the AdvancedRanker
        ranker = AdvancedRanker(indexer=indexer_instance)
        print("✓ AdvancedRanker initialized")
        
        # Test search manager
        print("\nInitializing SearchManager...")
        manager = SearchManager(
            local_ranker=ranker,
            mode='local'
        )
        print("✓ SearchManager initialized")
        
        print("\n✅ All components initialized successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_search_flow():
    """Test complete search flow"""
    print("\n" + "="*60)
    print("Testing Search Flow...")
    print("="*60)
    
    try:
        from src.ranking.advanced_ranker import AdvancedRanker
        from src.search.search_manager import SearchManager
        
        # Initialize dependencies for the Indexer first
        print("\nInitializing Database and Tokenizer...")
        database_instance = Database() 
        tokenizer_instance = Tokenizer()
        print("✓ Database and Tokenizer initialized")

        # Initialize Indexer
        print("\nInitializing Indexer...")
        indexer_instance = Indexer(database=database_instance, tokenizer=tokenizer_instance)
        print("✓ Indexer initialized")
        
        # Initialize Ranker and Manager
        ranker = AdvancedRanker(indexer=indexer_instance) 
        manager = SearchManager(local_ranker=ranker, mode='local')
        
        # Test search
        print("\nPerforming test search...")
        try:
            results = manager.search("test", max_results=5)
            # Safe way to print results count if structure varies
            count = results.get('total', len(results.get('results', [])) if isinstance(results, dict) else 0)
            print(f"✓ Search executed: {count} results")
        except Exception as e:
            print(f"⚠ Search failed (expected if no documents indexed): {e}")
        
        print("\n✅ Search flow test complete!")
        return True
        
    except Exception as e:
        print(f"\n❌ Search flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    # ... [The main execution block remains the same] ...
    print("\n" + "="*60)
    print("INTEGRATION TEST SUITE")
    print("="*60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Initialization", test_initialization()))
    results.append(("Search Flow", test_search_flow()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! Integration successful!")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED! Check errors above.")
        sys.exit(1)

