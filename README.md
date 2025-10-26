# Search Engine Project

A simple web search engine built with Python, featuring crawling, indexing, ranking, and a Flask-based web UI.

## Features
- **Crawler**: Concurrently fetches and processes web pages.
- **Indexer**: Builds an inverted index for fast searches.
- **Processor**: Tokenizes and normalizes text.
- **Ranker**: Scores results using TF-IDF.
- **Storage**: Saves/loads index via JSON.
- **Web UI**: Basic search interface with Flask.

## Installation
1. Clone or download the project.
2. Install dependencies: `pip install flask requests beautifulsoup4`.
3. Run the project: `python main.py`.

## Usage
- The app starts on `http://localhost:5000`.
- Enter a query in the search box to get ranked results.
- To crawl more pages, edit `urls` in `main.py` and re-run.

## Project Structure
- `main.py`: Entry point.
- `src/`: Core modules (crawler, indexing, etc.).
- `src/web/`: Flask app and static files.
- `tests/`: Unit tests.

## Contributing
- Add more ranking algorithms (e.g., BM25).
- Improve UI with advanced features.

## License
MIT License.