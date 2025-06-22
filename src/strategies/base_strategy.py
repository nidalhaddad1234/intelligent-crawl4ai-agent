#!/usr/bin/env python3
"""
Base Extraction Strategy
Defines the interface and common functionality for all extraction strategies
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import ExtractionStrategy

logger = logging.getLogger("base_strategy")

class StrategyType(Enum):
    CSS = "css"
    LLM = "llm"
    HYBRID = "hybrid"
    PLATFORM_SPECIFIC = "platform_specific"
    SPECIALIZED = "specialized"

class ConfidenceLevel(Enum):
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.8
    VERY_HIGH = 0.95

@dataclass
class StrategyResult:
    """Result from strategy execution"""
    success: bool
    extracted_data: Dict[str, Any]
    confidence_score: float
    strategy_used: str
    execution_time: float
    metadata: Dict[str, Any]
    error: Optional[str] = None
    fallback_used: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ExtractionField:
    """Defines a field to extract"""
    name: str
    selector: str
    data_type: str = "text"  # text, number, url, email, phone, date
    required: bool = True
    multiple: bool = False
    validator: Optional[str] = None
    transformer: Optional[str] = None

class BaseExtractionStrategy(ABC):
    """
    Base class for all extraction strategies
    Provides common functionality and interface
    """
    
    def __init__(self, 
                 strategy_type: StrategyType = StrategyType.CSS,
                 confidence_threshold: float = 0.7,
                 max_retries: int = 3,
                 timeout: int = 30000):
        self.strategy_type = strategy_type
        self.confidence_threshold = confidence_threshold
        self.max_retries = max_retries
        self.timeout = timeout
        self.logger = logging.getLogger(f"strategy.{self.__class__.__name__}")
        
    @abstractmethod
    async def extract(self, 
                     url: str, 
                     html_content: str,
                     purpose: str,
                     context: Dict[str, Any] = None) -> StrategyResult:
        """
        Extract data from the given URL/content
        
        Args:
            url: Target URL
            html_content: HTML content to extract from
            purpose: Extraction purpose (company_info, contact_discovery, etc.)
            context: Additional context for extraction
            
        Returns:
            StrategyResult with extracted data and metadata
        """
        pass
    
    @abstractmethod
    def get_confidence_score(self, 
                           url: str, 
                           html_content: str, 
                           purpose: str) -> float:
        """
        Estimate confidence score for this strategy on given content
        
        Returns:
            Float between 0.0 and 1.0 indicating strategy fitness
        """
        pass
    
    @abstractmethod
    def supports_purpose(self, purpose: str) -> bool:
        """
        Check if this strategy supports the given extraction purpose
        
        Returns:
            Boolean indicating support
        """
        pass
    
    def get_browser_config(self) -> Dict[str, Any]:
        """Get browser configuration for this strategy"""
        return {
            "headless": True,
            "page_timeout": self.timeout,
            "wait_for": "networkidle",
            "js_code": self.get_page_js(),
            "extra_args": ["--no-sandbox", "--disable-dev-shm-usage"]
        }
    
    def get_page_js(self) -> str:
        """Get JavaScript code to run on the page before extraction"""
        return """
        // Basic page preparation
        window.scrollTo(0, 0);
        
        // Remove annoying overlays
        const overlays = document.querySelectorAll(
            '.modal, .overlay, .popup, .cookie-banner, [class*="cookie"], [id*="cookie"]'
        );
        overlays.forEach(el => el.style.display = 'none');
        
        // Mark extraction timestamp
        window.extractionTimestamp = Date.now();
        """
    
    def validate_extracted_data(self, 
                               data: Dict[str, Any], 
                               fields: List[ExtractionField]) -> Dict[str, Any]:
        """
        Validate and clean extracted data based on field definitions
        
        Args:
            data: Raw extracted data
            fields: List of field definitions for validation
            
        Returns:
            Cleaned and validated data
        """
        validated = {}
        
        for field in fields:
            value = data.get(field.name)
            
            # Check if required field is missing
            if field.required and not value:
                self.logger.warning(f"Required field '{field.name}' is missing")
                continue
            
            if value is None:
                continue
                
            # Type conversion and validation
            try:
                validated_value = self._validate_field_value(value, field)
                if validated_value is not None:
                    validated[field.name] = validated_value
            except Exception as e:
                self.logger.warning(f"Field validation failed for '{field.name}': {e}")
                
        return validated
    
    def _validate_field_value(self, value: Any, field: ExtractionField) -> Any:
        """Validate individual field value"""
        import re
        
        if field.data_type == "text":
            return str(value).strip() if value else None
            
        elif field.data_type == "number":
            try:
                return float(value) if value else None
            except (ValueError, TypeError):
                return None
                
        elif field.data_type == "email":
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if isinstance(value, str) and re.match(email_pattern, value):
                return value.lower().strip()
            return None
            
        elif field.data_type == "phone":
            # Clean and validate phone numbers
            if isinstance(value, str):
                cleaned = re.sub(r'[^\d+\-\(\)\s]', '', value)
                if re.search(r'\d{3,}', cleaned):  # At least 3 digits
                    return cleaned.strip()
            return None
            
        elif field.data_type == "url":
            if isinstance(value, str) and value.startswith(('http://', 'https://')):
                return value.strip()
            return None
            
        else:
            return value
    
    def calculate_confidence(self, 
                           extracted_data: Dict[str, Any],
                           expected_fields: List[str]) -> float:
        """
        Calculate confidence score based on extracted data completeness
        
        Args:
            extracted_data: The extracted data
            expected_fields: List of expected field names
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not expected_fields:
            return 0.5
            
        found_fields = 0
        quality_score = 0.0
        
        for field in expected_fields:
            value = extracted_data.get(field)
            if value:
                found_fields += 1
                
                # Score based on data quality
                if isinstance(value, str):
                    if len(value.strip()) > 2:
                        quality_score += 1.0
                    else:
                        quality_score += 0.3
                elif isinstance(value, (list, dict)) and value:
                    quality_score += 1.0
                else:
                    quality_score += 0.5
        
        # Combine completeness and quality
        completeness = found_fields / len(expected_fields)
        avg_quality = quality_score / len(expected_fields) if expected_fields else 0
        
        return (completeness * 0.7 + avg_quality * 0.3)
    
    def extract_structured_data(self, html_content: str) -> Dict[str, Any]:
        """
        Extract structured data (JSON-LD, microdata) from HTML
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Dictionary with structured data
        """
        from bs4 import BeautifulSoup
        import json
        
        structured_data = {}
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract JSON-LD
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict):
                        structured_data.update(data)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                structured_data.update(item)
                except json.JSONDecodeError:
                    continue
            
            # Extract microdata
            microdata_items = soup.find_all(attrs={"itemtype": True})
            for item in microdata_items:
                item_type = item.get('itemtype', '')
                props = {}
                
                prop_elements = item.find_all(attrs={"itemprop": True})
                for prop_el in prop_elements:
                    prop_name = prop_el.get('itemprop')
                    prop_value = prop_el.get('content') or prop_el.get_text(strip=True)
                    if prop_name and prop_value:
                        props[prop_name] = prop_value
                
                if props:
                    structured_data[f"microdata_{item_type}"] = props
            
        except Exception as e:
            self.logger.warning(f"Failed to extract structured data: {e}")
        
        return structured_data
    
    def detect_anti_bot_measures(self, html_content: str) -> List[str]:
        """
        Detect anti-bot measures on the page
        
        Returns:
            List of detected anti-bot measures
        """
        measures = []
        content_lower = html_content.lower()
        
        # Common anti-bot patterns
        if 'cloudflare' in content_lower:
            measures.append('cloudflare')
        if 'recaptcha' in content_lower or 'g-recaptcha' in content_lower:
            measures.append('recaptcha')
        if 'access denied' in content_lower:
            measures.append('access_denied')
        if 'rate limit' in content_lower:
            measures.append('rate_limiting')
        if 'bot' in content_lower and 'block' in content_lower:
            measures.append('bot_blocking')
        
        return measures
    
    async def handle_dynamic_content(self, 
                                   crawler: AsyncWebCrawler,
                                   url: str) -> str:
        """
        Handle dynamic content loading (AJAX, lazy loading, etc.)
        
        Returns:
            Updated HTML content after dynamic loading
        """
        dynamic_js = """
        // Scroll to trigger lazy loading
        const scrollStep = 100;
        let currentPosition = 0;
        const maxScroll = document.body.scrollHeight;
        
        function scrollGradually() {
            return new Promise((resolve) => {
                const interval = setInterval(() => {
                    currentPosition += scrollStep;
                    window.scrollTo(0, currentPosition);
                    
                    if (currentPosition >= maxScroll) {
                        clearInterval(interval);
                        // Wait for final content to load
                        setTimeout(resolve, 2000);
                    }
                }, 100);
            });
        }
        
        await scrollGradually();
        
        // Click "Load More" buttons if present
        const loadMoreButtons = document.querySelectorAll(
            '[data-testid="load-more"], .load-more, [class*="load-more"], ' +
            '[class*="show-more"], .show-more, button[aria-label*="more"]'
        );
        
        for (const button of loadMoreButtons) {
            if (button.offsetParent !== null) { // visible
                button.click();
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }
        """
        
        try:
            config = CrawlerRunConfig(
                js_code=dynamic_js,
                wait_for="networkidle",
                timeout=self.timeout
            )
            
            result = await crawler.arun(url=url, config=config)
            return result.html
            
        except Exception as e:
            self.logger.warning(f"Dynamic content handling failed: {e}")
            return ""
    
    def create_extraction_summary(self, 
                                result: StrategyResult,
                                url: str) -> Dict[str, Any]:
        """Create a summary of the extraction for logging/monitoring"""
        return {
            "url": url,
            "strategy": self.__class__.__name__,
            "success": result.success,
            "confidence": result.confidence_score,
            "fields_extracted": len(result.extracted_data) if result.extracted_data else 0,
            "execution_time": result.execution_time,
            "fallback_used": result.fallback_used,
            "error": result.error
        }
