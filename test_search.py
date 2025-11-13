"""Test the search endpoint."""
import requests
import json

def test_search():
    base_url = 'http://localhost:5000'
    
    # Test cases
    test_queries = [
        {'endpoint': '/search?query=python', 'expected_status': 200},
        {'endpoint': '/search?q=python', 'expected_status': 200},
        {'endpoint': '/search?query=', 'expected_status': 400},
        {'endpoint': '/search', 'expected_status': 400}
    ]
    
    for test in test_queries:
        url = base_url + test['endpoint']
        try:
            print(f"\nTesting: {url}")
            response = requests.get(url)
            print(f"Status code: {response.status_code} (Expected: {test['expected_status']})")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Results: {json.dumps(data, indent=2)}")
            else:
                print(f"Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"Could not connect to {url} - is the Flask app running?")

if __name__ == '__main__':
    test_search()