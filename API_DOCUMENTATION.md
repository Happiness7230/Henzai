# API Documentation - Phase 2

## Base URL
```
http://localhost:5000
```

---

## Search Endpoints

### 1. Unified Search
**Endpoint:** `/api/search`  
**Methods:** `GET`, `POST`  
**Description:** Main search endpoint supporting all search modes

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| q | string | Yes | - | Search query |
| max_results | integer | No | 10 | Maximum results to return |
| mode | string | No | config | Search mode (local/serpapi/hybrid) |
| safe_search | boolean | No | true | Enable safe search filtering |
| region | string | No | wt-wt | Region code (us-en, uk-en, etc.) |
| time_period | string | No | - | Time filter (d/w/m/y) |
| filters | object | No | {} | Advanced filters |

#### Example Request (GET)
```bash
curl "http://localhost:5000/api/search?q=python+programming&max_results=10"
```

#### Example Request (POST)
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "q": "python programming",
    "max_results": 10,
    "mode": "hybrid",
    "safe_search": true,
    "region": "us-en"
  }'
```

#### Response
```json
{
  "status": "success",
  "data": {
    "query": "python programming",
    "results": [
      {
        "title": "Python Tutorial",
        "url": "https://example.com",
        "snippet": "Learn Python programming...",
        "domain": "example.com",
        "position": 1,
        "source": "serpapi",
        "score": 0.95
      }
    ],
    "total": 10,
    "answer_box": {
      "title": "Python",
      "answer": "Python is a programming language...",
      "link": "https://python.org"
    },
    "knowledge_graph": {
      "title": "Python (programming language)",
      "type": "Programming language",
      "description": "...",
      "website": "https://python.org"
    },
    "related_searches": [
      "python tutorial",
      "python basics"
    ],
    "metadata": {
      "source": "hybrid",
      "local_count": 3,
      "api_count": 7,
      "blended_count": 10,
      "response_time": 0.234,
      "mode": "hybrid",
      "timestamp": "2024-11-10T10:30:00"
    }
  }
}
```

---

### 2. Autocomplete Suggestions
**Endpoint:** `/api/suggestions`  
**Method:** `GET`  
**Description:** Get autocomplete suggestions for partial queries

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| q | string | Yes | - | Partial query |
| max | integer | No | 10 | Maximum suggestions |

#### Example Request
```bash
curl "http://localhost:5000/api/suggestions?q=python&max=5"
```

#### Response
```json
{
  "status": "success",
  "query": "python",
  "suggestions": [
    "python programming",
    "python tutorial",
    "python basics",
    "python for beginners",
    "python projects"
  ]
}
```

---

### 3. News Search
**Endpoint:** `/api/search/news`  
**Method:** `GET`  
**Description:** Search for news articles (requires SerpAPI)

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| q | string | Yes | - | Search query |
| max_results | integer | No | 10 | Maximum results |

#### Example Request
```bash
curl "http://localhost:5000/api/search/news?q=artificial+intelligence&max_results=5"
```

#### Response
```json
{
  "status": "success",
  "data": {
    "query": "artificial intelligence",
    "results": [
      {
        "title": "AI Breakthrough Announced",
        "url": "https://news.example.com/ai-news",
        "snippet": "Researchers announce...",
        "source": "Tech News",
        "date": "2024-11-10",
        "thumbnail": "https://...",
        "type": "news"
      }
    ],
    "total": 5
  }
}
```

---

### 4. Image Search
**Endpoint:** `/api/search/images`  
**Method:** `GET`  
**Description:** Search for images (requires SerpAPI)

#### Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| q | string | Yes | - | Search query |
| max_results | integer | No | 20 | Maximum results |

#### Example Request
```bash
curl "http://localhost:5000/api/search/images?q=cats&max_results=10"
```

#### Response
```json
{
  "status": "success",
  "data": {
    "query": "cats",
    "results": [
      {
        "title": "Cute cat",
        "url": "https://example.com/cat.jpg",
        "thumbnail": "https://example.com/thumb.jpg",
        "source": "example.com",
        "width": 1920,
        "height": 1080,
        "type": "image"
      }
    ],
    "total": 10
  }
}
```

---

### 5. Change Search Mode
**Endpoint:** `/api/search/mode`  
**Method:** `POST`  
**Description:** Change search mode at runtime

#### Request Body
```json
{
  "mode": "hybrid"
}
```

Valid modes: `local`, `serpapi`, `hybrid`

#### Example Request
```bash
curl -X POST http://localhost:5000/api/search/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "hybrid"}'
```

#### Response
```json
{
  "status": "success",
  "mode": "hybrid",
  "message": "Search mode changed to hybrid"
}
```

---

## Crawling Endpoints

### 6. Crawl URLs
**Endpoint:** `/api/crawl`  
**Method:** `POST`  
**Description:** Crawl URLs and add to index

#### Request Body
```json
{
  "urls": [
    "https://example.com",
    "https://example.com/page2"
  ],
  "max_depth": 1
}
```

#### Example Request
```bash
curl -X POST http://localhost:5000/api/crawl \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://example.com"],
    "max_depth": 2
  }'
```

#### Response
```json
{
  "status": "success",
  "message": "Crawled 5 pages",
  "data": {
    "crawled": 5,
    "failed": 0,
    "indexed": 5
  }
}
```

---

## Analytics & Statistics

### 7. Analytics
**Endpoint:** `/api/analytics`  
**Method:** `GET`  
**Description:** Get search analytics and statistics

#### Example Request
```bash
curl "http://localhost:5000/api/analytics"
```

#### Response
```json
{
  "status": "success",
  "data": {
    "search_manager": {
      "total_searches": 150,
      "local_searches": 30,
      "api_searches": 50,
      "hybrid_searches": 70,
      "cache_hits": 45,
      "avg_response_time": 0.345
    },
    "serpapi": {
      "total_requests": 120,
      "successful_requests": 118,
      "failed_requests": 2,
      "success_rate": 98.33
    },
    "cache": {
      "hits": 45,
      "misses": 105,
      "hit_rate": 30.0
    },
    "queries": [
      {"query": "python", "count": 25},
      {"query": "javascript", "count": 20}
    ]
  }
}
```

---

### 8. System Statistics
**Endpoint:** `/api/stats`  
**Method:** `GET`  
**Description:** Get system configuration and status

#### Example Request
```bash
curl "http://localhost:5000/api/stats"
```

#### Response
```json
{
  "status": "success",
  "data": {
    "search_mode": "hybrid",
    "serpapi_enabled": true,
    "cache_enabled": true,
    "analytics_enabled": true,
    "components": {
      "search_manager": true,
      "serpapi_client": true,
      "local_ranker": true,
      "cache_manager": true,
      "analytics_store": true,
      "spider": true
    },
    "search_stats": {
      "total_searches": 150,
      "mode": "hybrid"
    }
  }
}
```

---

### 9. Prometheus Metrics
**Endpoint:** `/api/metrics`  
**Method:** `GET`  
**Description:** Prometheus-compatible metrics

#### Example Request
```bash
curl "http://localhost:5000/api/metrics"
```

#### Response (Plain Text)
```
search_total_searches 150
search_cache_hits 45
search_avg_response_time 0.345
serpapi_total_requests 120
serpapi_successful_requests 118
serpapi_failed_requests 2
```

---

## Cache Management

### 10. Cache Statistics
**Endpoint:** `/api/cache/stats`  
**Method:** `GET`  
**Description:** Get cache statistics

#### Example Request
```bash
curl "http://localhost:5000/api/cache/stats"
```

#### Response
```json
{
  "status": "success",
  "data": {
    "hits": 45,
    "misses": 105,
    "hit_rate": 30.0,
    "size": 1024,
    "keys": 150
  }
}
```

---

### 11. Clear Cache
**Endpoint:** `/api/cache/clear`  
**Method:** `POST`  
**Description:** Clear all cached data

#### Example Request
```bash
curl -X POST "http://localhost:5000/api/cache/clear"
```

#### Response
```json
{
  "status": "success",
  "message": "Cache cleared successfully"
}
```

---

## Health & Monitoring

### 12. Health Check
**Endpoint:** `/health`  
**Method:** `GET`  
**Description:** Check system health

#### Example Request
```bash
curl "http://localhost:5000/health"
```

#### Response (Healthy)
```json
{
  "status": "healthy",
  "timestamp": "2024-11-10T10:30:00",
  "components": {
    "serpapi": true,
    "cache": true,
    "search_manager": true
  }
}
```

#### Response (Degraded)
```json
{
  "status": "degraded",
  "timestamp": "2024-11-10T10:30:00",
  "components": {
    "serpapi": false,
    "cache": true,
    "search_manager": true
  }
}
```

---

## Error Responses

All endpoints return consistent error responses:

### 400 Bad Request
```json
{
  "status": "error",
  "error": "Query parameter 'q' is required"
}
```

### 500 Internal Server Error
```json
{
  "status": "error",
  "error": "Internal server error",
  "code": 500
}
```

### 503 Service Unavailable
```json
{
  "status": "error",
  "error": "Service not available"
}
```

---

## Rate Limiting

When rate limiting is enabled (default), requests are limited to:
- **60 requests per minute** per IP
- **Burst limit:** 10 requests

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1699612800
```

---

## CORS

CORS is enabled by default for all origins. Configure in `.env`:
```bash
CORS_ENABLED=true
CORS_ORIGINS=*  # or specific origins: http://localhost:3000
```

---

## Authentication

Currently, no authentication is required. In production, consider:
- API keys
- OAuth2
- JWT tokens

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## Testing with cURL

### Quick Tests
```bash
# Basic search
curl "http://localhost:5000/api/search?q=test"

# With parameters
curl "http://localhost:5000/api/search?q=python&max_results=5&mode=hybrid"

# Suggestions
curl "http://localhost:5000/api/suggestions?q=python"

# News
curl "http://localhost:5000/api/search/news?q=technology"

# Health check
curl "http://localhost:5000/health"

# Analytics
curl "http://localhost:5000/api/analytics"
```

---

## SDK Examples

### Python
```python
import requests

# Search
response = requests.get('http://localhost:5000/api/search', params={
    'q': 'python programming',
    'max_results': 10
})
results = response.json()

# POST search
response = requests.post('http://localhost:5000/api/search', json={
    'q': 'machine learning',
    'mode': 'hybrid',
    'safe_search': True
})
```

### JavaScript
```javascript
// Search
fetch('http://localhost:5000/api/search?q=python&max_results=10')
  .then(res => res.json())
  .then(data => console.log(data));

// POST search
fetch('http://localhost:5000/api/search', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    q: 'machine learning',
    mode: 'hybrid'
  })
})
  .then(res => res.json())
  .then(data => console.log(data));
```

---

## Next Steps

- Implement authentication
- Add request validation
- Implement pagination
- Add more filters
- Rate limiting per user
- API versioning (v1, v2, etc.)