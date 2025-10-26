"""Entry point for the search engine project."""
from src.crawler.spider import Spider
from src.indexing.indexer import Indexer
from src.processing.tokenizer import Tokenizer
from src.ranking.ranker import Ranker
from src.storage.database import Database
from src.web.app import app

def main():
      # Initialize components
      tokenizer = Tokenizer()
      database = Database()
      indexer = Indexer(tokenizer, database)
      ranker = Ranker(database)
      spider = Spider(tokenizer, indexer)

      # Crawl sample URLs (replace with real ones)
      urls = ["https://example.com", "https://example.org"]
      spider.crawl(urls)

      # Start web app
      app.run(debug=True)

if __name__ == "__main__":
      main()
