import logging
import yaml
from pathlib import Path
from modules.crawler import Crawler
from modules.browser_automation import BrowserController
from modules.network_monitor import NetworkLogger
from modules.data_extractor import EndpointExtractor
from modules.reporting import ReportGenerator

def load_config(path='config.yaml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def setup_logging(level):
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.StreamHandler()
        ]
    )

def main():
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(config.get('log_level', 'INFO'))
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize components
        browser = BrowserController(config['browser'])
        network_logger = NetworkLogger(browser)
        extractor = EndpointExtractor(config['api'])
        reporter = ReportGenerator(config['output'])
        
        # Initialize crawler with dependencies
        crawler = Crawler(
            start_url=config['target_url'],
            browser=browser,
            network_logger=network_logger,
            extractor=extractor,
            max_depth=config.get('max_depth', 2)
        )
        
        # Start crawling and collect endpoints
        logger.info("Starting crawl process...")
        endpoints = crawler.start()
        
        # Generate report
        reporter.generate(endpoints)
        logger.info("Crawl completed successfully")
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise
    
    finally:
        # Cleanup
        browser.shutdown()

if __name__ == "__main__":
    main()