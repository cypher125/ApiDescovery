import json
import logging
from pathlib import Path
from utils.exceptions import ReportingException

class ReportGenerator:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def generate(self, endpoints):
        try:
            output_path = Path(self.config['path'])
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            report = {
                "total_endpoints": len(endpoints),
                "endpoints": endpoints
            }
            
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
                
            self.logger.info(f"Report generated successfully at {output_path}")
        except Exception as e:
            raise ReportingException(f"Failed to generate report: {str(e)}")