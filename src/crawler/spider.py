"""Crawler module: handles data fetching and document loading."""

import logging
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

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
        self.visited_urls = set() # CRITICAL: Tracks visited URLs to prevent loops
        
        self.logger = logging.getLogger(__name__)
        try:
            from requests.adapters import HTTPAdapter
            from urllib3.util.retry import Retry
            
            # --- FIX START: Configure connection pool and spoof User-Agent ---
            
            # CRITICAL: Lower the effective pool size to a reasonable limit (e.g., 20) 
            # to prevent connection flooding against strict domains like Oracle.
            # We use a hardcoded small number for the connection pool maximum size.
            POOL_SIZE_LIMIT = 20
            pool_maxsize = min(self.max_workers + 10, POOL_SIZE_LIMIT) 
            
            self.session = requests.Session()
            retries = Retry(total=5, backoff_factor=1.0, # Increased total retries, increased backoff factor
                            status_forcelist=[403, 429, 500, 502, 503, 504], # Added 403 to retry status list
                            allowed_methods=frozenset(['GET', 'POST']))
            
            # Use max_retries and pool_maxsize in the adapter
            adapter = HTTPAdapter(max_retries=retries, pool_connections=pool_maxsize, pool_maxsize=pool_maxsize)
            
            self.session.mount('http://', adapter)
            self.session.mount('https://', adapter)
            
            # Use a common browser User-Agent to avoid simple blacklists
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'
            })
            # --- FIX END ---
            
        except Exception:
            self.session = requests

    def crawl(self, urls, max_depth: int = 1, max_total_pages: int = 10000):
        """Crawl a list of URLs recursively (deep crawl).

        Args:
            urls: Initial list of URLs to start crawling from.
            max_depth: Maximum recursion level for link following (e.g., 1 = only start URLs).
            max_total_pages: Maximum number of pages to index globally before stopping.

        Returns a small statistics dict.
        """
        from datetime import datetime
        self.last_crawl_time = datetime.utcnow().isoformat()
        
        # Reset tracking data for a new crawl job
        self.visited_urls.clear()
        self.crawled_count = 0
        self.error_count = 0

        # The crawl queue stores tuples: (url, depth)
        initial_tasks = [(url, 0) for url in urls]
        # future_tasks now maps the Future object to the URL it is crawling
        future_tasks = {}
        
        self.logger.info(
            f"Crawl requested: {len(urls)} starts, Max Depth={max_depth}, Max Pages={max_total_pages}"
        )
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            
            # Start initial tasks
            for url, depth in initial_tasks:
                if self.crawled_count >= max_total_pages:
                    break
                # _crawl_and_extract needs to know the URL's current depth
                future_tasks[executor.submit(self._crawl_and_extract, url, depth, max_depth)] = depth 

            # Process futures and add new links recursively
            while future_tasks:
                future = next(as_completed(future_tasks))
                current_depth = future_tasks.pop(future)
                
                # Check for global page limit before starting new tasks
                if self.crawled_count >= max_total_pages:
                    continue

                try:
                    # result is now a list of new_links found on the page
                    new_links = future.result() 
                    
                    if not new_links:
                        continue

                    # Calculate the depth for the next generation of links
                    next_depth = current_depth + 1
                    
                    if next_depth <= max_depth:
                        for link in new_links:
                            if self.crawled_count < max_total_pages and link not in self.visited_urls:
                                
                                # Ensure only same-domain links are followed (logic is inside _crawl_and_extract during link extraction)
                                # We MUST re-add the link to visited_urls here to prevent multiple future submissions
                                with self._lock:
                                     if link in self.visited_urls:
                                        continue
                                     self.visited_urls.add(link)
                                     
                                # Submit the new link as a new task, passing the next depth
                                new_future = executor.submit(self._crawl_and_extract, link, next_depth, max_depth)
                                future_tasks[new_future] = next_depth 
                    
                except Exception as e:
                    # Error was handled and counted inside _crawl_and_extract
                    self.logger.debug(f"Task finished with warning/error. Crawl continues.")

        self.logger.info(f"Crawl job finished. Crawled {self.crawled_count} pages with {self.error_count} errors.")
        return {
            'crawled': self.crawled_count,
            'errors': self.error_count,
            'last_crawl': self.last_crawl_time,
            'requested': len(urls),
            'max_depth': max_depth
        }
    
    def _crawl_and_extract(self, url, depth, max_depth) -> list:
        """Helper to crawl a single page, index content, and return extracted links."""
        
        # NOTE: self.visited_urls check is performed before submission in crawl(), 
        # but we need a final check inside the worker thread due to concurrency.
        # This check needs to be robust, but removing the self.visited_urls.add(url) here 
        # since it's added before submission in the main loop/task submission. 
        # We rely on the check in the main loop.
        
        try:
            self.logger.debug(f"Fetching URL (Depth {depth}/{max_depth}): {url}")
            response = self.session.get(url, timeout=15) # Increased timeout slightly for large docs
            response.raise_for_status()
            
            if 'text/html' not in response.headers.get('Content-Type', ''):
                self.logger.debug(f"Skipping non-HTML content: {url}")
                return []
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # --- Indexing ---
            text = soup.get_text()
            tokens = self.tokenizer.tokenize(text)
            self.indexer.index_document(url, tokens)

            # Store Document Metadata
            if self.document_store is not None:
                title_tag = soup.title.string.strip() if soup.title and soup.title.string else url
                snippet = ' '.join(text.split()[:50])
                self.document_store.add_document(doc_id=url, url=url, title=title_tag, snippet=snippet, content_length=len(text))

            with self._lock:
                self.crawled_count += 1
            self.logger.info(f"Indexed (Depth {depth}): {url}")

            # --- Link Extraction for Recursion ---
            links = []
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                absolute_url = urljoin(url, href).split('#')[0] # Remove fragments
                
                # Only add if it's the same domain
                if self._is_same_domain(url, absolute_url):
                    links.append(absolute_url)
                    
            return links
            
        except requests.exceptions.RequestException as e:
            with self._lock:
                self.error_count += 1
            self.logger.warning(f"Fetch failed for {url}: {e}")
            
        except Exception as e:
            with self._lock:
                self.error_count += 1
            self.logger.error(f"Processing error for {url}: {e}", exc_info=True)
            
        return []

    def _get_url_depth(self, url):
        """Simple function to find the depth of a URL within the current crawl session (approximated)."""
        # This function is now OBSOLETE, but kept for compatibility.
        return len([p for p in urlparse(url).path.split('/') if p])

    def _is_same_domain(self, base_url, target_url):
        """Checks if two URLs belong to the same domain."""
        try:
            # Need to normalize scheme to ensure comparison works (e.g. http vs https)
            base_netloc = urlparse(base_url).netloc
            target_netloc = urlparse(target_url).netloc
            return base_netloc == target_netloc
        except Exception:
            return False

    def get_statistics(self):
        """Return basic crawler statistics."""
        with self._lock:
            return {
                'crawled': self.crawled_count,
                'errors': self.error_count,
                'last_crawl': self.last_crawl_time,
                'max_workers': self.max_workers,
                'visited_urls': len(self.visited_urls)
            }