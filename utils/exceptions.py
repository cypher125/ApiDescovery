class CrawlerException(Exception):
    """Base exception for crawler errors"""
    pass

class BrowserException(Exception):
    """Exception for browser automation errors"""
    pass

class NetworkMonitorException(Exception):
    """Exception for network monitoring errors"""
    pass

class ExtractorException(Exception):
    """Exception for endpoint extraction errors"""
    pass

class ReportingException(Exception):
    """Exception for reporting errors"""
    pass