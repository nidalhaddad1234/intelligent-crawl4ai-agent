#!/usr/bin/env python3
"""
Hybrid Extraction Strategies Package
Combines multiple extraction approaches for optimal results
"""

from .json_css_hybrid import JSONCSSHybridStrategy
from .smart_hybrid import SmartHybridStrategy
from .fallback_chains import FallbackStrategy
from .adaptive_learning import AdaptiveHybridStrategy
from .multi_strategy import MultiStrategyCoordinator, CoordinationMode, StrategyWeight, CoordinationConfig
from .adaptive_crawler import AdaptiveCrawlerStrategy, WebsitePattern, AdaptationConfig
from .ai_enhanced import AIEnhancedStrategy, AIEnhancementConfig, AIExtractionPlan

__all__ = [
    # Original hybrid strategies
    "JSONCSSHybridStrategy",
    "SmartHybridStrategy", 
    "FallbackStrategy",
    "AdaptiveHybridStrategy",
    
    # New Task 5.1 hybrid strategies
    "MultiStrategyCoordinator",
    "AdaptiveCrawlerStrategy", 
    "AIEnhancedStrategy",
    
    # Configuration classes
    "CoordinationMode",
    "StrategyWeight",
    "CoordinationConfig",
    "WebsitePattern",
    "AdaptationConfig",
    "AIEnhancementConfig",
    "AIExtractionPlan"
]
