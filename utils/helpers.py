from urllib.parse import urlparse, urljoin

def is_valid_url(url):
    """Check if a URL is valid and should be crawled"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def normalize_url(base_url, url):
    """Normalize relative URLs to absolute URLs"""
    return urljoin(base_url, url)