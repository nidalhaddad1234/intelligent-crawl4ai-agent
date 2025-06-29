"""
URL Filtering System for Deep Crawling
Provides intelligent filtering capabilities for discovered URLs
"""

import re
from abc import ABC, abstractmethod
from typing import List, Set, Dict, Any
from urllib.parse import urlparse
import logging

logger = logging.getLogger("deep_crawling.filters")

class URLFilter(ABC):
    """Abstract base class for URL filters"""
    
    @abstractmethod
    def should_crawl(self, url: str, context: Dict[str, Any] = None) -> bool:
        """
        Determine if a URL should be crawled
        
        Args:
            url: The URL to evaluate
            context: Additional context (depth, parent_url, etc.)
            
        Returns:
            True if URL should be crawled, False otherwise
        """
        pass
    
    @abstractmethod
    def get_filter_name(self) -> str:
        """Get a human-readable name for this filter"""
        pass

class URLPatternFilter(URLFilter):
    """
    Filter URLs based on inclusion/exclusion patterns
    
    Examples:
        # Include only contact and about pages
        filter = URLPatternFilter(include=["*/contact*", "*/about*"])
        
        # Exclude admin and API endpoints  
        filter = URLPatternFilter(exclude=["*/admin/*", "*/api/*"])
    """
    
    def __init__(self, include: List[str] = None, exclude: List[str] = None):
        self.include_patterns = include or []
        self.exclude_patterns = exclude or []
        
        # Convert glob patterns to regex
        self.include_regex = [self._glob_to_regex(pattern) for pattern in self.include_patterns]
        self.exclude_regex = [self._glob_to_regex(pattern) for pattern in self.exclude_patterns]
    
    def _glob_to_regex(self, pattern: str) -> re.Pattern:
        """Convert glob pattern to compiled regex"""
        # Escape special regex characters except * and ?
        escaped = re.escape(pattern)
        # Convert glob wildcards to regex
        regex_pattern = escaped.replace(r'\*', '.*').replace(r'\?', '.')
        return re.compile(regex_pattern, re.IGNORECASE)
    
    def should_crawl(self, url: str, context: Dict[str, Any] = None) -> bool:
        # Check exclusion patterns first
        if self.exclude_regex:
            for pattern in self.exclude_regex:
                if pattern.search(url):
                    return False
        
        # If no include patterns, allow by default (only exclusions apply)
        if not self.include_regex:
            return True
        
        # Check inclusion patterns
        for pattern in self.include_regex:
            if pattern.search(url):
                return True
        
        return False
    
    def get_filter_name(self) -> str:
        return f"URLPatternFilter(include={self.include_patterns}, exclude={self.exclude_patterns})"

class DomainFilter(URLFilter):
    """
    Filter URLs based on allowed/blocked domains
    
    Examples:
        # Only crawl company.com and subdomains
        filter = DomainFilter(allowed_domains=["company.com"])
        
        # Block social media and ad domains
        filter = DomainFilter(blocked_domains=["facebook.com", "twitter.com", "ads.google.com"])
    """
    
    def __init__(self, allowed_domains: List[str] = None, blocked_domains: List[str] = None):
        self.allowed_domains = [domain.lower() for domain in (allowed_domains or [])]
        self.blocked_domains = [domain.lower() for domain in (blocked_domains or [])]
    
    def should_crawl(self, url: str, context: Dict[str, Any] = None) -> bool:
        try:
            domain = urlparse(url).netloc.lower()
            
            # Check blocked domains first
            if self.blocked_domains:
                for blocked_domain in self.blocked_domains:
                    if blocked_domain in domain or domain.endswith('.' + blocked_domain):
                        return False
            
            # If no allowed domains specified, allow by default (only blocks apply)
            if not self.allowed_domains:
                return True
            
            # Check allowed domains
            for allowed_domain in self.allowed_domains:
                if allowed_domain in domain or domain.endswith('.' + allowed_domain):
                    return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Failed to parse domain from URL {url}: {e}")
            return False
    
    def get_filter_name(self) -> str:
        return f"DomainFilter(allowed={self.allowed_domains}, blocked={self.blocked_domains})"

class ContentTypeFilter(URLFilter):
    """
    Filter URLs based on expected content types
    
    Examples:
        # Only crawl HTML pages
        filter = ContentTypeFilter(allowed_types=["text/html"])
        
        # Exclude images and videos
        filter = ContentTypeFilter(blocked_extensions=[".jpg", ".png", ".mp4", ".avi"])
    """
    
    def __init__(self, allowed_types: List[str] = None, blocked_extensions: List[str] = None):
        self.allowed_types = [t.lower() for t in (allowed_types or [])]
        self.blocked_extensions = [ext.lower() for ext in (blocked_extensions or [])]
        
        # Default blocked extensions for non-HTML content
        if not self.blocked_extensions:
            self.blocked_extensions = [
                '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico',
                '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm',
                '.mp3', '.wav', '.ogg', '.flac',
                '.zip', '.rar', '.tar', '.gz', '.7z',
                '.exe', '.msi', '.dmg', '.deb', '.rpm'
            ]
    
    def should_crawl(self, url: str, context: Dict[str, Any] = None) -> bool:
        try:
            parsed_url = urlparse(url)
            path = parsed_url.path.lower()
            
            # Check for blocked file extensions
            if self.blocked_extensions:
                for ext in self.blocked_extensions:
                    if path.endswith(ext):
                        return False
            
            # If allowed types specified, this would require an HTTP HEAD request
            # For now, we'll assume HTML if no extension is present
            if self.allowed_types:
                # Simple heuristic: if no extension, assume HTML
                if '.' not in path.split('/')[-1]:
                    return 'text/html' in self.allowed_types
                    
            return True
            
        except Exception as e:
            logger.warning(f"Failed to check content type for URL {url}: {e}")
            return True  # Default to allowing if we can't determine
    
    def get_filter_name(self) -> str:
        return f"ContentTypeFilter(allowed={self.allowed_types}, blocked_ext={self.blocked_extensions})"

class DepthFilter(URLFilter):
    """
    Filter URLs based on crawling depth
    
    Examples:
        # Only crawl pages within 2 levels
        filter = DepthFilter(max_depth=2)
        
        # Skip the homepage, start from level 1
        filter = DepthFilter(min_depth=1, max_depth=3)
    """
    
    def __init__(self, min_depth: int = 0, max_depth: int = 10):
        self.min_depth = min_depth
        self.max_depth = max_depth
    
    def should_crawl(self, url: str, context: Dict[str, Any] = None) -> bool:
        if context and 'depth' in context:
            depth = context['depth']
            return self.min_depth <= depth <= self.max_depth
        return True  # Allow if depth not specified
    
    def get_filter_name(self) -> str:
        return f"DepthFilter(min={self.min_depth}, max={self.max_depth})"

class PathLengthFilter(URLFilter):
    """
    Filter URLs based on path complexity/length
    
    Examples:
        # Avoid very deep nested paths (likely pagination/filters)
        filter = PathLengthFilter(max_path_segments=5)
        
        # Skip homepage and require some path depth
        filter = PathLengthFilter(min_path_segments=1)
    """
    
    def __init__(self, min_path_segments: int = 0, max_path_segments: int = 10):
        self.min_path_segments = min_path_segments
        self.max_path_segments = max_path_segments
    
    def should_crawl(self, url: str, context: Dict[str, Any] = None) -> bool:
        try:
            path = urlparse(url).path
            # Count path segments (split by '/', filter empty)
            segments = [s for s in path.split('/') if s]
            segment_count = len(segments)
            
            return self.min_path_segments <= segment_count <= self.max_path_segments
            
        except Exception as e:
            logger.warning(f"Failed to analyze path length for URL {url}: {e}")
            return True

    def get_filter_name(self) -> str:
        return f"PathLengthFilter(min={self.min_path_segments}, max={self.max_path_segments})"

class QueryParameterFilter(URLFilter):
    """
    Filter URLs based on query parameters
    
    Examples:
        # Exclude search and filter URLs
        filter = QueryParameterFilter(blocked_params=["search", "filter", "sort"])
        
        # Only allow specific parameter patterns
        filter = QueryParameterFilter(allowed_params=["page", "category"])
    """
    
    def __init__(self, allowed_params: List[str] = None, blocked_params: List[str] = None, max_params: int = 5):
        self.allowed_params = [p.lower() for p in (allowed_params or [])]
        self.blocked_params = [p.lower() for p in (blocked_params or [])]
        self.max_params = max_params
    
    def should_crawl(self, url: str, context: Dict[str, Any] = None) -> bool:
        try:
            from urllib.parse import parse_qs
            
            parsed_url = urlparse(url)
            if not parsed_url.query:
                return True  # No parameters, allow
            
            params = parse_qs(parsed_url.query)
            param_names = [p.lower() for p in params.keys()]
            
            # Check parameter count limit
            if len(param_names) > self.max_params:
                return False
            
            # Check blocked parameters
            if self.blocked_params:
                for blocked_param in self.blocked_params:
                    if blocked_param in param_names:
                        return False
            
            # Check allowed parameters
            if self.allowed_params:
                for param_name in param_names:
                    if param_name not in self.allowed_params:
                        return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Failed to analyze query parameters for URL {url}: {e}")
            return True
    
    def get_filter_name(self) -> str:
        return f"QueryParameterFilter(allowed={self.allowed_params}, blocked={self.blocked_params})"

class FilterChain:
    """
    Chains multiple filters together with AND/OR logic
    
    Examples:
        # Must pass ALL filters
        chain = FilterChain([
            DomainFilter(allowed_domains=["company.com"]),
            URLPatternFilter(include=["*/contact*", "*/about*"]),
            DepthFilter(max_depth=3)
        ], logic="AND")
        
        # Must pass ANY filter  
        chain = FilterChain([
            URLPatternFilter(include=["*/contact*"]),
            URLPatternFilter(include=["*/about*"])
        ], logic="OR")
    """
    
    def __init__(self, filters: List[URLFilter], logic: str = "AND"):
        self.filters = filters
        self.logic = logic.upper()
        
        if self.logic not in ["AND", "OR"]:
            raise ValueError("Filter logic must be 'AND' or 'OR'")
    
    def should_crawl(self, url: str, context: Dict[str, Any] = None) -> bool:
        if not self.filters:
            return True
        
        results = []
        for filter_obj in self.filters:
            try:
                result = filter_obj.should_crawl(url, context)
                results.append(result)
            except Exception as e:
                logger.warning(f"Filter {filter_obj.get_filter_name()} failed for URL {url}: {e}")
                results.append(False)  # Fail safe
        
        if self.logic == "AND":
            return all(results)
        else:  # OR
            return any(results)
    
    def get_filter_info(self) -> Dict[str, Any]:
        return {
            "logic": self.logic,
            "filter_count": len(self.filters),
            "filters": [f.get_filter_name() for f in self.filters]
        }

# Pre-built filter configurations for common use cases
class CommonFilters:
    """Pre-built filter configurations for common crawling scenarios"""
    
    @staticmethod
    def contact_discovery() -> FilterChain:
        """Filter for finding contact and company information pages"""
        return FilterChain([
            URLPatternFilter(include=[
                "*/contact*", "*/about*", "*/team*", "*/staff*",
                "*/leadership*", "*/management*", "*/executive*",
                "*/office*", "*/location*", "*/address*"
            ]),
            DepthFilter(max_depth=3),
            PathLengthFilter(max_path_segments=5),
            QueryParameterFilter(max_params=2)
        ])
    
    @staticmethod
    def product_discovery() -> FilterChain:
        """Filter for finding product and service pages"""
        return FilterChain([
            URLPatternFilter(include=[
                "*/product*", "*/service*", "*/solution*",
                "*/offering*", "*/catalog*", "*/shop*"
            ], exclude=[
                "*/cart*", "*/checkout*", "*/payment*"
            ]),
            DepthFilter(max_depth=4),
            ContentTypeFilter(allowed_types=["text/html"])
        ])
    
    @staticmethod
    def news_content() -> FilterChain:
        """Filter for finding news and blog content"""
        return FilterChain([
            URLPatternFilter(include=[
                "*/news*", "*/blog*", "*/article*", "*/post*",
                "*/press*", "*/announcement*", "*/update*"
            ]),
            DepthFilter(max_depth=3),
            QueryParameterFilter(blocked_params=["search", "tag", "filter"])
        ])
    
    @staticmethod
    def comprehensive_discovery() -> FilterChain:
        """Comprehensive filter for general site exploration"""
        return FilterChain([
            URLPatternFilter(exclude=[
                "*/admin*", "*/login*", "*/register*", "*/cart*",
                "*/checkout*", "*/payment*", "*/api/*", "*/download*"
            ]),
            DepthFilter(max_depth=4),
            PathLengthFilter(max_path_segments=6),
            ContentTypeFilter(),  # Uses default blocked extensions
            QueryParameterFilter(max_params=3)
        ])
