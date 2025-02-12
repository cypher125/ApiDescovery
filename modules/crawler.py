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
                
                # First, check if there are any forms on the page
                forms = self.browser.driver.find_elements("tag name", "form")
                if forms:
                    self.logger.info(f"Found {len(forms)} forms on {url}")
                    # Handle each form individually
                    for form_idx, form in enumerate(forms):
                        # Reload page for each form to ensure clean state
                        if form_idx > 0:
                            self.browser.load_page(url)
                        
                        try:
                            form_results = self.browser.handle_forms()
                            for result in form_results:
                                if result["success"]:
                                    try:
                                        # Extract endpoints from form submission network events
                                        endpoints = self.extractor.extract(result["network_events"])
                                        if endpoints:
                                            discovered_endpoints.extend(endpoints)
                                            self.logger.info(f"Found endpoints from form submission on {url}")
                                    except Exception as e:
                                        self.logger.warning(f"Error extracting endpoints from form submission: {str(e)}")
                                    
                                    # Reload page to continue exploration regardless of endpoint extraction
                                    self.browser.load_page(url)
                        except Exception as e:
                            self.logger.warning(f"Error processing form: {str(e)}")
                            # Continue with the next form or page exploration
                            continue
                
                # Always continue with regular element interactions
                self.logger.info(f"Exploring clickable elements on {url}")
                elements = self.browser.find_clickable_elements()
                for element in elements:
                    try:
                        self.browser.click_element(element)
                        # Capture network traffic after interaction
                        network_events = self.network_logger.capture_requests()
                        try:
                            # Extract endpoints from captured traffic
                            endpoints = self.extractor.extract(network_events)
                            if endpoints:
                                discovered_endpoints.extend(endpoints)
                        except Exception as e:
                            self.logger.warning(f"Error extracting endpoints from click: {str(e)}")
                            continue
                            
                        # If the click caused navigation, reload the original page
                        if url != self.browser.driver.current_url:
                            self.browser.load_page(url)
                    except Exception as e:
                        self.logger.warning(f"Error interacting with element: {str(e)}")
                        continue
                
                # Find new links to crawl
                new_urls = self.browser.get_page_links()
                for new_url in new_urls:
                    if is_valid_url(new_url) and new_url not in self.visited:
                        self.queue.append((new_url, depth + 1))
                
            except Exception as e:
                self.logger.error(f"Error crawling {url}: {str(e)}")
                # Continue with next URL even if current one fails
                continue
        
        return discovered_endpoints