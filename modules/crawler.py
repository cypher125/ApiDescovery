from urllib.parse import urljoin, urlparse
import logging
from collections import deque
from utils.helpers import is_valid_url
from utils.exceptions import CrawlerException

class Crawler:
    def __init__(self, start_url, browser, network_logger, extractor, max_depth=2):
        self.start_url = start_url
        self.browser = browser
        self.network_logger = network_logger
        self.extractor = extractor
        self.max_depth = max_depth
        self.visited = set()
        self.queue = deque([(start_url, 0)])  # (url, depth)
        self.logger = logging.getLogger(__name__)

    def start(self):
        discovered_endpoints = []
        
        while self.queue:
            url, depth = self.queue.popleft()
            
            if depth > self.max_depth or url in self.visited:
                continue
                
            self.visited.add(url)
            
            try:
                # Load page and capture network traffic
                self.browser.load_page(url)
                
                # Find and interact with elements
                elements = self.browser.find_clickable_elements()
                for element in elements:
                    try:
                        self.browser.click_element(element)
                        # Capture network traffic after interaction
                        network_events = self.network_logger.capture_requests()
                        # Extract endpoints from captured traffic
                        endpoints = self.extractor.extract(network_events)
                        discovered_endpoints.extend(endpoints)
                    except Exception as e:
                        self.logger.warning(f"Error interacting with element: {str(e)}")
                
                # Find new links to crawl
                new_urls = self.browser.get_page_links()
                for new_url in new_urls:
                    if is_valid_url(new_url) and new_url not in self.visited:
                        self.queue.append((new_url, depth + 1))
                
            except Exception as e:
                self.logger.error(f"Error crawling {url}: {str(e)}")
        
        return discovered_endpoints