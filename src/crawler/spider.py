"""Crawler module: handles data fetching and document loading."""

import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

class Spider:
    def __init__(self, tokenizer, indexer, document_store=None, max_workers=9):
        """Simple web spider used by the project.

        Args:
            tokenizer: Tokenizer instance (must provide tokenize())
            indexer: Indexer instance (must provide index_document())
            document_store: optional DocumentStore-like object for metadata
            max_workers: max concurrent threads for crawling
        """
        self.tokenizer = tokenizer
        self.indexer = indexer
        self.document_store = document_store
        self.max_workers = max_workers
        # runtime statistics
        import threading
        self._lock = threading.Lock()
        self.crawled_count = 0
        self.error_count = 0
        self.last_crawl_time = None
        # module logger
        self.logger = logging.getLogger(__name__)
        # requests session with retries to handle transient network errors
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            self.session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.5,
                            status_forcelist=[429, 500, 502, 503, 504],
                            allowed_methods=frozenset(['GET', 'POST']))
            adapter = HTTPAdapter(max_retries=retries)
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
            # sensible default headers
            self.session.headers.update({'User-Agent': 'SearchEngineBot/1.0 (+https://example.com)'})
        except Exception:
            # fall back to top-level requests if session setup fails
            self.session = requests

    def crawl(self, urls, max_pages: int = 100):
        """Crawl a list of URLs (concurrently).

        Returns a small statistics dict.
        """
        from datetime import datetime
        self.last_crawl_time = datetime.utcnow().isoformat()
        to_crawl = list(urls)[:max_pages]
        self.logger.info(f"Crawl requested for {len(to_crawl)} URLs (max_pages={max_pages})")
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._crawl_single, url): url for url in to_crawl}
            for future in as_completed(futures):
                url = futures[future]
                try:
                    future.result()  # Raises exception if any
                except Exception as e:
                    with self._lock:
                        self.error_count += 1
                    # keep crawling others
        return {
            'crawled': self.crawled_count,
            'errors': self.error_count,
            'last_crawl': self.last_crawl_time,
            'requested': len(to_crawl)
        }
    def _crawl_single(self, url):
        # Fetch and process a single URL. Log on success/failure for easier debugging.
        try:
            self.logger.debug(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            tokens = self.tokenizer.tokenize(text)

            # index document by URL
            try:
                self.indexer.index_document(url, tokens)
                # store minimal metadata if document_store present
                if self.document_store is not None:
                    title_tag = soup.title.string.strip() if soup.title and soup.title.string else url
                    snippet = ' '.join(text.split()[:50])
                    try:
                        self.document_store.add_document(doc_id=url,
                                                         url=url,
                                                         title=title_tag,
                                                         snippet=snippet,
                                                         content_length=len(text))
                    except Exception:
                        # ignore document store errors
                        pass
                with self._lock:
                    self.crawled_count += 1
                self.logger.info(f"Crawled: {url}")
            except Exception as e:
                with self._lock:
                    self.error_count += 1
                self.logger.warning(f"Indexing failed for {url}: {e}")
        except Exception as e:
            with self._lock:
                self.error_count += 1
            self.logger.warning(f"Failed to fetch {url}: {e}")

    def get_statistics(self):
        """Return basic crawler statistics."""
        with self._lock:
            return {
                'crawled': self.crawled_count,
                'errors': self.error_count,
                'last_crawl': self.last_crawl_time,
                'max_workers': self.max_workers
            }
  
