#!/usr/bin/env python3
"""
URL Extraction Utilities
Extracts URLs from text messages
"""

import re
from typing import List, Tuple
from urllib.parse import urlparse

def extract_urls_from_text(text: str) -> List[str]:
    """
    Extract URLs from text using multiple patterns
    
    Args:
        text: Input text containing URLs
        
    Returns:
        List of extracted URLs
    """
    urls = []
    
    # Pattern 1: URLs with protocol
    url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    urls.extend(re.findall(url_pattern, text))
    
    # Pattern 2: URLs without protocol but with www
    www_pattern = r'www\.[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
    www_urls = re.findall(www_pattern, text)
    urls.extend([f'https://{url}' for url in www_urls])
    
    # Pattern 3: Common domains without www (careful with false positives)
    domain_pattern = r'\b(?:[a-zA-Z0-9-]+\.)+(?:com|org|net|edu|gov|io|co|uk|de|fr|jp|au|ca|in|br|mx|nl|se|it|es|ru|cn)\b(?:/[-a-zA-Z0-9()@:%_\+.~#?&=]*)?'
    potential_domains = re.findall(domain_pattern, text)
    
    # Filter out common false positives
    false_positives = ['example.com', 'test.com', 'email.com', 'mail.com']
    for domain in potential_domains:
        if domain not in false_positives and domain not in urls:
            # Check if it's likely a URL (has path or looks like a domain)
            if '/' in domain or (domain.count('.') >= 1 and len(domain) > 5):
                urls.append(f'https://{domain}')
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        # Normalize URL
        normalized = url.rstrip('/')
        if normalized not in seen:
            seen.add(normalized)
            unique_urls.append(url)
    
    return unique_urls

def parse_message_with_urls(message: str) -> Tuple[str, List[str]]:
    """
    Parse a message to extract URLs and clean the message text
    
    Args:
        message: Input message
        
    Returns:
        Tuple of (cleaned_message, extracted_urls)
    """
    urls = extract_urls_from_text(message)
    
    # Remove URLs from message for cleaner intent detection
    cleaned_message = message
    for url in urls:
        cleaned_message = cleaned_message.replace(url, '')
    
    # Also remove common URL indicators
    cleaned_message = re.sub(r'\s*:\s*$', '', cleaned_message)  # Remove trailing colons
    cleaned_message = re.sub(r'\s+', ' ', cleaned_message).strip()  # Clean whitespace
    
    return cleaned_message, urls

def validate_url(url: str) -> bool:
    """
    Validate if a string is a valid URL
    
    Args:
        url: URL to validate
        
    Returns:
        Boolean indicating if URL is valid
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def normalize_url(url: str) -> str:
    """
    Normalize a URL by adding protocol if missing
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL with protocol
    """
    if not url.startswith(('http://', 'https://')):
        # Check if it starts with www
        if url.startswith('www.'):
            return f'https://{url}'
        else:
            # Assume it's a domain
            return f'https://{url}'
    return url
