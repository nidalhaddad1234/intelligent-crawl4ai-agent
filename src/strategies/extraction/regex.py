#!/usr/bin/env python3
"""
Regex Extraction Strategy
High-performance regex-based extraction for common patterns
"""

import re
import time
import logging
from typing import Dict, Any, List, Optional

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

logger = logging.getLogger("strategies.extraction.regex")


class RegexExtractionStrategy(BaseExtractionStrategy):
    """
    High-performance regex-based extraction for common patterns
    
    Best for: Contact discovery, lead generation, data mining
    Extracts: emails, phones, URLs, social handles, addresses
    """
    
    def __init__(self):
        super().__init__(strategy_type=StrategyType.SPECIALIZED)
        
        # Pre-compiled regex patterns for performance
        self.patterns = {
            'emails': re.compile(
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                re.IGNORECASE
            ),
            'phones_us': re.compile(
                r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
                re.IGNORECASE
            ),
            'urls': re.compile(
                r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*)?(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?',
                re.IGNORECASE
            ),
            'linkedin': re.compile(
                r'linkedin\.com/in/([A-Za-z0-9_-]+)',
                re.IGNORECASE
            ),
            'addresses': re.compile(
                r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln)\b',
                re.IGNORECASE
            ),
            'companies': re.compile(
                r'\b[\w\s&]+(?:inc|llc|corp|corporation|company|co|ltd|limited)\b',
                re.IGNORECASE
            )
        }
    
    async def extract(self, 
                     url: str, 
                     html_content: str,
                     purpose: str,
                     context: Dict[str, Any] = None) -> StrategyResult:
        """Extract data using regex patterns"""
        start_time = time.time()
        
        try:
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text_content = soup.get_text()
            extracted_data = {}
            
            # Apply regex patterns
            for pattern_name, pattern in self.patterns.items():
                matches = pattern.findall(text_content)
                
                if matches:
                    # Clean and deduplicate matches
                    cleaned_matches = list(set([
                        match.strip() if isinstance(match, str) else ''.join(match).strip()
                        for match in matches
                    ]))
                    
                    if cleaned_matches:
                        extracted_data[pattern_name] = cleaned_matches
            
            # Calculate confidence based on patterns found
            confidence = len(extracted_data) / len(self.patterns) if extracted_data else 0.0
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="RegexExtractionStrategy",
                execution_time=execution_time,
                metadata={
                    "total_matches": sum(len(v) for v in extracted_data.values()),
                    "url": url
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"Regex extraction failed: {e}")
            
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="RegexExtractionStrategy",
                execution_time=execution_time,
                metadata={"error": str(e)},
                error=str(e)
            )
    
    def get_confidence_score(self, 
                           url: str, 
                           html_content: str, 
                           purpose: str) -> float:
        """Estimate confidence for regex extraction on this content"""
        
        # Regex works well on text-heavy pages
        text_indicators = [
            'contact', 'about', 'team', 'staff', 'directory',
            '@', 'phone', 'email', 'address', '.com', '.org'
        ]
        
        content_lower = html_content.lower()
        matches = sum(1 for indicator in text_indicators if indicator in content_lower)
        
        # Base confidence based on content indicators
        base_confidence = min(0.9, matches * 0.1)
        
        # Boost for contact/about pages
        if any(page_type in url.lower() for page_type in ['contact', 'about', 'team']):
            base_confidence += 0.2
        
        return min(1.0, base_confidence)
    
    def supports_purpose(self, purpose: str) -> bool:
        """Check if regex strategy supports this purpose"""
        supported_purposes = [
            'contact_discovery', 'lead_generation', 'social_media_analysis',
            'business_listings', 'general'
        ]
        return purpose in supported_purposes