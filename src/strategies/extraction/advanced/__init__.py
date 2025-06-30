#!/usr/bin/env python3
"""
Advanced Extraction Strategies Package
Specialized algorithms for complex data extraction patterns
"""

from .regex_patterns import RegexExtractionStrategy
from .xpath_extraction import JsonXPathExtractionStrategy
from .cosine_similarity import CosineStrategy

__all__ = [
    "RegexExtractionStrategy",
    "JsonXPathExtractionStrategy", 
    "CosineStrategy"
]
