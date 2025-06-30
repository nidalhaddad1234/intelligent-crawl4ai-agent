#!/usr/bin/env python3
"""
CAPTCHA Solving Strategy
Handle CAPTCHA detection and solving

Examples:
- Detect reCAPTCHA and hCaptcha challenges
- Integrate with CAPTCHA solving services
- Handle image-based CAPTCHAs
- Manage CAPTCHA retry logic
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.authentication.captcha")


class CaptchaStrategy(BaseExtractionStrategy):
    """
    Handle CAPTCHA detection and solving
    
    Examples:
    - Detect reCAPTCHA and hCaptcha challenges
    - Integrate with CAPTCHA solving services
    - Handle image-based CAPTCHAs
    - Manage CAPTCHA retry logic
    """
    
    def __init__(self, captcha_service_key: str = None, **kwargs):
        super().__init__(strategy_type=StrategyType.SPECIALIZED, **kwargs)
        self.captcha_service_key = captcha_service_key
        
        # CAPTCHA detection patterns
        self.captcha_indicators = {
            "recaptcha": [
                ".g-recaptcha", "[data-sitekey]", 
                "iframe[src*='recaptcha']", "#recaptcha"
            ],
            "hcaptcha": [
                ".h-captcha", "[data-sitekey*='hcaptcha']",
                "iframe[src*='hcaptcha']"
            ],
            "image_captcha": [
                ".captcha-image", "[src*='captcha']",
                ".verification-image", "[alt*='captcha']"
            ],
            "text_captcha": [
                "[name*='captcha']", ".captcha-input",
                "[placeholder*='captcha']"
            ]
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Detect CAPTCHA types
            captcha_info = self._detect_captcha_types(soup, html_content)
            
            # Create solving plan
            solving_plan = self._create_captcha_solving_plan(captcha_info, context)
            
            extracted_data = {
                "captcha_detected": captcha_info.get("has_captcha", False),
                "captcha_types": captcha_info.get("types", []),
                "solving_plan": solving_plan,
                "service_required": captcha_info.get("has_captcha", False)
            }
            
            confidence = 0.9 if captcha_info.get("has_captcha") else 0.1
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=True,  # Always successful at detection
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="CaptchaStrategy",
                execution_time=execution_time,
                metadata={
                    "captcha_present": captcha_info.get("has_captcha", False),
                    "complexity": captcha_info.get("complexity", "none")
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="CaptchaStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _detect_captcha_types(self, soup: BeautifulSoup, html_content: str) -> Dict[str, Any]:
        """Detect CAPTCHA types and characteristics"""
        
        captcha_info = {
            "has_captcha": False,
            "types": [],
            "complexity": "none",
            "site_keys": {},
            "elements": {}
        }
        
        # Check each CAPTCHA type
        for captcha_type, selectors in self.captcha_indicators.items():
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    captcha_info["has_captcha"] = True
                    captcha_info["types"].append(captcha_type)
                    captcha_info["elements"][captcha_type] = selector
                    
                    # Extract site keys for reCAPTCHA/hCaptcha
                    if captcha_type in ["recaptcha", "hcaptcha"]:
                        site_key = self._extract_site_key(elements[0], captcha_type)
                        if site_key:
                            captcha_info["site_keys"][captcha_type] = site_key
                    
                    break
        
        # Determine complexity
        if "recaptcha" in captcha_info["types"]:
            captcha_info["complexity"] = "recaptcha_v2_or_v3"
        elif "hcaptcha" in captcha_info["types"]:
            captcha_info["complexity"] = "hcaptcha"
        elif "image_captcha" in captcha_info["types"]:
            captcha_info["complexity"] = "image_recognition"
        elif "text_captcha" in captcha_info["types"]:
            captcha_info["complexity"] = "text_input"
        
        return captcha_info
    
    def _extract_site_key(self, element, captcha_type: str) -> Optional[str]:
        """Extract site key from CAPTCHA element"""
        
        # Check data-sitekey attribute
        site_key = element.get('data-sitekey')
        if site_key:
            return site_key
        
        # Check parent elements
        parent = element.find_parent()
        if parent:
            site_key = parent.get('data-sitekey')
            if site_key:
                return site_key
        
        # Check iframe src for embedded CAPTCHAs
        if element.name == 'iframe':
            src = element.get('src', '')
            if 'sitekey=' in src:
                match = re.search(r'sitekey=([^&]+)', src)
                if match:
                    return match.group(1)
        
        return None
    
    def _create_captcha_solving_plan(self, captcha_info: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create CAPTCHA solving plan"""
        
        plan = {
            "solving_method": "none",
            "steps": [],
            "estimated_time": 0,
            "service_config": {}
        }
        
        if not captcha_info.get("has_captcha"):
            return plan
        
        captcha_types = captcha_info.get("types", [])
        
        if "recaptcha" in captcha_types:
            plan["solving_method"] = "2captcha_recaptcha"
            plan["estimated_time"] = 30  # seconds
            plan["steps"] = [
                {
                    "action": "submit_to_service",
                    "service": "2captcha",
                    "captcha_type": "recaptcha_v2",
                    "site_key": captcha_info.get("site_keys", {}).get("recaptcha"),
                    "page_url": context.get("url") if context else None
                },
                {
                    "action": "wait_for_solution",
                    "timeout": 120  # 2 minutes max
                },
                {
                    "action": "submit_solution",
                    "selector": "[name='g-recaptcha-response']"
                }
            ]
        
        elif "hcaptcha" in captcha_types:
            plan["solving_method"] = "2captcha_hcaptcha"
            plan["estimated_time"] = 30
            plan["steps"] = [
                {
                    "action": "submit_to_service",
                    "service": "2captcha",
                    "captcha_type": "hcaptcha",
                    "site_key": captcha_info.get("site_keys", {}).get("hcaptcha"),
                    "page_url": context.get("url") if context else None
                },
                {
                    "action": "wait_for_solution",
                    "timeout": 120
                },
                {
                    "action": "submit_solution",
                    "selector": "[name='h-captcha-response']"
                }
            ]
        
        elif "image_captcha" in captcha_types:
            plan["solving_method"] = "image_recognition"
            plan["estimated_time"] = 20
            plan["steps"] = [
                {
                    "action": "capture_image",
                    "selector": captcha_info.get("elements", {}).get("image_captcha")
                },
                {
                    "action": "solve_image",
                    "service": "2captcha_image"
                },
                {
                    "action": "input_solution",
                    "selector": "[name*='captcha'], .captcha-input"
                }
            ]
        
        elif "text_captcha" in captcha_types:
            plan["solving_method"] = "text_recognition"
            plan["estimated_time"] = 10
            plan["steps"] = [
                {
                    "action": "extract_question",
                    "selector": ".captcha-question, .captcha-text"
                },
                {
                    "action": "solve_text",
                    "method": "simple_math_or_lookup"
                },
                {
                    "action": "input_solution",
                    "selector": "[name*='captcha'], .captcha-input"
                }
            ]
        
        # Add service configuration
        if self.captcha_service_key:
            plan["service_config"] = {
                "api_key": self.captcha_service_key,
                "service_url": "http://2captcha.com/in.php",
                "result_url": "http://2captcha.com/res.php"
            }
        else:
            plan["service_config"] = {
                "note": "CAPTCHA service API key required for automated solving"
            }
        
        return plan
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """CAPTCHA strategy confidence"""
        
        # Check for CAPTCHA indicators
        captcha_terms = [
            "captcha", "recaptcha", "hcaptcha", "verification",
            "prove you're human", "security check"
        ]
        
        content_lower = html_content.lower()
        indicator_count = sum(1 for term in captcha_terms if term in content_lower)
        
        confidence = min(indicator_count * 0.3, 0.9)
        
        # Check for actual CAPTCHA elements
        soup = BeautifulSoup(html_content, 'html.parser')
        if soup.select(".g-recaptcha, .h-captcha"):
            confidence = 0.95
        
        return confidence
    
    def supports_purpose(self, purpose: str) -> bool:
        """CAPTCHA strategy supports access purposes"""
        supported_purposes = [
            "form_automation", "data_access", "protected_content",
            "anti_bot_circumvention", "verification_handling"
        ]
        return purpose in supported_purposes
