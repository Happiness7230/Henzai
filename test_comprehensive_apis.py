#!/usr/bin/env python
"""
Comprehensive API diagnostic test
Tests marketplace API, job search API, and Google API client integration
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from src.config.config import Config
from src.marketplace.marketplace_client import MarketplaceClient
from src.jobs.job_search_client import JobSearchClient
from src.external.google_search_client import GoogleSearchClient

# Test configuration
BASE_URL = "http://127.0.0.1:8080"
TEST_RESULTS = []

def test_result(name, passed, details=""):
    """Track test results"""
    status = "✅ PASS" if passed else "❌ FAIL"
    TEST_RESULTS.append({"name": name, "passed": passed, "status": status, "details": details})
    print(f"{status}: {name}")
    if details:
        print(f"       {details}")

# ============================================================================
# PART 1: Test Marketplace Client (Backend)
# ============================================================================

def test_marketplace_backend():
    """Test marketplace client initialization and basic functionality"""
    print("\n" + "="*70)
    print("PART 1: Marketplace Client Backend Test")
    print("="*70)
    
    try:
        print("\n1. Initializing marketplace client...")
        client = MarketplaceClient()
        test_result("Marketplace client initialization", True, "✓ Client created successfully")
        
        print("\n2. Testing marketplace search...")
        try:
            results = client.search_all(
                query="laptop",
                max_results=5,
                sort_by="price_asc"
            )
            
            if results:
                test_result("Marketplace search execution", True, f"✓ Got {len(results)} results")
                print(f"   Sample results:")
                for i, result in enumerate(results[:2], 1):
                    print(f"     {i}. {result.get('title', 'N/A')[:60]}")
                    print(f"        Price: {result.get('price', 'N/A')}")
            else:
                test_result("Marketplace search execution", False, "✗ No results returned")
        
        except Exception as e:
            test_result("Marketplace search execution", False, f"✗ Error: {str(e)[:60]}")
        
        return True
    
    except Exception as e:
        test_result("Marketplace client initialization", False, f"✗ Error: {str(e)[:60]}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# PART 2: Test Job Search Client (Backend)
# ============================================================================

def test_job_search_backend():
    """Test job search client initialization and basic functionality"""
    print("\n" + "="*70)
    print("PART 2: Job Search Client Backend Test")
    print("="*70)
    
    try:
        print("\n1. Initializing job search client...")
        client = JobSearchClient()
        test_result("Job search client initialization", True, "✓ Client created successfully")
        
        print("\n2. Testing job search...")
        try:
            results = client.search_jobs(
                query="python developer",
                location="remote",
                max_results=5
            )
            
            if results:
                test_result("Job search execution", True, f"✓ Got {len(results)} results")
                print(f"   Sample results:")
                for i, result in enumerate(results[:2], 1):
                    print(f"     {i}. {result.get('title', 'N/A')[:60]}")
                    print(f"        {result.get('company', 'N/A')}")
            else:
                test_result("Job search execution", False, "✗ No results returned")
        
        except Exception as e:
            test_result("Job search execution", False, f"✗ Error: {str(e)[:60]}")
        
        return True
    
    except Exception as e:
        test_result("Job search client initialization", False, f"✗ Error: {str(e)[:60]}")
        import traceback
        traceback.print_exc()
        return False

# ============================================================================
# PART 3: Test Google API Client
# ============================================================================

def test_google_api_backend():
    """Test Google Search API client"""
    print("\n" + "="*70)
    print("PART 3: Google Search API Client Test")
    print("="*70)
    
    try:
        print("\n1. Checking Google configuration...")
        api_key = Config.GOOGLE_API_KEY
        cse_id = Config.GOOGLE_SEARCH_ENGINE_ID
        enabled = Config.GOOGLE_ENABLED
        
        print(f"   - API Key configured: {'✓ Yes' if api_key else '✗ No'}")
        print(f"   - CSE ID configured: {'✓ Yes' if cse_id else '✗ No'}")
        print(f"   - Enabled: {'✓ Yes' if enabled else '✗ No'}")
        
        if not (api_key and cse_id):
            test_result("Google API configuration", False, "✗ Missing API key or CSE ID")
            return False
        
        print("\n2. Initializing Google Search client...")
        try:
            client = GoogleSearchClient(api_key=api_key, cse_id=cse_id)
            test_result("Google client initialization", True, "✓ Client created successfully")
            
            print("\n3. Testing Google search...")
            try:
                results = client.search(
                    query="python programming",
                    max_results=5
                )
                
                organic = results.get('organic_results', [])
                if organic:
                    test_result("Google search execution", True, f"✓ Got {len(organic)} results")
                    print(f"   Sample results:")
                    for i, result in enumerate(organic[:2], 1):
                        print(f"     {i}. {result.get('title', 'N/A')[:60]}")
                        print(f"        {result.get('url', 'N/A')[:60]}")
                else:
                    test_result("Google search execution", False, "✗ No results returned")
            
            except Exception as e:
                error_msg = str(e)
                if "API key" in error_msg or "quotaExceeded" in error_msg:
                    test_result("Google search execution", False, f"✗ Auth error: {error_msg[:60]}")
                else:
                    test_result("Google search execution", False, f"✗ Error: {error_msg[:60]}")
        
        except Exception as e:
            test_result("Google client initialization", False, f"✗ Error: {str(e)[:60]}")
            import traceback
            traceback.print_exc()
        
        return True
    
    except Exception as e:
        test_result("Google API test setup", False, f"✗ Error: {str(e)[:60]}")
        return False

# ============================================================================
# PART 4: Test API Endpoints via HTTP
# ============================================================================

def test_api_endpoints():
    """Test API endpoints via HTTP"""
    print("\n" + "="*70)
    print("PART 4: HTTP API Endpoint Tests")
    print("="*70)
    
    # Check if server is running
    print("\n1. Checking if Flask server is running...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=2)
        test_result("Flask server running", True, f"✓ Server responsive (status {response.status_code})")
    except requests.exceptions.ConnectionError:
        test_result("Flask server running", False, "✗ Cannot connect to Flask server at http://127.0.0.1:8080")
        print("   → Start server with: python main.py runserver")
        return False
    except Exception as e:
        test_result("Flask server running", False, f"✗ Error: {str(e)[:60]}")
        return False
    
    # Test marketplace endpoint
    print("\n2. Testing /api/marketplace/search endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/marketplace/search",
            json={"q": "laptop", "max_results": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                results = data.get('data', [])
                test_result("Marketplace API endpoint", True, f"✓ Got {len(results)} results")
            else:
                test_result("Marketplace API endpoint", False, f"✗ API error: {data.get('error', 'unknown')[:60]}")
        else:
            test_result("Marketplace API endpoint", False, f"✗ HTTP {response.status_code}: {response.text[:60]}")
    
    except Exception as e:
        test_result("Marketplace API endpoint", False, f"✗ Error: {str(e)[:60]}")
    
    # Test job search endpoint
    print("\n3. Testing /api/jobs/search endpoint...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/jobs/search",
            json={"q": "python developer", "location": "remote", "max_results": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                results = data.get('data', [])
                test_result("Job search API endpoint", True, f"✓ Got {len(results)} results")
            else:
                test_result("Job search API endpoint", False, f"✗ API error: {data.get('error', 'unknown')[:60]}")
        else:
            test_result("Job search API endpoint", False, f"✗ HTTP {response.status_code}: {response.text[:60]}")
    
    except Exception as e:
        test_result("Job search API endpoint", False, f"✗ Error: {str(e)[:60]}")
    
    # Test main search endpoint (Google integration)
    print("\n4. Testing /api/search endpoint (with Google)...")
    try:
        response = requests.get(
            f"{BASE_URL}/api/search?q=python&max_results=5",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                results = data.get('results', [])
                test_result("Main search API endpoint", True, f"✓ Got {len(results)} results")
            else:
                test_result("Main search API endpoint", False, f"✗ API error: {data.get('error', 'unknown')[:60]}")
        else:
            test_result("Main search API endpoint", False, f"✗ HTTP {response.status_code}: {response.text[:60]}")
    
    except Exception as e:
        test_result("Main search API endpoint", False, f"✗ Error: {str(e)[:60]}")

# ============================================================================
# PART 5: Test Frontend UI Access
# ============================================================================

def test_ui_endpoints():
    """Test UI page endpoints"""
    print("\n" + "="*70)
    print("PART 5: Frontend UI Endpoint Tests")
    print("="*70)
    
    endpoints = [
        ("/", "Home"),
        ("/marketplace", "Marketplace"),
        ("/jobs", "Job Search"),
    ]
    
    for endpoint, name in endpoints:
        print(f"\nTesting {name} page ({endpoint})...")
        try:
            response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                test_result(f"UI: {name} page", True, f"✓ Page loads (status {response.status_code})")
            else:
                test_result(f"UI: {name} page", False, f"✗ HTTP {response.status_code}")
        except Exception as e:
            test_result(f"UI: {name} page", False, f"✗ Error: {str(e)[:60]}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all tests"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════════════════╗")
    print("║     🔧 COMPREHENSIVE API & BACKEND DIAGNOSTIC TEST SUITE              ║")
    print("║                     November 24, 2025                                  ║")
    print("╚════════════════════════════════════════════════════════════════════════╝")
    
    # Run all tests
    test_marketplace_backend()
    test_job_search_backend()
    test_google_api_backend()
    test_ui_endpoints()
    test_api_endpoints()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for t in TEST_RESULTS if t['passed'])
    total = len(TEST_RESULTS)
    
    print(f"\nTotal: {passed}/{total} tests passed\n")
    
    for test in TEST_RESULTS:
        print(f"{test['status']}: {test['name']}")
        if test['details']:
            print(f"       {test['details']}")
    
    print("\n" + "="*70)
    print("RECOMMENDATIONS")
    print("="*70)
    
    if passed == total:
        print("✅ All tests passed! Your APIs are working correctly.")
    else:
        failed_tests = [t for t in TEST_RESULTS if not t['passed']]
        print(f"\n❌ {len(failed_tests)} test(s) failed:\n")
        
        for test in failed_tests:
            print(f"  • {test['name']}")
            if "server" in test['name'].lower():
                print(f"    → Start Flask server: python main.py runserver")
            elif "google" in test['name'].lower():
                print(f"    → Check Google API credentials in .env")
                print(f"    → Verify GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID are valid")
            elif "marketplace" in test['name'].lower():
                print(f"    → Check RapidAPI key in .env (RAPIDAPI_KEY)")
            elif "job" in test['name'].lower():
                print(f"    → Ensure job search APIs are configured")

if __name__ == "__main__":
    main()
