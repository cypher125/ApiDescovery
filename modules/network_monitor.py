import json
import logging
from utils.exceptions import NetworkMonitorException

class NetworkLogger:
    def __init__(self, browser_controller):
        self.browser = browser_controller
        self.logger = logging.getLogger(__name__)

    def capture_requests(self):
        try:
            logs = self.browser.get_performance_logs()
            network_events = []
            
            for entry in logs:
                log = json.loads(entry["message"])["message"]
                if "Network." in log["method"]:
                    network_events.append(log)
            
            return network_events
        except Exception as e:
            raise NetworkMonitorException(f"Failed to capture network traffic: {str(e)}")