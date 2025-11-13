"""
API Endpoint Tests - Phase 2
Tests for all Flask API endpoints
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from src.web.app import app, initialize_components


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_search_manager():
    """Create mock search manager"""
    manager = Mock()
    manager.search.return_value = {
        'query': 'test',
        'results': [
            {
                'title': 'Test Result',
                'url': 'https://example.com',
                'snippet': 'Test snippet',
                'domain': 'example.com',
                'score': 0.9,
                'source': 'serpapi'
            }
        ],
        'total': 1,
        'metadata': {
            'source': 'hybrid',
            'response_time': 0.123,
            'mode': 'hybrid'
        }
    }
    manager.get_suggestions.return_value = ['test 1', 'test 2', 'test 3']
    manager.get_stats.return_value = {
        'total_searches': 10,
        'mode': 'hybrid'
    }
    manager.set_mode.return_value = True
    return manager


class TestSearchEndpoints:
    """Test search API endpoints"""
    
    def test_search_get(self, client, mock_search_manager):
        """Test GET /api/search"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.get('/api/search?q=test&max_results=10')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'data' in data
            assert data['data']['query'] == 'test'
            assert len(data['data']['results']) == 1
    
    def test_search_post(self, client, mock_search_manager):
        """Test POST /api/search"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.post(
                '/api/search',
                data=json.dumps({'q': 'test', 'max_results': 5}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
    
    def test_search_no_query(self, client):
        """Test search without query parameter"""
        response = client.get('/api/search')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert 'required' in data['error'].lower()
    
    def test_search_with_mode_override(self, client, mock_search_manager):
        """Test search with mode override"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.get('/api/search?q=test&mode=serpapi')
            
            assert response.status_code == 200
            mock_search_manager.set_mode.assert_called()
    
    def test_search_with_filters(self, client, mock_search_manager):
        """Test search with filters"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.post(
                '/api/search',
                data=json.dumps({
                    'q': 'test',
                    'filters': {'site': 'example.com'},
                    'safe_search': True,
                    'region': 'us-en'
                }),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'


class TestSuggestionsEndpoint:
    """Test suggestions endpoint"""
    
    def test_suggestions_success(self, client, mock_search_manager):
        """Test successful suggestions request"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.get('/api/suggestions?q=test&max=5')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'suggestions' in data
            assert len(data['suggestions']) == 3
    
    def test_suggestions_no_query(self, client):
        """Test suggestions without query"""
        response = client.get('/api/suggestions')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['status'] == 'error'


class TestNewsEndpoint:
    """Test news search endpoint"""
    
    def test_news_search(self, client):
        """Test news search"""
        mock_serpapi = Mock()
        mock_serpapi.search_news.return_value = {
            'query': 'test',
            'results': [
                {
                    'title': 'News Article',
                    'url': 'https://news.example.com',
                    'snippet': 'News snippet',
                    'source': 'News Source',
                    'date': '2024-11-10',
                    'type': 'news'
                }
            ],
            'total': 1
        }
        
        with patch('src.web.app.serpapi_client', mock_serpapi):
            response = client.get('/api/search/news?q=test&max_results=10')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'data' in data
    
    def test_news_no_serpapi(self, client):
        """Test news search without SerpAPI"""
        with patch('src.web.app.serpapi_client', None):
            response = client.get('/api/search/news?q=test')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert data['status'] == 'error'


class TestImagesEndpoint:
    """Test image search endpoint"""
    
    def test_image_search(self, client):
        """Test image search"""
        mock_serpapi = Mock()
        mock_serpapi.search_images.return_value = {
            'query': 'cats',
            'results': [
                {
                    'title': 'Cat image',
                    'url': 'https://example.com/cat.jpg',
                    'thumbnail': 'https://example.com/thumb.jpg',
                    'type': 'image'
                }
            ],
            'total': 1
        }
        
        with patch('src.web.app.serpapi_client', mock_serpapi):
            response = client.get('/api/search/images?q=cats&max_results=20')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'


class TestModeEndpoint:
    """Test search mode endpoint"""
    
    def test_set_mode_success(self, client, mock_search_manager):
        """Test successful mode change"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.post(
                '/api/search/mode',
                data=json.dumps({'mode': 'hybrid'}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert data['mode'] == 'hybrid'
    
    def test_set_mode_invalid(self, client, mock_search_manager):
        """Test invalid mode"""
        mock_search_manager.set_mode.return_value = False
        
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.post(
                '/api/search/mode',
                data=json.dumps({'mode': 'invalid'}),
                content_type='application/json'
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['status'] == 'error'
    
    def test_set_mode_no_mode(self, client):
        """Test mode change without mode parameter"""
        response = client.post(
            '/api/search/mode',
            data=json.dumps({}),
            content_type='application/json'
        )
        
        assert response.status_code == 400


class TestCrawlEndpoint:
    """Test crawl endpoint"""
    
    def test_crawl_success(self, client):
        """Test successful crawl"""
        mock_spider = Mock()
        mock_spider.crawl.return_value = {
            'crawled': 5,
            'failed': 0,
            'indexed': 5
        }
        
        with patch('src.web.app.spider', mock_spider):
            response = client.post(
                '/api/crawl',
                data=json.dumps({
                    'urls': ['https://example.com'],
                    'max_depth': 2
                }),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
    
    def test_crawl_no_urls(self, client):
        """Test crawl without URLs"""
        with patch('src.web.app.spider', Mock()):
            response = client.post(
                '/api/crawl',
                data=json.dumps({}),
                content_type='application/json'
            )
            
            assert response.status_code == 400


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_analytics(self, client, mock_search_manager):
        """Test analytics endpoint"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.get('/api/analytics')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'data' in data
    
    def test_stats(self, client, mock_search_manager):
        """Test stats endpoint"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.get('/api/stats')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'search_mode' in data['data']
    
    def test_metrics(self, client, mock_search_manager):
        """Test metrics endpoint"""
        with patch('src.web.app.search_manager', mock_search_manager):
            response = client.get('/api/metrics')
            
            assert response.status_code == 200
            assert response.content_type == 'text/plain; charset=utf-8'


class TestCacheEndpoints:
    """Test cache management endpoints"""
    
    def test_cache_stats(self, client):
        """Test cache stats endpoint"""
        mock_cache = Mock()
        mock_cache.get_stats.return_value = {
            'hits': 10,
            'misses': 20,
            'hit_rate': 33.33
        }
        
        with patch('src.web.app.cache_manager', mock_cache):
            response = client.get('/api/cache/stats')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
    
    def test_cache_clear(self, client):
        """Test cache clear endpoint"""
        mock_cache = Mock()
        
        with patch('src.web.app.cache_manager', mock_cache):
            response = client.post('/api/cache/clear')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'success'
            mock_cache.clear.assert_called_once()


class TestHealthEndpoints:
    """Test health and monitoring endpoints"""
    
    def test_health_check_healthy(self, client):
        """Test health check when all services are up"""
        mock_serpapi = Mock()
        mock_serpapi.health_check.return_value = True
        
        with patch('src.web.app.serpapi_client', mock_serpapi):
            with patch('src.web.app.cache_manager', Mock()):
                with patch('src.web.app.search_manager', Mock()):
                    response = client.get('/health')
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['status'] == 'healthy'
    
    def test_health_check_degraded(self, client):
        """Test health check when service is degraded"""
        mock_serpapi = Mock()
        mock_serpapi.health_check.return_value = False
        
        with patch('src.web.app.serpapi_client', mock_serpapi):
            response = client.get('/health')
            
            assert response.status_code == 503
            data = json.loads(response.data)
            assert data['status'] == 'degraded'


class TestErrorHandlers:
    """Test error handlers"""
    
    def test_404_handler(self, client):
        """Test 404 error handler"""
        response = client.get('/nonexistent')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data['status'] == 'error'
        assert data['code'] == 404


class TestUIRoutes:
    """Test UI routes"""
    
    def test_index_page(self, client):
        """Test index page"""
        with patch('src.web.app.render_template') as mock_render:
            mock_render.return_value = '<html>Search</html>'
            response = client.get('/')
            
            assert response.status_code == 200
            mock_render.assert_called_with('search.html')
    
    def test_results_page(self, client):
        """Test results page"""
        with patch('src.web.app.render_template') as mock_render:
            mock_render.return_value = '<html>Results</html>'
            response = client.get('/results?q=test')
            
            assert response.status_code == 200
            mock_render.assert_called_with('results.html', query='test')


class TestIntegration:
    """Integration tests"""
    
    @pytest.mark.integration
    def test_full_search_flow(self, client, mock_search_manager):
        """Test complete search flow"""
        with patch('src.web.app.search_manager', mock_search_manager):
            # 1. Perform search
            response = client.get('/api/search?q=python&max_results=5')
            assert response.status_code == 200
            
            # 2. Get suggestions
            response = client.get('/api/suggestions?q=python')
            assert response.status_code == 200
            
            # 3. Check analytics
            response = client.get('/api/analytics')
            assert response.status_code == 200
            
            # 4. Check health
            response = client.get('/health')
            assert response.status_code in [200, 503]
    
    @pytest.mark.integration
    def test_mode_switching_flow(self, client, mock_search_manager):
        """Test mode switching during search"""
        with patch('src.web.app.search_manager', mock_search_manager):
            # 1. Check current mode
            response = client.get('/api/stats')
            assert response.status_code == 200
            
            # 2. Switch mode
            response = client.post(
                '/api/search/mode',
                data=json.dumps({'mode': 'serpapi'}),
                content_type='application/json'
            )
            assert response.status_code == 200
            
            # 3. Search with new mode
            response = client.get('/api/search?q=test')
            assert response.status_code == 200


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])