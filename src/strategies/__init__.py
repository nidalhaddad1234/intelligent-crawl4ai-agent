#!/usr/bin/env python3
"""
Extraction Strategies Module
Provides intelligent, adaptive extraction strategies for different website types
"""

from .base_strategy import BaseExtractionStrategy, StrategyResult
from .css_strategies import (
    DirectoryCSSStrategy,
    EcommerceCSSStrategy,
    NewsCSSStrategy,
    ContactCSSStrategy,
    SocialMediaCSSStrategy
)
from .llm_strategies import (
    IntelligentLLMStrategy,
    ContextAwareLLMStrategy,
    AdaptiveLLMStrategy,
    MultiPassLLMStrategy
)
from .hybrid_strategies import (
    JSONCSSHybridStrategy,
    SmartHybridStrategy,
    FallbackStrategy,
    AdaptiveHybridStrategy
)
from .platform_strategies import (
    YelpStrategy,
    LinkedInStrategy,
    AmazonStrategy,
    YellowPagesStrategy,
    GoogleBusinessStrategy,
    FacebookStrategy
)
from .specialized_strategies import (
    RegexExtractionStrategy,
    FormAutoStrategy,
    PaginationStrategy,
    InfiniteScrollStrategy,
    AuthenticationStrategy,
    CaptchaStrategy
)

__all__ = [
    # Base classes
    'BaseExtractionStrategy',
    'StrategyResult',
    
    # CSS Strategies
    'DirectoryCSSStrategy',
    'EcommerceCSSStrategy', 
    'NewsCSSStrategy',
    'ContactCSSStrategy',
    'SocialMediaCSSStrategy',
    
    # LLM Strategies
    'IntelligentLLMStrategy',
    'ContextAwareLLMStrategy',
    'AdaptiveLLMStrategy',
    'MultiPassLLMStrategy',
    
    # Hybrid Strategies
    'JSONCSSHybridStrategy',
    'SmartHybridStrategy',
    'FallbackStrategy',
    'AdaptiveHybridStrategy',
    
    # Platform-Specific Strategies
    'YelpStrategy',
    'LinkedInStrategy',
    'AmazonStrategy',
    'YellowPagesStrategy',
    'GoogleBusinessStrategy',
    'FacebookStrategy',
    
    # Specialized Strategies
    'RegexExtractionStrategy',
    'FormAutoStrategy',
    'PaginationStrategy',
    'InfiniteScrollStrategy',
    'AuthenticationStrategy',
    'CaptchaStrategy'
]

# Strategy registry for dynamic selection
STRATEGY_REGISTRY = {
    # CSS Strategies
    'directory_css': DirectoryCSSStrategy,
    'ecommerce_css': EcommerceCSSStrategy,
    'news_css': NewsCSSStrategy,
    'contact_css': ContactCSSStrategy,
    'social_css': SocialMediaCSSStrategy,
    
    # LLM Strategies
    'intelligent_llm': IntelligentLLMStrategy,
    'context_llm': ContextAwareLLMStrategy,
    'adaptive_llm': AdaptiveLLMStrategy,
    'multipass_llm': MultiPassLLMStrategy,
    
    # Hybrid Strategies
    'json_css_hybrid': JSONCSSHybridStrategy,
    'smart_hybrid': SmartHybridStrategy,
    'fallback': FallbackStrategy,
    'adaptive_hybrid': AdaptiveHybridStrategy,
    
    # Platform Strategies
    'yelp': YelpStrategy,
    'linkedin': LinkedInStrategy,
    'amazon': AmazonStrategy,
    'yellowpages': YellowPagesStrategy,
    'google_business': GoogleBusinessStrategy,
    'facebook': FacebookStrategy,
    
    # Specialized Strategies
    'regex': RegexExtractionStrategy,
    'form_auto': FormAutoStrategy,
    'pagination': PaginationStrategy,
    'infinite_scroll': InfiniteScrollStrategy,
    'authentication': AuthenticationStrategy,
    'captcha': CaptchaStrategy
}

def get_strategy(strategy_name: str, **kwargs):
    """Get strategy instance by name"""
    if strategy_name in STRATEGY_REGISTRY:
        return STRATEGY_REGISTRY[strategy_name](**kwargs)
    else:
        raise ValueError(f"Unknown strategy: {strategy_name}. Available strategies: {list(STRATEGY_REGISTRY.keys())}")

def list_strategies():
    """List all available strategies"""
    return list(STRATEGY_REGISTRY.keys())

def get_strategies_by_type(strategy_type: str):
    """Get strategies filtered by type"""
    type_mapping = {
        'css': ['directory_css', 'ecommerce_css', 'news_css', 'contact_css', 'social_css'],
        'llm': ['intelligent_llm', 'context_llm', 'adaptive_llm', 'multipass_llm'],
        'hybrid': ['json_css_hybrid', 'smart_hybrid', 'fallback', 'adaptive_hybrid'],
        'platform': ['yelp', 'linkedin', 'amazon', 'yellowpages', 'google_business', 'facebook'],
        'specialized': ['regex', 'form_auto', 'pagination', 'infinite_scroll', 'authentication', 'captcha']
    }
    return type_mapping.get(strategy_type, [])

def get_recommended_strategies(purpose: str, website_type: str = None):
    """Get recommended strategies for a given purpose and website type"""
    
    recommendations = {
        'company_info': {
            'directory_listing': ['directory_css', 'contact_css'],
            'corporate': ['intelligent_llm', 'contact_css'],
            'e_commerce': ['ecommerce_css', 'intelligent_llm'],
            'default': ['smart_hybrid', 'intelligent_llm']
        },
        'contact_discovery': {
            'any': ['regex', 'contact_css', 'intelligent_llm', 'form_auto'],
            'default': ['regex', 'contact_css', 'intelligent_llm']
        },
        'product_data': {
            'e_commerce': ['ecommerce_css', 'json_css_hybrid'],
            'amazon': ['amazon'],
            'default': ['ecommerce_css', 'json_css_hybrid']
        },
        'profile_info': {
            'linkedin': ['linkedin', 'authentication'],
            'social_media': ['social_css', 'intelligent_llm'],
            'default': ['social_css', 'intelligent_llm']
        },
        'news_content': {
            'news': ['news_css', 'json_css_hybrid'],
            'default': ['news_css', 'intelligent_llm']
        },
        'business_listings': {
            'yelp': ['yelp', 'regex', 'pagination'],
            'yellowpages': ['yellowpages', 'regex', 'pagination'],
            'directory_listing': ['directory_css', 'regex', 'pagination'],
            'default': ['directory_css', 'regex', 'pagination']
        }
    }
    
    purpose_strategies = recommendations.get(purpose, {})
    
    if website_type and website_type in purpose_strategies:
        return purpose_strategies[website_type]
    elif 'any' in purpose_strategies:
        return purpose_strategies['any']
    else:
        return purpose_strategies.get('default', ['smart_hybrid', 'intelligent_llm'])
