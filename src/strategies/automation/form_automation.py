#!/usr/bin/env python3
"""
Form Automation Strategy
Automated form detection, completion, and submission

Examples:
- Automatically fill out contact forms for lead generation
- Submit search forms to access hidden content
- Complete registration forms for data access
- Handle multi-step form wizards
"""

import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.automation.form_automation")


class FormAutoStrategy(BaseExtractionStrategy):
    """
    Automated form detection, completion, and submission
    
    Examples:
    - Automatically fill out contact forms for lead generation
    - Submit search forms to access hidden content
    - Complete registration forms for data access
    - Handle multi-step form wizards
    """
    
    def __init__(self, form_data: Dict[str, Any] = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.form_data = form_data or {}
        
        # Common form field patterns
        self.field_patterns = {
            "email": [
                "email", "e-mail", "mail", "user_email", "contact_email"
            ],
            "name": [
                "name", "full_name", "first_name", "last_name", "username", "contact_name"
            ],
            "phone": [
                "phone", "telephone", "mobile", "contact_phone", "phone_number"
            ],
            "company": [
                "company", "organization", "business", "company_name"
            ],
            "message": [
                "message", "comment", "inquiry", "question", "description"
            ],
            "subject": [
                "subject", "topic", "title", "regarding"
            ]
        }
        
        # Default form data
        self.default_data = {
            "email": "contact@example.com",
            "name": "John Smith",
            "phone": "555-123-4567",
            "company": "Example Corp",
            "message": "I am interested in learning more about your services.",
            "subject": "Business Inquiry"
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect and analyze forms
            forms_data = self._analyze_forms(soup, url)
            
            # Determine which forms to fill
            target_forms = self._select_target_forms(forms_data, purpose)
            
            # Create form completion plan
            completion_plan = self._create_completion_plan(target_forms, context)
            
            extracted_data = {
                "forms_detected": len(forms_data),
                "target_forms": len(target_forms),
                "completion_plan": completion_plan,
                "forms_analysis": forms_data
            }
            
            # If this is just analysis, return the plan
            if context and context.get("analyze_only", True):
                extracted_data["action_required"] = "Form completion requires browser automation"
            
            confidence = 0.8 if target_forms else 0.3
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(target_forms),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="FormAutoStrategy",
                execution_time=execution_time,
                metadata={
                    "forms_found": len(forms_data),
                    "actionable_forms": len(target_forms)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="FormAutoStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _analyze_forms(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """Analyze all forms on the page"""
        forms_data = []
        
        forms = soup.find_all('form')
        
        for i, form in enumerate(forms):
            form_info = {
                "form_id": form.get('id', f'form_{i}'),
                "action": form.get('action', ''),
                "method": form.get('method', 'GET').upper(),
                "fields": [],
                "submit_buttons": [],
                "form_type": "unknown"
            }
            
            # Make action URL absolute
            if form_info["action"]:
                form_info["action"] = urljoin(base_url, form_info["action"])
            
            # Analyze form fields
            fields = form.find_all(['input', 'textarea', 'select'])
            for field in fields:
                field_info = self._analyze_form_field(field)
                if field_info:
                    form_info["fields"].append(field_info)
            
            # Find submit buttons
            submit_buttons = form.find_all(['input', 'button'], type=['submit', 'button'])
            for button in submit_buttons:
                button_info = {
                    "type": button.get('type', 'button'),
                    "name": button.get('name', ''),
                    "value": button.get('value', ''),
                    "text": button.get_text(strip=True)
                }
                form_info["submit_buttons"].append(button_info)
            
            # Determine form type
            form_info["form_type"] = self._classify_form(form_info)
            
            forms_data.append(form_info)
        
        return forms_data
    
    def _analyze_form_field(self, field) -> Optional[Dict[str, Any]]:
        """Analyze individual form field"""
        field_type = field.get('type', 'text')
        
        # Skip hidden and submit fields
        if field_type in ['hidden', 'submit', 'button']:
            return None
        
        field_info = {
            "tag": field.name,
            "type": field_type,
            "name": field.get('name', ''),
            "id": field.get('id', ''),
            "placeholder": field.get('placeholder', ''),
            "required": field.has_attr('required'),
            "value": field.get('value', ''),
            "label": self._find_field_label(field),
            "field_purpose": "unknown"
        }
        
        # Determine field purpose
        field_info["field_purpose"] = self._classify_field_purpose(field_info)
        
        return field_info
    
    def _find_field_label(self, field) -> str:
        """Find label associated with form field"""
        # Check for label tag
        field_id = field.get('id')
        if field_id:
            label = field.find_parent().find('label', attrs={'for': field_id})
            if label:
                return label.get_text(strip=True)
        
        # Check for wrapping label
        label_parent = field.find_parent('label')
        if label_parent:
            return label_parent.get_text(strip=True).replace(field.get('value', ''), '').strip()
        
        # Check for adjacent text
        previous = field.find_previous_sibling(string=True)
        if previous:
            text = previous.strip()
            if text and len(text) < 50:
                return text
        
        return ""
    
    def _classify_field_purpose(self, field_info: Dict[str, Any]) -> str:
        """Classify the purpose of a form field"""
        
        # Combine all text sources for analysis
        text_sources = [
            field_info.get("name", "").lower(),
            field_info.get("id", "").lower(),
            field_info.get("placeholder", "").lower(),
            field_info.get("label", "").lower()
        ]
        
        combined_text = " ".join(text_sources)
        
        # Check against known patterns
        for purpose, patterns in self.field_patterns.items():
            if any(pattern in combined_text for pattern in patterns):
                return purpose
        
        # Special cases based on field type
        field_type = field_info.get("type", "")
        if field_type == "email":
            return "email"
        elif field_type == "tel":
            return "phone"
        elif field_type == "password":
            return "password"
        elif field_info.get("tag") == "textarea":
            return "message"
        
        return "unknown"
    
    def _classify_form(self, form_info: Dict[str, Any]) -> str:
        """Classify the type of form"""
        
        # Analyze field purposes
        field_purposes = [field["field_purpose"] for field in form_info["fields"]]
        
        # Contact forms
        if "email" in field_purposes and ("message" in field_purposes or "name" in field_purposes):
            return "contact_form"
        
        # Search forms
        if any("search" in field.get("name", "").lower() for field in form_info["fields"]):
            return "search_form"
        
        # Login forms
        if "password" in field_purposes and ("email" in field_purposes or "name" in field_purposes):
            return "login_form"
        
        # Registration forms
        if field_purposes.count("email") >= 1 and len(field_purposes) > 3:
            return "registration_form"
        
        # Newsletter forms
        if "email" in field_purposes and len(field_purposes) <= 2:
            return "newsletter_form"
        
        return "unknown"
    
    def _select_target_forms(self, forms_data: List[Dict[str, Any]], purpose: str) -> List[Dict[str, Any]]:
        """Select forms that match the extraction purpose"""
        
        target_forms = []
        
        for form in forms_data:
            form_type = form["form_type"]
            
            # Select forms based on purpose
            if purpose == "contact_discovery" and form_type in ["contact_form", "newsletter_form"]:
                target_forms.append(form)
            elif purpose == "lead_generation" and form_type in ["contact_form", "registration_form"]:
                target_forms.append(form)
            elif purpose == "data_access" and form_type in ["search_form", "registration_form"]:
                target_forms.append(form)
            elif purpose == "form_automation":
                target_forms.append(form)  # Include all forms
        
        return target_forms
    
    def _create_completion_plan(self, target_forms: List[Dict[str, Any]], context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Create plan for completing target forms"""
        
        completion_plan = []
        
        # Get form data from context or use defaults
        form_data = context.get("form_data", {}) if context else {}
        combined_data = {**self.default_data, **self.form_data, **form_data}
        
        for form in target_forms:
            plan = {
                "form_id": form["form_id"],
                "form_type": form["form_type"],
                "action": form["action"],
                "method": form["method"],
                "completion_steps": []
            }
            
            # Create completion steps for each field
            for field in form["fields"]:
                field_purpose = field["field_purpose"]
                
                if field_purpose in combined_data:
                    step = {
                        "action": "fill_field",
                        "selector": self._create_field_selector(field),
                        "value": combined_data[field_purpose],
                        "field_name": field["name"],
                        "field_type": field["type"]
                    }
                    plan["completion_steps"].append(step)
            
            # Add submit step
            if form["submit_buttons"]:
                submit_button = form["submit_buttons"][0]  # Use first submit button
                plan["completion_steps"].append({
                    "action": "submit_form",
                    "button_text": submit_button["text"],
                    "button_type": submit_button["type"]
                })
            
            completion_plan.append(plan)
        
        return completion_plan
    
    def _create_field_selector(self, field: Dict[str, Any]) -> str:
        """Create CSS selector for form field"""
        
        if field["id"]:
            return f"#{field['id']}"
        elif field["name"]:
            return f"[name='{field['name']}']"
        else:
            # Fallback selector
            return f"{field['tag']}[type='{field['type']}']"
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Form strategy confidence based on form presence"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        forms = soup.find_all('form')
        
        if not forms:
            return 0.1
        
        # Higher confidence for relevant purposes
        if purpose in ["contact_discovery", "lead_generation", "form_automation"]:
            return 0.8
        
        return 0.5
    
    def supports_purpose(self, purpose: str) -> bool:
        """Form strategy supports automation purposes"""
        supported_purposes = [
            "contact_discovery", "lead_generation", "form_automation",
            "data_access", "registration_automation"
        ]
        return purpose in supported_purposes
