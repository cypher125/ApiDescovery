import re
import logging
from utils.exceptions import ExtractorException

class EndpointExtractor:
    def __init__(self, config):
        self.patterns = [re.compile(pattern) for pattern in config['patterns']]
        self.logger = logging.getLogger(__name__)

    def extract(self, network_events):
        try:
            endpoints = []
            seen = set()  # For deduplication
            
            for event in network_events:
                if event["method"] == "Network.requestWillBeSent":
                    request = event.get("params", {}).get("request", {})
                    url = request.get("url", "")
                    
                    # Check if URL matches any of our API patterns
                    if any(pattern.search(url) for pattern in self.patterns):
                        # Create unique key for deduplication
                        unique_key = f"{request.get('method')}:{url}"
                        
                        if unique_key not in seen:
                            seen.add(unique_key)
                            endpoints.append({
                                "method": request.get("method"),
                                "url": url,
                                "headers": request.get("headers"),
                                "postData": request.get("postData")
                            })
            
            return endpoints
        except Exception as e:
            raise ExtractorException(f"Failed to extract endpoints: {str(e)}")