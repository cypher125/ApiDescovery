from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging, time
from selenium.webdriver.chrome.service import Service
from utils.exceptions import BrowserException
from webdriver_manager.chrome import ChromeDriverManager
from utils.form_handler import FormHandler

class BrowserController:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.setup_browser()
        self.form_handler = FormHandler(self)

    def handle_forms(self):
        """Find and interact with all forms on the page"""
        forms_data = []
        try:
            # Find all forms
            forms = self.form_handler.find_forms()
            
            for form in forms:
                form_result = {
                    "success": False,
                    "network_events": []
                }
                
                # Store current URL before form submission
                current_url = self.driver.current_url
                
                # Try to populate and submit the form
                if self.form_handler.populate_form(form):
                    # Clear existing network logs before submission
                    self.driver.get_log('performance')
                    
                    # Submit the form
                    if self.form_handler.submit_form(form):
                        # Wait for network activity to settle
                        time.sleep(2)
                        
                        # Capture network events
                        form_result["success"] = True
                        form_result["network_events"] = self.get_performance_logs()
                        
                        # If form submission caused navigation, note it
                        form_result["caused_navigation"] = current_url != self.driver.current_url
                
                forms_data.append(form_result)
                
        except Exception as e:
            self.logger.warning(f"Error handling forms: {str(e)}")
            
        return forms_data

    def setup_browser(self):
        try:
            chrome_options = Options()
            if self.config.get('headless', True):
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--disable-fonts")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument(f"user-agent={self.config.get('user_agent')}")
            chrome_options.add_experimental_option("perfLoggingPrefs", {
                "enableNetwork": True,
                "enablePage": False,
            })
            chrome_options.set_capability(
                "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
            )
            #service = Service('./drivers/chromedriver')
            # Use WebDriver Manager to automatically manage ChromeDriver
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_script_timeout(self.config.get('timeout', 30))
            self.wait = WebDriverWait(self.driver, self.config.get('timeout', 30))
        except Exception as e:
            raise BrowserException(f"Failed to initialize browser: {str(e)}")

    def load_page(self, url):
        try:
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        except Exception as e:
            raise BrowserException(f"Failed to load page {url}: {str(e)}")

    def find_clickable_elements(self):
        """Enhanced method to find truly clickable elements."""
        try:
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Find all potentially clickable elements
            elements = self.driver.find_elements(By.CSS_SELECTOR, 
                "button, [role='button'], a, input[type='submit'], [onclick], [class*='btn'], [class*='button']")
            
            # Filter for actually clickable elements
            clickable_elements = []
            for elem in elements:
                try:
                    if (elem.is_displayed() and 
                        elem.is_enabled() and 
                        self.wait_for_element_clickable(elem, timeout=2)):
                        clickable_elements.append(elem)
                except:
                    continue
                    
            return clickable_elements
        except Exception as e:
            self.logger.warning(f"Error finding clickable elements: {str(e)}")
            return []
        
    def wait_for_element_clickable(self, element, timeout=10):
        """Wait for an element to become clickable."""
        try:
            # Wait for the element to be visible and enabled
            end_time = time.time() + timeout
            while time.time() < end_time:
                if element.is_displayed() and element.is_enabled():
                    # Check if element is not overlapped
                    overlapping = self.driver.execute_script("""
                        var elem = arguments[0];
                        var rect = elem.getBoundingClientRect();
                        var cx = rect.left + rect.width/2;
                        var cy = rect.top + rect.height/2;
                        var element = document.elementFromPoint(cx, cy);
                        return element !== elem && !elem.contains(element);
                    """, element)
                    
                    if not overlapping:
                        return True
                time.sleep(0.5)
            return False
        except:
            return False
    
    def remove_overlays(self):
        """Remove potential overlay elements that might intercept clicks."""
        overlays = [
            ".modal", ".overlay", ".popup", ".dialog",
            "[role='dialog']", "[aria-modal='true']",
            ".fixed", ".absolute"
        ]
        
        for selector in overlays:
            try:
                self.driver.execute_script("""
                    document.querySelectorAll(arguments[0]).forEach(elem => {
                        if (window.getComputedStyle(elem).display !== 'none') {
                            elem.remove();
                        }
                    });
                """, selector)
            except:
                continue

    def click_element(self, element, retries=3):
        """Enhanced click function with multiple fallback methods."""
        for attempt in range(retries):
            try:
                # Remove any overlays that might intercept the click
                self.remove_overlays()
                
                # Scroll element into view
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                time.sleep(1)  # Wait for scroll to complete
                
                # Wait for element to be clickable
                if not self.wait_for_element_clickable(element):
                    raise Exception("Element not clickable after waiting")
                
                # Try multiple click methods
                try:
                    # Regular click
                    element.click()
                    return True
                except:
                    try:
                        # JavaScript click
                        self.driver.execute_script("arguments[0].click();", element)
                        return True
                    except:
                        # Force click with JavaScript
                        self.driver.execute_script("""
                            var evt = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            arguments[0].dispatchEvent(evt);
                        """, element)
                        return True
                        
            except Exception as e:
                if attempt == retries - 1:
                    raise BrowserException(f"Failed to click element: {str(e)}")
                
                # If element is stale, try to re-locate it
                try:
                    # Assuming you have a way to re-locate the element
                    # This is just an example using XPath, adjust according to your needs
                    xpath = self.driver.execute_script("""
                        function getXPath(element) {
                            if (element.id !== '')
                                return `//*[@id="${element.id}"]`;
                            if (element === document.body)
                                return '/html/body';
                            var ix = 0;
                            var siblings = element.parentNode.childNodes;
                            for (var i = 0; i < siblings.length; i++) {
                                var sibling = siblings[i];
                                if (sibling === element)
                                    return getXPath(element.parentNode) + '/' + element.tagName.toLowerCase() + '[' + (ix + 1) + ']';
                                if (sibling.nodeType === 1 && sibling.tagName === element.tagName)
                                    ix++;
                            }
                        }
                        return getXPath(arguments[0]);
                    """, element)
                    element = self.driver.find_element(By.XPATH, xpath)
                except:
                    pass
                
                time.sleep(1)  # Wait before retry
                
        return False

    def get_page_links(self):
        try:
            elements = self.driver.find_elements(By.TAG_NAME, "a")
            return [elem.get_attribute('href') for elem in elements if elem.get_attribute('href')]
        except Exception as e:
            self.logger.warning(f"Error getting page links: {str(e)}")
            return []

    def get_performance_logs(self):
        return self.driver.get_log('performance')

    def shutdown(self):
        if hasattr(self, 'driver'):
            self.driver.quit()