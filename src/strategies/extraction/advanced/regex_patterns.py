#!/usr/bin/env python3
"""
Regex Pattern Extraction Strategy
Fast pattern-based extraction using pre-compiled regular expressions
"""

import re
import time
from typing import Dict, Any, List, Optional, Union
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

class RegexExtractionStrategy(BaseExtractionStrategy):
    """
    Fast pattern-based extraction using pre-compiled regular expressions
    Matches Crawl4AI's RegexExtractionStrategy functionality
    """
    
    # Built-in pattern catalog (matches Crawl4AI patterns)
    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        'url': r'https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?',
        'date': r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
        'time': r'\b\d{1,2}:\d{2}(?::\d{2})?(?:\s?[AaPp][Mm])?\b',
        'currency': r'\$\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s?(?:USD|EUR|GBP|JPY|CAD|AUD)',
        'social_security': r'\b\d{3}-\d{2}-\d{4}\b',
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'zip_code': r'\b\d{5}(?:-\d{4})?\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'
    }
    
    def __init__(self, patterns: Union[str, List[str], Dict[str, str]] = None, **kwargs):
        super().__init__(strategy_type=StrategyType.CSS, **kwargs)
        
        self.custom_patterns = {}
        self.compiled_patterns = {}
        
        if patterns:
            if isinstance(patterns, str):
                # Single built-in pattern
                if patterns in self.PATTERNS:
                    self.custom_patterns[patterns] = self.PATTERNS[patterns]
            elif isinstance(patterns, list):
                # Multiple built-in patterns
                for pattern in patterns:
                    if pattern in self.PATTERNS:
                        self.custom_patterns[pattern] = self.PATTERNS[pattern]
            elif isinstance(patterns, dict):
                # Custom pattern dictionary
                self.custom_patterns.update(patterns)
        else:
            # Default to common patterns
            self.custom_patterns = {
                'email': self.PATTERNS['email'],
                'phone': self.PATTERNS['phone'],
                'url': self.PATTERNS['url']
            }
        
        # Compile patterns for performance
        for name, pattern in self.custom_patterns.items():
            try:
                self.compiled_patterns[name] = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                self.logger.warning(f"Failed to compile pattern '{name}': {e}")
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Extract text content from HTML
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            
            # Extract data using compiled patterns
            extracted_data = {}
            
            for pattern_name, compiled_pattern in self.compiled_patterns.items():
                matches = compiled_pattern.findall(text_content)
                if matches:
                    # Remove duplicates while preserving order
                    unique_matches = list(dict.fromkeys(matches))
                    extracted_data[pattern_name] = unique_matches
            
            # Calculate confidence based on number of matches
            total_matches = sum(len(matches) for matches in extracted_data.values())
            confidence = min(0.3 + (total_matches * 0.1), 1.0)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="RegexExtractionStrategy",
                execution_time=execution_time,
                metadata={
                    "patterns_used": list(self.compiled_patterns.keys()),
                    "total_matches": total_matches,
                    "text_length": len(text_content)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="RegexExtractionStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def add_pattern(self, name: str, pattern: str):
        """Add a new regex pattern"""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            self.custom_patterns[name] = pattern
            self.compiled_patterns[name] = compiled_pattern
        except re.error as e:
            self.logger.error(f"Failed to add pattern '{name}': {e}")
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}")
    
    def remove_pattern(self, name: str):
        """Remove a regex pattern"""
        if name in self.custom_patterns:
            del self.custom_patterns[name]
        if name in self.compiled_patterns:
            del self.compiled_patterns[name]
    
    def get_patterns(self) -> Dict[str, str]:
        """Get all current patterns"""
        return self.custom_patterns.copy()
    
    def get_available_patterns(self) -> List[str]:
        """Get list of available built-in patterns"""
        return list(self.PATTERNS.keys())
    
    def validate_pattern(self, pattern: str) -> bool:
        """Validate a regex pattern"""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False
    
    def test_pattern(self, pattern: str, test_text: str) -> List[str]:
        """Test a pattern against sample text"""
        try:
            compiled_pattern = re.compile(pattern, re.IGNORECASE)
            return compiled_pattern.findall(test_text)
        except re.error as e:
            self.logger.error(f"Pattern test failed: {e}")
            return []
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Regex strategy works well for pattern-based data extraction"""
        if purpose in ["contact_discovery", "data_validation", "pattern_extraction"]:
            return 0.8
        return 0.4  # Lower for complex semantic tasks
    
    def supports_purpose(self, purpose: str) -> bool:
        """Regex strategy supports pattern-based extraction purposes"""
        supported_purposes = [
            "contact_discovery", "data_validation", "pattern_extraction",
            "email_extraction", "phone_extraction", "url_extraction"
        ]
        return purpose in supported_purposes
