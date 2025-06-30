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
        """Extract data from the given URL/content"""
        pass
    
    @abstractmethod
    def get_confidence_score(self, 
                           url: str, 
                           html_content: str, 
                           purpose: str) -> float:
        """Estimate confidence score for this strategy on given content"""
        pass
    
    @abstractmethod
    def supports_purpose(self, purpose: str) -> bool:
        """Check if this strategy supports the given extraction purpose"""
        pass
    
    def calculate_confidence(self, 
                           extracted_data: Dict[str, Any],
                           expected_fields: List[str]) -> float:
        """Calculate confidence score based on extracted data completeness"""
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