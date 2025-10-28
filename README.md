# Search Engine

A concurrent web crawler and search engine implementation with a Flask web interface. Features inverted index-based search with TF-IDF ranking and thread-safe operations.

## Features

- **Concurrent Crawling**: Multi-threaded web crawler using ThreadPoolExecutor
- **Thread-safe Indexing**: In-memory inverted index with background auto-flush
- **Efficient Storage**: Atomic file operations for index persistence
- **TF-IDF Ranking**: Document scoring based on term frequency and inverse document frequency
- **Clean Architecture**: Modular design with separation of concerns
- **Web Interface**: Flask-based search UI
- **Comprehensive Tests**: Unit tests covering core functionality

## Project Structure

```
Search-Engine/
├── src/
│   ├── crawler/          # Web crawler implementation
│   │   └── spider.py     # Concurrent webpage fetcher
│   ├── indexing/         # Indexing logic
│   │   └── indexer.py    # Thread-safe inverted index
│   ├── processing/       # Text processing
│   │   └── tokenizer.py  # Document tokenization
│   ├── ranking/          # Search ranking
│   │   └── ranker.py     # TF-IDF implementation
│   ├── storage/          # Persistence layer
│   │   └── database.py   # JSON-based storage
│   └── web/             # Web interface
│       ├── app.py       # Flask application
│       ├── templates/   # HTML templates
│       └── static/      # CSS/JS assets
├── tests/               # Unit tests
├── requirements.txt     # Project dependencies
└── main.py             # Application entry point
```

## Quick Start

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

4. Open http://127.0.0.1:5000 in your browser

## Development Setup

1. Install development dependencies:
```bash
pip install pytest pytest-cov
```

2. Run tests:
```bash
python -m pytest tests/
```

## Implementation Details

### Crawler (src/crawler/spider.py)
- Concurrent webpage fetching using ThreadPoolExecutor
- HTML parsing with BeautifulSoup4
- Error handling for network issues
- Configurable max workers

### Indexer (src/indexing/indexer.py)
- Thread-safe inverted index implementation
- Optional background auto-flush capability
- Memory-first with configurable persistence
- Atomic updates using locks

### Ranking (src/ranking/ranker.py)
- TF-IDF scoring implementation
- Document frequency normalization
- Sorted results by relevance score

### Storage (src/storage/database.py)
- JSON-based persistent storage
- Atomic write operations
- Thread-safe implementation
- Graceful handling of missing/corrupt files

## Configuration

The search engine is configured through environment variables. Copy `.env.example` to `.env` to get started:

```bash
cp .env.example .env
```

Available configuration options:

### Flask Application
- `FLASK_ENV`: Set to 'development' for debug mode
- `FLASK_APP`: Application entry point
- `FLASK_PORT`: Web interface port (default: 5000)
- `FLASK_DEBUG`: Enable debug mode

### Crawler
- `MAX_WORKERS`: Number of concurrent crawler threads
- `CRAWL_TIMEOUT`: Request timeout in seconds
- `MAX_PAGES_PER_DOMAIN`: Page limit per domain
- `RESPECT_ROBOTS_TXT`: Whether to check robots.txt
- `USER_AGENT`: Crawler identification string

### Indexer
- `INDEX_FILE`: Path to store the inverted index
- `AUTO_FLUSH`: Enable background auto-flush
- `FLUSH_INTERVAL`: Seconds between flushes
- `MAX_INDEX_SIZE`: Term limit in index

### Storage
- `STORAGE_DIR`: Data directory path
- `BACKUP_ENABLED`: Enable index backups
- `BACKUP_INTERVAL`: Backup frequency in seconds

### Ranking
- `MIN_TERM_FREQUENCY`: Minimum term frequency to index
- `MAX_RESULTS`: Maximum search results to return

### Debug
- `LOG_LEVEL`: Logging verbosity
- `PROFILE_ENABLED`: Enable performance profiling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and ensure they pass
5. Submit a pull request

Improvement ideas:
- Add BM25 ranking algorithm
- Implement robots.txt compliance
- Add query suggestions
- Improve UI/UX
- Add more comprehensive tests

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

Run with coverage:
```bash
python -m pytest --cov=src tests/
```

## License

MIT License - see LICENSE file for details.