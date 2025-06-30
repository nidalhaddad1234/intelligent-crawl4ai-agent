#!/usr/bin/env python3
"""
Platform Strategies Package
Platform-specific extraction strategies for major websites and services
"""

# Business Directories
from .business_directories.yelp import YelpStrategy
from .business_directories.yellow_pages import YellowPagesStrategy
from .business_directories.google_business import GoogleBusinessStrategy

# Social Networks
from .social_networks.linkedin import LinkedInStrategy
from .social_networks.facebook import FacebookStrategy

# E-commerce
from .ecommerce.amazon import AmazonStrategy

__all__ = [
    # Business Directories
    "YelpStrategy",
    "YellowPagesStrategy", 
    "GoogleBusinessStrategy",
    
    # Social Networks
    "LinkedInStrategy",
    "FacebookStrategy",
    
    # E-commerce
    "AmazonStrategy"
]
