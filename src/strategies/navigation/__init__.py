#!/usr/bin/env python3
"""
Navigation Strategies Package
Handles pagination, infinite scroll, and dynamic content loading
"""

from .pagination import PaginationStrategy
from .infinite_scroll import InfiniteScrollStrategy

__all__ = [
    "PaginationStrategy",
    "InfiniteScrollStrategy"
]
