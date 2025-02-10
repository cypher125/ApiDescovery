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
    """Handles form detection, data population, and submission"""
    
    def __init__(self, browser_controller):
        self.browser = browser_controller
        self.data_generator = FormDataGenerator()
        
    def find_forms(self) -> List[Dict]:
        """Find all forms on the page and analyze their fields"""
        forms = []
        try:
            form_elements = self.browser.driver.find_elements("tag name", "form")
            
            for form in form_elements:
                form_data = {
                    "element": form,
                    "inputs": self._analyze_form_fields(form),
                    "submit_button": self._find_submit_button(form)
                }
                forms.append(form_data)
                
        except Exception as e:
            self.browser.logger.warning(f"Error finding forms: {str(e)}")
            
        return forms
    
    def _analyze_form_fields(self, form) -> List[Dict]:
        """Analyze all input fields in a form"""
        fields = []
        
        # Find all input elements
        input_elements = form.find_elements("tag name", "input")
        select_elements = form.find_elements("tag name", "select")
        textarea_elements = form.find_elements("tag name", "textarea")
        
        # Process input elements
        for input_elem in input_elements:
            field_type = input_elem.get_attribute("type")
            if field_type not in ["submit", "button", "hidden", "file"]:
                fields.append({
                    "element": input_elem,
                    "type": field_type,
                    "name": input_elem.get_attribute("name"),
                    "id": input_elem.get_attribute("id"),
                    "required": input_elem.get_attribute("required") is not None
                })
        
        # Process select elements
        for select_elem in select_elements:
            fields.append({
                "element": select_elem,
                "type": "select",
                "name": select_elem.get_attribute("name"),
                "id": select_elem.get_attribute("id"),
                "required": select_elem.get_attribute("required") is not None,
                "options": self._get_select_options(select_elem)
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
    
    def _find_submit_button(self, form) -> Optional[object]:
        """Find the submit button for a form"""
        try:
            # Try finding by type="submit"
            submit = form.find_element("css selector", "input[type='submit'], button[type='submit']")
            if submit:
                return submit
            
            # Try finding by common button classes or text
            button_selectors = [
                "button[class*='submit']",
                "button[class*='save']",
                "button:contains('Submit')",
                "button:contains('Save')",
                "button:contains('Search')",
                "button:contains('Login')",
                "button:contains('Register')"
            ]
            
            for selector in button_selectors:
                try:
                    button = form.find_element("css selector", selector)
                    if button:
                        return button
                except:
                    continue
                    
        except Exception as e:
            self.browser.logger.warning(f"Error finding submit button: {str(e)}")
            
        return None
    
    def populate_form(self, form_data: Dict) -> bool:
        """Populate a form with appropriate mock data"""
        try:
            for field in form_data["inputs"]:
                self._populate_field(field)
            return True
        except Exception as e:
            self.browser.logger.warning(f"Error populating form: {str(e)}")
            return False
    
    def _populate_field(self, field: Dict):
        """Populate a single form field with appropriate data"""
        try:
            element = field["element"]
            field_type = field["type"]
            
            # Handle different input types
            if field_type == "text":
                element.send_keys(self.data_generator.generate_text())
            elif field_type == "email":
                element.send_keys(self.data_generator.generate_email())
            elif field_type == "password":
                element.send_keys(self.data_generator.generate_password())
            elif field_type == "tel":
                element.send_keys(self.data_generator.generate_phone())
            elif field_type == "number":
                element.send_keys(self.data_generator.generate_number())
            elif field_type == "date":
                element.send_keys(self.data_generator.generate_date())
            elif field_type == "checkbox":
                if not element.is_selected():
                    element.click()
            elif field_type == "radio":
                if not element.is_selected():
                    element.click()
            elif field_type == "select":
                if field["options"]:
                    random_option = random.choice(field["options"])
                    random_option["element"].click()
            elif field_type == "textarea":
                element.send_keys(self.data_generator.generate_text(20, 50))
                
        except Exception as e:
            self.browser.logger.warning(f"Error populating field: {str(e)}")
    
    def submit_form(self, form_data: Dict) -> bool:
        """Submit a form and return success status"""
        try:
            if form_data["submit_button"]:
                form_data["submit_button"].click()
                return True
            else:
                # Fallback: try submitting the form using JavaScript
                self.browser.driver.execute_script("arguments[0].submit();", form_data["element"])
                return True
        except Exception as e:
            self.browser.logger.warning(f"Error submitting form: {str(e)}")
            return False