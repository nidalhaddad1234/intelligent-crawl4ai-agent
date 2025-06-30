#!/usr/bin/env python3
"""
Extraction Strategies Package
Pattern-based and CSS-based extraction methods
"""

from .regex import RegexExtractionStrategy
from .css_selectors.directory_css import DirectoryCSSStrategy
from .css_selectors.ecommerce_css import EcommerceCSSStrategy
from .css_selectors.news_css import NewsCSSStrategy
from .css_selectors.contact_css import ContactCSSStrategy
from .css_selectors.social_css import SocialMediaCSSStrategy

__all__ = [
    "RegexExtractionStrategy",
    "DirectoryCSSStrategy",
    "EcommerceCSSStrategy", 
    "NewsCSSStrategy",
    "ContactCSSStrategy",
    "SocialMediaCSSStrategy"
]
