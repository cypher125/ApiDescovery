# New utility file: utils/form_handler.py
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional

class FormDataGenerator:
    
    """Generates appropriate mock data for different form field types"""
    
    @staticmethod
    def generate_text(min_length=5, max_length=10) -> str:
        length = random.randint(min_length, max_length)
        return ''.join(random.choices(string.ascii_letters, k=length))
    
    @staticmethod
    def generate_email() -> str:
        username = ''.join(random.choices(string.ascii_lowercase, k=8))
        domain = ''.join(random.choices(string.ascii_lowercase, k=6))
        return f"{username}@{domain}.com"
    
    @staticmethod
    def generate_password() -> str:
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(random.choices(chars, k=12))
    
    @staticmethod
    def generate_phone() -> str:
        return f"+1{''.join(random.choices(string.digits, k=10))}"
    
    @staticmethod
    def generate_number(min_val=1, max_val=100) -> str:
        return str(random.randint(min_val, max_val))
    
    @staticmethod
    def generate_date() -> str:
        start_date = datetime.now() - timedelta(days=365*5)  # 5 years ago
        end_date = datetime.now() + timedelta(days=365)      # 1 year ahead
        time_between = end_date - start_date
        random_days = random.randint(0, time_between.days)
        random_date = start_date + timedelta(days=random_days)
        return random_date.strftime('%Y-%m-%d')

class FormHandler:
    def __init__(self, logger=None):
        self.logger = logger

    def _find_submit_button(self, form) -> Optional[object]:
        """Find the submit button for a form"""
        try:
            # List of possible submit button identifiers
            submit_indicators = [
                # By type
                "input[type='submit']",
                "button[type='submit']",
                # By common class names
                "[class*='submit']",
                "[class*='btn']",
                "[class*='button']",
                # By common text content (case insensitive)
                "button",
                "input[type='button']"
            ]
            
            # Common button text patterns
            button_texts = ['submit', 'search', 'login', 'register', 'sign in', 'sign up', 'send']
            
            # Try finding by selectors first
            for selector in submit_indicators:
                elements = form.find_elements("css selector", selector)
                for element in elements:
                    # Check if the element's text content matches any of our patterns
                    element_text = element.get_attribute("value") or element.text
                    if element_text:
                        element_text = element_text.lower()
                        if any(text in element_text for text in button_texts):
                            return element
            
            # If no button found by text, try finding any button or input that looks like a submit
            for selector in submit_indicators:
                elements = form.find_elements("css selector", selector)
                if elements:
                    return elements[0]  # Return the first matching element
                    
            # Last resort: try to find any button within the form
            buttons = form.find_elements("tag name", "button")
            if buttons:
                return buttons[0]
            
        except Exception as e:
            self.browser.logger.warning(f"Error finding submit button: {str(e)}")
            
        return None
    
    def _analyze_form_fields(self, form):
        """Analyze all input fields in a form"""
        
        fields = []
        
        try:
            # Capture form method
            form_method = form.get_attribute("method") or "get"

            # Find all input elements
            input_elements = form.find_elements("tag name", "input")
            select_elements = form.find_elements("tag name", "select")
            textarea_elements = form.find_elements("tag name", "textarea")

            # Add form metadata
            fields.append({
                "form_method": form_method.upper(),
                "form_action": form.get_attribute("action") or ""
            })
            
            # Process input elements
            for input_elem in input_elements:
                field_type = input_elem.get_attribute("type")
                if field_type not in ["submit", "button", "hidden", "file"]:
                    fields.append({
                        "element": input_elem,
                        "type": field_type or "text",  # Default to text if type is not specified
                        "name": input_elem.get_attribute("name"),
                        "id": input_elem.get_attribute("id"),
                        "required": input_elem.get_attribute("required") is not None
                    })
            
            # Process select elements
            for select_elem in select_elements:
                options = select_elem.find_elements("tag name", "option")
                option_values = []
                for option in options:
                    if option.get_attribute("value"):
                        option_values.append({
                            "element": option,
                            "value": option.get_attribute("value"),
                            "text": option.text
                        })
                
                if option_values:  # Only add select fields that have valid options
                    fields.append({
                        "element": select_elem,
                        "type": "select",
                        "name": select_elem.get_attribute("name"),
                        "id": select_elem.get_attribute("id"),
                        "required": select_elem.get_attribute("required") is not None,
                        "options": option_values
                    })
            
            # Process textarea elements
            for textarea_elem in textarea_elements:
                fields.append({
                    "element": textarea_elem,
                    "type": "textarea",
                    "name": textarea_elem.get_attribute("name"),
                    "id": textarea_elem.get_attribute("id"),
                    "required": textarea_elem.get_attribute("required") is not None
                })
                
        except Exception as e:
            self.logger.warning(f"Error analyzing form fields: {str(e)}")
            
        return fields
    
    def _get_select_options(self, select_element) -> List[Dict]:
        """Get all options from a select element"""
        options = []
        try:
            option_elements = select_element.find_elements("tag name", "option")
            for option in option_elements:
                if option.get_attribute("value"):  # Skip empty options
                    options.append({
                        "element": option,
                        "value": option.get_attribute("value"),
                        "text": option.text
                    })
        except Exception as e:
            self.browser.logger.warning(f"Error getting select options: {str(e)}")
        return options
    
    def _find_submit_button(self, form):
        """Find the submit button for a form"""
        try:
            # Common submit button identifiers
            submit_selectors = [
                "input[type='submit']",
                "button[type='submit']",
                "button:contains('Submit')",
                "button:contains('Login')",
                "button:contains('Sign In')",
                "button:contains('Register')",
                "button:contains('Search')",
                "button:contains('Send')",
                "[class*='submit']",
                "[class*='login']",
                "[class*='search']"
            ]
            
            # Try each selector
            for selector in submit_selectors:
                try:
                    elements = form.find_elements("css selector", selector)
                    if elements:
                        return elements[0]
                except:
                    continue
            
            # If no specific submit button found, look for any button in the form
            buttons = form.find_elements("tag name", "button")
            if buttons:
                return buttons[0]
            
            inputs = form.find_elements("tag name", "input")
            for input_elem in inputs:
                if input_elem.get_attribute("type") in ["submit", "button"]:
                    return input_elem
                    
        except Exception as e:
            self.logger.warning(f"Error finding submit button: {str(e)}")
            
        return None
    
    def _populate_form(self, form_data):
        """Populate a form with mock data"""
        try:
            for field in form_data["inputs"]:
                self._populate_field(field)
            return True
        except Exception as e:
            self.logger.warning(f"Error populating form: {str(e)}")
            return False

    def _populate_field(self, field):
        """Populate a single form field with appropriate mock data"""
        try:
            element = field["element"]
            field_type = field["type"]
            
            # Clear any existing value first
            element.clear()
            
            # Generate and input appropriate mock data based on field type
            if field_type == "email":
                element.send_keys("test@example.com")
            elif field_type == "password":
                element.send_keys("TestPassword123!")
            elif field_type == "tel":
                element.send_keys("1234567890")
            elif field_type == "number":
                element.send_keys("12345")
            elif field_type == "date":
                element.send_keys("2024-02-11")
            elif field_type == "checkbox":
                if not element.is_selected():
                    element.click()
            elif field_type == "radio":
                if not element.is_selected():
                    element.click()
            elif field_type == "select":
                if field["options"]:
                    # Select the first non-empty option
                    field["options"][0]["element"].click()
            elif field_type == "textarea":
                element.send_keys("This is a test message")
            else:  # Default to text input
                element.send_keys("TestInput")
                
            self.logger.info(f"Populated {field_type} field with mock data")
                
        except Exception as e:
            self.logger.warning(f"Error populating field: {str(e)}")
    

    def _submit_form(self, form_data):
        """Submit a form and return success status"""
        try:
            if form_data["submit_button"]:
                # Try clicking the button first
                try:
                    form_data["submit_button"].click()
                    self.logger.info("Form submitted via button click")
                    return True
                except:
                    # If clicking fails, try JavaScript click
                    try:
                        self.driver.execute_script("arguments[0].click();", form_data["submit_button"])
                        self.logger.info("Form submitted via JavaScript click")
                        return True
                    except:
                        pass
            
            # If button click fails or no button found, try submitting the form directly
            try:
                self.driver.execute_script("arguments[0].submit();", form_data["element"])
                self.logger.info("Form submitted via JavaScript form.submit()")
                return True
            except Exception as e:
                self.logger.warning(f"Failed to submit form: {str(e)}")
                return False
                
        except Exception as e:
            self.logger.warning(f"Error in submit_form: {str(e)}")
            return False

