#!/usr/bin/env python3
"""
Strategies Package
Organized extraction strategies by purpose and functionality
"""

# Basic extraction strategies
from .extraction.regex import RegexExtractionStrategy as BasicRegexStrategy
from .extraction.css_selectors.directory_css import DirectoryCSSStrategy
from .extraction.css_selectors.ecommerce_css import EcommerceCSSStrategy
from .extraction.css_selectors.news_css import NewsCSSStrategy
from .extraction.css_selectors.contact_css import ContactCSSStrategy
from .extraction.css_selectors.social_css import SocialMediaCSSStrategy

# Advanced extraction strategies
from .extraction.advanced.regex_patterns import RegexExtractionStrategy
from .extraction.advanced.xpath_extraction import JsonXPathExtractionStrategy
from .extraction.advanced.cosine_similarity import CosineStrategy

# Navigation strategies
from .navigation.pagination import PaginationStrategy
from .navigation.infinite_scroll import InfiniteScrollStrategy

# Authentication strategies
from .authentication.auth_handler import AuthenticationStrategy
from .authentication.captcha_solver import CaptchaStrategy

# Automation strategies
from .automation.form_automation import FormAutoStrategy

# Platform strategies
from .platforms.business_directories.yelp import YelpStrategy
from .platforms.business_directories.yellow_pages import YellowPagesStrategy
from .platforms.business_directories.google_business import GoogleBusinessStrategy
from .platforms.social_networks.linkedin import LinkedInStrategy
from .platforms.social_networks.facebook import FacebookStrategy
from .platforms.ecommerce.amazon import AmazonStrategy

# Hybrid strategies
from .hybrid.json_css_hybrid import JSONCSSHybridStrategy
from .hybrid.smart_hybrid import SmartHybridStrategy
from .hybrid.fallback_chains import FallbackStrategy
from .hybrid.adaptive_learning import AdaptiveHybridStrategy
from .hybrid.multi_strategy import MultiStrategyCoordinator
from .hybrid.adaptive_crawler import AdaptiveCrawlerStrategy
from .hybrid.ai_enhanced import AIEnhancedStrategy

# LLM strategies
from .llm.intelligent_base import IntelligentLLMStrategy
from .llm.context_aware import ContextAwareLLMStrategy
from .llm.adaptive_learning import AdaptiveLLMStrategy
from .llm.multipass_extraction import MultiPassLLMStrategy

__all__ = [
    # Basic extraction strategies
    "BasicRegexStrategy",
    "DirectoryCSSStrategy",
    "EcommerceCSSStrategy", 
    "NewsCSSStrategy",
    "ContactCSSStrategy",
    "SocialMediaCSSStrategy",
    
    # Advanced extraction strategies
    "RegexExtractionStrategy",
    "JsonXPathExtractionStrategy",
    "CosineStrategy",
    
    # Navigation
    "PaginationStrategy", 
    "InfiniteScrollStrategy",
    
    # Authentication
    "AuthenticationStrategy",
    "CaptchaStrategy",
    
    # Automation
    "FormAutoStrategy",
    
    # Platform-specific strategies
    "YelpStrategy",
    "YellowPagesStrategy", 
    "GoogleBusinessStrategy",
    "LinkedInStrategy",
    "FacebookStrategy",
    "AmazonStrategy",
    
    # Hybrid strategies
    "JSONCSSHybridStrategy",
    "SmartHybridStrategy",
    "FallbackStrategy",
    "AdaptiveHybridStrategy",
    "MultiStrategyCoordinator",
    "AdaptiveCrawlerStrategy",
    "AIEnhancedStrategy",
    
    # LLM strategies
    "IntelligentLLMStrategy",
    "ContextAwareLLMStrategy",
    "AdaptiveLLMStrategy",
    "MultiPassLLMStrategy"
]
