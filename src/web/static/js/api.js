/**
 * API Client
 * Handles all API requests to the backend
 */

if (typeof API === 'undefined') {
    const API = {
    baseUrl: window.location.origin,
    
    /**
     * Make API request
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise<Object>} Response data
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }
            
            return data;
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },
    
    /**
     * Search
     * @param {Object} params - Search parameters
     * @returns {Promise<Object>} Search results
     */
    async search(params) {
        const queryString = new URLSearchParams(params).toString();
        return this.request(`/api/search?${queryString}`);
    },
    
    /**
     * Get autocomplete suggestions
     * @param {string} query - Search query
     * @param {number} max - Max suggestions
     * @returns {Promise<Array>} Suggestions
     */
    async getSuggestions(query, max = 10) {
        const data = await this.request(`/api/suggestions?q=${encodeURIComponent(query)}&max=${max}`);
        return data.suggestions || [];
    },
    
    /**
     * Search news
     * @param {string} query - Search query
     * @param {number} maxResults - Max results
     * @returns {Promise<Object>} News results
     */
    async searchNews(query, maxResults = 10) {
        return this.request(`/api/search/news?q=${encodeURIComponent(query)}&max_results=${maxResults}`);
    },
    
    /**
     * Search images
     * @param {string} query - Search query
     * @param {number} maxResults - Max results
     * @returns {Promise<Object>} Image results
     */
    async searchImages(query, maxResults = 20) {
        return this.request(`/api/search/images?q=${encodeURIComponent(query)}&max_results=${maxResults}`);
    },
    
    /**
     * Set search mode
     * @param {string} mode - Search mode (local/serpapi/hybrid)
     * @returns {Promise<Object>} Response
     */
    async setSearchMode(mode) {
        return this.request('/api/search/mode', {
            method: 'POST',
            body: JSON.stringify({ mode })
        });
    },
    
    /**
     * Get analytics
     * @returns {Promise<Object>} Analytics data
     */
    async getAnalytics() {
        return this.request('/api/analytics');
    },
    
    /**
     * Get system stats
     * @returns {Promise<Object>} System stats
     */
    async getStats() {
        return this.request('/api/stats');
    },
    
    /**
     * Get cache stats
     * @returns {Promise<Object>} Cache stats
     */
    async getCacheStats() {
        return this.request('/api/cache/stats');
    },
    
    /**
     * Clear cache
     * @returns {Promise<Object>} Response
     */
    async clearCache() {
        return this.request('/api/cache/clear', {
            method: 'POST'
        });
    },
    
    /**
     * Crawl URLs
     * @param {Array} urls - URLs to crawl
     * @param {number} maxDepth - Max crawl depth
     * @returns {Promise<Object>} Crawl results
     */
    async crawlUrls(urls, maxDepth = 1) {
        return this.request('/api/crawl', {
            method: 'POST',
            body: JSON.stringify({ urls, max_depth: maxDepth })
        });
    },
    
    /**
     * Health check
     * @returns {Promise<Object>} Health status
     */
    async healthCheck() {
        return this.request('/health');
    }
};

// Export for use in other scripts
window.API = API;
}