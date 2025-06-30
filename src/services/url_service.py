#!/usr/bin/env python3
"""
URL Service
Handles URL validation, parsing, normalization, and analysis
"""

import asyncio
import aiohttp
import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse, urljoin, urlunparse, parse_qs, urlencode
import tldextract
from dataclasses import dataclass

logger = logging.getLogger("url_service")

@dataclass
class URLValidationResult:
    """Result of URL validation"""
    is_valid: bool
    normalized_url: str
    domain: str
    scheme: str
    errors: List[str]
    warnings: List[str]

class URLService:
    """
    Comprehensive URL service for validation, parsing, and analysis
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self.validation_cache: Dict[str, URLValidationResult] = {}
        self.domain_cache: Dict[str, Dict[str, Any]] = {}
        self.false_positives = set()
        
        # Common URL patterns for different site types
        self.url_patterns = {
            "ecommerce": [
                r"/product/", r"/item/", r"/shop/", r"/store/",
                r"/cart", r"/checkout", r"/catalog/"
            ],
            "social": [
                r"/profile/", r"/user/", r"/people/", r"/connect/",
                r"/follow", r"/friend", r"/group/"
            ],
            "news": [
                r"/article/", r"/news/", r"/story/", r"/post/",
                r"/blog/", r"/press/"
            ],
            "directory": [
                r"/listing/", r"/business/", r"/directory/",
                r"/search", r"/browse", r"/category/"
            ]
        }
    
    async def initialize(self):
        """Initialize the service"""
        if not self.session:
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=10)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
    async def validate_url(self, url: str, check_reachability: bool = True) -> URLValidationResult:
        """
        Comprehensive URL validation
        
        Args:
            url: URL to validate
            check_reachability: Whether to check if URL is reachable
            
        Returns:
            URLValidationResult object
        """
        
        # Check cache first
        cache_key = f"{url}:{check_reachability}"
        if cache_key in self.validation_cache:
            return self.validation_cache[cache_key]
        
        errors = []
        warnings = []
        normalized_url = url
        
        try:
            # Basic format validation
            if not url or not isinstance(url, str):
                errors.append("URL must be a non-empty string")
                return self._create_validation_result(False, url, "", "", errors, warnings)
            
            # Parse URL
            parsed = urlparse(url.strip())
            
            # Validate scheme
            if not parsed.scheme:
                # Try to add scheme
                url = "https://" + url
                parsed = urlparse(url)
                warnings.append("Added missing https:// scheme")
            
            if parsed.scheme not in ["http", "https"]:
                errors.append(f"Invalid scheme: {parsed.scheme}")
            
            # Validate domain
            if not parsed.netloc:
                errors.append("Missing domain")
            else:
                # Check domain format
                domain_pattern = re.compile(
                    r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
                    r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
                )
                
                if not domain_pattern.match(parsed.netloc.split(':')[0]):
                    errors.append("Invalid domain format")
            
            # Normalize URL
            normalized_url = self.normalize_url(url)
            
            # Check for common false positives
            if self._is_false_positive(normalized_url):
                warnings.append("URL appears to be a false positive")
            
            # Reachability check
            if check_reachability and not errors:
                is_reachable = await self._check_reachability(normalized_url)
                if not is_reachable:
                    warnings.append("URL is not reachable")
            
            result = self._create_validation_result(
                len(errors) == 0, normalized_url, 
                parsed.netloc, parsed.scheme, errors, warnings
            )
            
            # Cache result
            self.validation_cache[cache_key] = result
            return result
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return self._create_validation_result(False, url, "", "", errors, warnings)
    
    def _create_validation_result(self, is_valid: bool, url: str, domain: str, 
                                 scheme: str, errors: List[str], warnings: List[str]) -> URLValidationResult:
        """Create URL validation result"""
        return URLValidationResult(
            is_valid=is_valid,
            normalized_url=url,
            domain=domain,
            scheme=scheme,
            errors=errors,
            warnings=warnings
        )
    
    async def _check_reachability(self, url: str) -> bool:
        """Check if URL is reachable"""
        try:
            await self.initialize()
            async with self.session.head(url, allow_redirects=True) as response:
                return response.status < 400
        except Exception:
            return False
    
    def _is_false_positive(self, url: str) -> bool:
        """Check if URL is a known false positive"""
        false_positive_patterns = [
            r'mailto:', r'tel:', r'javascript:', r'#',
            r'\.css$', r'\.js$', r'\.jpg$', r'\.png$', r'\.gif$',
            r'\.pdf$', r'\.doc$', r'\.zip$'
        ]
        
        for pattern in false_positive_patterns:
            if re.search(pattern, url.lower()):
                return True
        
        return url in self.false_positives
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URL for consistent processing
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL string
        """
        
        try:
            # Remove extra whitespace
            url = url.strip()
            
            # Parse URL
            parsed = urlparse(url)
            
            # Ensure scheme
            if not parsed.scheme:
                url = "https://" + url
                parsed = urlparse(url)
            
            # Normalize domain (lowercase)
            domain = parsed.netloc.lower()
            
            # Remove default ports
            if (parsed.scheme == "http" and ":80" in domain):
                domain = domain.replace(":80", "")
            elif (parsed.scheme == "https" and ":443" in domain):
                domain = domain.replace(":443", "")
            
            # Normalize path
            path = parsed.path
            if not path:
                path = "/"
            
            # Remove trailing slash for non-root paths
            if path != "/" and path.endswith("/"):
                path = path.rstrip("/")
            
            # Rebuild URL
            normalized = urlunparse((
                parsed.scheme,
                domain,
                path,
                parsed.params,
                parsed.query,
                ""  # Remove fragment
            ))
            
            return normalized
            
        except Exception as e:
            logger.warning(f"URL normalization failed for {url}: {e}")
            return url
    
    def join_urls(self, base_url: str, relative_url: str) -> str:
        """
        Join base URL with relative URL
        
        Args:
            base_url: Base URL
            relative_url: Relative URL or absolute URL
            
        Returns:
            Joined URL
        """
        
        try:
            return urljoin(base_url, relative_url)
        except Exception:
            return relative_url
    
    def extract_urls_from_text(self, text: str) -> List[str]:
        """
        Extract URLs from text using regex
        
        Args:
            text: Text to search
            
        Returns:
            List of found URLs
        """
        
        url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        return url_pattern.findall(text)
    
    def categorize_url(self, url: str) -> str:
        """
        Categorize URL based on patterns
        
        Args:
            url: URL to categorize
            
        Returns:
            Category string
        """
        
        url_lower = url.lower()
        
        for category, patterns in self.url_patterns.items():
            for pattern in patterns:
                if re.search(pattern, url_lower):
                    return category
        
        return "general"
    
    def build_url(self, base_url: str, path: str = "", params: Dict[str, Any] = None) -> str:
        """
        Build URL from components
        
        Args:
            base_url: Base URL
            path: Path to append
            params: Query parameters
            
        Returns:
            Complete URL
        """
        
        try:
            # Ensure base_url ends without slash if path starts with slash
            if path.startswith("/"):
                base_url = base_url.rstrip("/")
            elif path and not base_url.endswith("/"):
                base_url += "/"
            
            url = base_url + path
            
            # Add query parameters
            if params:
                query_params = []
                for key, value in params.items():
                    if isinstance(value, list):
                        for v in value:
                            query_params.append(f"{key}={v}")
                    else:
                        query_params.append(f"{key}={value}")
                
                if query_params:
                    url += "?" + "&".join(query_params)
            
            return url
            
        except Exception as e:
            logger.error(f"Failed to build URL: {e}")
            return base_url
    
    def extract_domain_info(self, url: str) -> Dict[str, str]:
        """
        Extract detailed domain information
        
        Args:
            url: URL to analyze
            
        Returns:
            Dictionary with domain information
        """
        
        try:
            extracted = tldextract.extract(url)
            parsed = urlparse(url)
            
            return {
                "full_domain": extracted.domain + '.' + extracted.suffix if extracted.domain else '',
                "domain": extracted.domain,
                "subdomain": extracted.subdomain,
                "tld": extracted.suffix,
                "port": str(parsed.port) if parsed.port else None,
                "scheme": parsed.scheme,
                "netloc": parsed.netloc
            }
            
        except Exception as e:
            logger.error(f"Failed to extract domain info: {e}")
            return {}
    
    def is_same_domain(self, url1: str, url2: str) -> bool:
        """
        Check if two URLs belong to the same domain
        
        Args:
            url1, url2: URLs to compare
            
        Returns:
            Boolean indicating if domains match
        """
        
        try:
            domain1 = tldextract.extract(url1)
            domain2 = tldextract.extract(url2)
            
            return (domain1.domain == domain2.domain and 
                    domain1.suffix == domain2.suffix)
        except Exception:
            return False
    
    def get_robots_txt_url(self, url: str) -> str:
        """
        Get the robots.txt URL for a given URL
        
        Args:
            url: Website URL
            
        Returns:
            robots.txt URL
        """
        
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            return f"{base_url}/robots.txt"
        except Exception:
            return None
    
    def get_sitemap_urls(self, url: str) -> List[str]:
        """
        Get potential sitemap URLs for a website
        
        Args:
            url: Website URL
            
        Returns:
            List of potential sitemap URLs
        """
        
        try:
            parsed = urlparse(url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            
            return [
                f"{base_url}/sitemap.xml",
                f"{base_url}/sitemap_index.xml",
                f"{base_url}/sitemaps.xml",
                f"{base_url}/sitemap.txt",
                f"{base_url}/robots.txt"  # Often contains sitemap references
            ]
        except Exception:
            return []
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        
        return {
            "validation_cache_size": len(self.validation_cache),
            "domain_cache_size": len(self.domain_cache),
            "supported_patterns": list(self.url_patterns.keys()),
            "false_positives_count": len(self.false_positives),
            "service_initialized": self.session is not None
        }
    
    async def cleanup(self):
        """Clean up resources"""
        
        if self.session:
            await self.session.close()
            self.session = None
        
        # Clear caches
        self.validation_cache.clear()
        self.domain_cache.clear()
        
        logger.info("URL service cleanup completed")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
