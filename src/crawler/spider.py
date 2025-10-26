"""Crawler module: handles data fetching and document loading."""

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

class Spider:
      def __init__(self, tokenizer, indexer, max_workers=9):
          self.tokenizer = tokenizer
          self.indexer = indexer
          self.max_workers = max_workers

      def crawl(self, urls):
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
              futures = {executor.submit(self._crawl_single, url): url for url in urls}
              for future in as_completed(futures):
                  url = futures[future]
                  try:
                      future.result()  # Raises exception if any
                  except Exception as e:
                      print(f"Error crawling {url}: {e}")
      def _crawl_single(self, url):
          response = requests.get(url, timeout=10)
          response.raise_for_status()
          soup = BeautifulSoup(response.text, 'html.parser')
          text = soup.get_text()
          tokens = self.tokenizer.tokenize(text)
          self.indexer.index_document(url, tokens)
  
