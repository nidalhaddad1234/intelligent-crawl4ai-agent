#!/usr/bin/env python3
"""
CSS Selectors Package
CSS-based extraction strategies for specific website types
"""

from .directory_css import DirectoryCSSStrategy
from .ecommerce_css import EcommerceCSSStrategy
from .news_css import NewsCSSStrategy
from .contact_css import ContactCSSStrategy
from .social_css import SocialMediaCSSStrategy

__all__ = [
    "DirectoryCSSStrategy",
    "EcommerceCSSStrategy",
    "NewsCSSStrategy",
    "ContactCSSStrategy",
    "SocialMediaCSSStrategy"
]
