#!/usr/bin/env python3
"""
Social Networks Package
Platform-specific strategies for social media platforms
"""

from .linkedin import LinkedInStrategy
from .facebook import FacebookStrategy

__all__ = [
    "LinkedInStrategy",
    "FacebookStrategy"
]
