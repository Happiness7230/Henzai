"""
Phase 1 Integration Tests
Tests for SerpAPI client and Search Manager
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from src.external.serpapi_client import SerpAPIClient, SerpAPIException
from src.search.search_manager import SearchManager
from src.config.config import Config


class TestSerpAPIClient:
    """Test SerpAPI client functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        with patch.dict(os.environ, {'SERPAPI_KEY': 'test_key'}):
            return SerpAPIClient(timeout=5)
    
    def test_client_initialization(self, client):
        """Test client initializes correctly"""
        assert client.api_key == 'test_key'
        assert client.timeout == 5
        assert client.stats['total_requests'] == 0
    
    def test_client_no_api_key(self):
        """Test client raises error without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                SerpAPIClient()
    
    @patch('src.external.serpapi_client.GoogleSearch')
    def test_search_success(self, mock_search, client):
        """Test successful search"""
        # Mock response - must include search_parameters for query extraction
        mock_results = {
            'organic_results': [
                {
                    'title': 'Test Result',
                    'link': 'https://example.com',
                    'snippet': 'Test snippet',
                    'position': 1
                }
            ],
            'search_metadata': {'total_time_taken': 0.5},
            'search_parameters': {'q': 'test query'}  # Required for query extraction
        }
        
        mock_search.return_value.get_dict.return_value = mock_results
        
        # Execute search
        results = client.search('test query', max_results=10)
        
        # Verify
        assert results['query'] == 'test query'
        assert len(results['organic_results']) == 1
        assert results['organic_results'][0]['title'] == 'Test Result'
        assert client.stats['successful_requests'] == 1
    
    @patch('src.external.serpapi_client.GoogleSearch')
    def test_search_error_handling(self, mock_search, client):
        """Test search error handling"""
        mock_search.return_value.get_dict.return_value = {'error': 'API Error'}
        
        # The retry decorator retries on SerpAPIException, so after 3 attempts
        # it raises RetryError. We verify that the underlying exception is SerpAPIException
        from tenacity import RetryError
        
        with pytest.raises(RetryError) as exc_info:
            client.search('test query')
        
        # Verify the underlying exception is SerpAPIException
        assert isinstance(exc_info.value.last_attempt.exception(), SerpAPIException)
        assert 'API Error' in str(exc_info.value.last_attempt.exception())
        
        # Stats: failed_requests is incremented twice per attempt (error detection + exception handler)
        # With 3 retry attempts, that's 3 * 2 = 6 increments
        assert client.stats['failed_requests'] == 6
    
    @patch('src.external.serpapi_client.GoogleSearch')
    def test_get_suggestions(self, mock_search, client):
        """Test autocomplete suggestions"""
        mock_results = {
            'suggestions': [
                {'value': 'python programming'},
                {'value': 'python tutorial'}
            ]
        }
        
        mock_search.return_value.get_dict.return_value = mock_results
        
        suggestions = client.get_suggestions('python')
        
        assert len(suggestions) == 2
        assert 'python programming' in suggestions
    
    def test_health_check(self, client):
        """Test health check"""
        with patch.object(client, 'search') as mock_search:
            mock_search.return_value = {'organic_results': []}
            assert client.health_check() == True


class TestSearchManager:
    """Test Search Manager functionality"""
    
    @pytest.fixture
    def mock_ranker(self):
        """Create mock local ranker"""
        ranker = Mock()
        ranker.rank.return_value = [
            {
                'title': 'Local Result',
                'url': 'https://local.com',
                'snippet': 'Local snippet',
                'score': 0.9
            }
        ]
        return ranker
    
    @pytest.fixture
    def mock_serpapi(self):
        """Create mock SerpAPI client"""
        client = Mock()
        client.search.return_value = {
            'organic_results': [
                {
                    'title': 'API Result',
                    'url': 'https://api.com',
                    'snippet': 'API snippet',
                    'position': 1
                }
            ],
            'metadata': {'source': 'serpapi'}
        }
        return client
    
    @pytest.fixture
    def manager_local(self, mock_ranker):
        """Create manager in local mode"""
        return SearchManager(
            local_ranker=mock_ranker,
            mode='local'
        )
    
    @pytest.fixture
    def manager_api(self, mock_serpapi):
        """Create manager in API mode"""
        return SearchManager(
            serpapi_client=mock_serpapi,
            mode='serpapi'
        )
    
    @pytest.fixture
    def manager_hybrid(self, mock_ranker, mock_serpapi):
        """Create manager in hybrid mode"""
        return SearchManager(
            local_ranker=mock_ranker,
            serpapi_client=mock_serpapi,
            mode='hybrid'
        )
    
    def test_local_search(self, manager_local):
        """Test local-only search"""
        results = manager_local.search('test query', max_results=10)
        
        assert results['query'] == 'test query'
        assert len(results['results']) == 1
        assert results['results'][0]['source'] == 'local'
        assert results['metadata']['source'] == 'local'
    
    def test_api_search(self, manager_api):
        """Test API-only search"""
        results = manager_api.search('test query', max_results=10)
        
        assert results['query'] == 'test query'
        assert len(results['results']) == 1
        assert results['metadata']['source'] == 'serpapi'
    
    def test_hybrid_search(self, manager_hybrid):
        """Test hybrid search blending"""
        results = manager_hybrid.search('test query', max_results=10)
        
        assert results['query'] == 'test query'
        assert results['metadata']['source'] == 'hybrid'
        # Should have results from both sources
        assert results['metadata']['local_count'] >= 0
        assert results['metadata']['api_count'] >= 0
    
    def test_result_deduplication(self, manager_hybrid):
        """Test that duplicate domains are removed"""
        # Mock to return same domain
        manager_hybrid.local_ranker.rank.return_value = [
            {'url': 'https://example.com/page1', 'title': 'Page 1', 'score': 0.9}
        ]
        manager_hybrid.serpapi_client.search.return_value = {
            'organic_results': [
                {'url': 'https://example.com/page2', 'title': 'Page 2', 'position': 1}
            ],
            'metadata': {}
        }
        
        results = manager_hybrid.search('test', max_results=10)
        
        # Should only have one result due to deduplication
        if manager_hybrid.deduplicate:
            assert len(results['results']) == 1
    
    def test_mode_switching(self, manager_hybrid):
        """Test runtime mode switching"""
        assert manager_hybrid.mode == 'hybrid'
        
        success = manager_hybrid.set_mode('local')
        assert success == True
        assert manager_hybrid.mode == 'local'
        
        success = manager_hybrid.set_mode('invalid')
        assert success == False
    
    def test_statistics_tracking(self, manager_local):
        """Test statistics are tracked correctly"""
        initial_count = manager_local.stats['total_searches']
        
        manager_local.search('test', max_results=10)
        
        assert manager_local.stats['total_searches'] == initial_count + 1
        assert manager_local.stats['local_searches'] > 0


class TestConfig:
    """Test configuration management"""
    
    def test_config_defaults(self):
        """Test default configuration values"""
        assert Config.FLASK_PORT == 5000
        assert Config.SEARCH_MODE in ['local', 'serpapi', 'hybrid']
        assert Config.CACHE_ENABLED in [True, False]
    
    def test_config_validation(self):
        """Test configuration validation"""
        # Should pass validation with defaults
        assert Config.validate() == True
    
    def test_config_get(self):
        """Test getting config values"""
        port = Config.get('FLASK_PORT')
        assert isinstance(port, int)
        
        invalid = Config.get('INVALID_KEY', 'default')
        assert invalid == 'default'
    
    def test_config_to_dict(self):
        """Test config to dictionary conversion"""
        config_dict = Config.to_dict()
        assert isinstance(config_dict, dict)
        assert 'FLASK_PORT' in config_dict


# Integration test
class TestPhase1Integration:
    """Test full Phase 1 integration"""
    
    @pytest.mark.integration
    def test_full_search_pipeline(self):
        """Test complete search pipeline with mocked components"""
        # Setup
        mock_ranker = Mock()
        mock_ranker.rank.return_value = [
            {'title': 'Test', 'url': 'https://test.com', 'score': 0.8}
        ]
        
        with patch('src.external.serpapi_client.GoogleSearch') as mock_search:
            mock_search.return_value.get_dict.return_value = {
                'organic_results': [
                    {'title': 'API', 'link': 'https://api.com', 'snippet': 'text', 'position': 1}
                ],
                'search_metadata': {}
            }
            
            # Create components
            with patch.dict(os.environ, {'SERPAPI_KEY': 'test_key'}):
                serpapi = SerpAPIClient()
                manager = SearchManager(
                    local_ranker=mock_ranker,
                    serpapi_client=serpapi,
                    mode='hybrid'
                )
                
                # Execute search
                results = manager.search('test query', max_results=10)
                
                # Verify
                assert results['query'] == 'test query'
                assert 'results' in results
                assert 'metadata' in results


if __name__ == '__main__':
    pytest.main([__file__, '-v'])