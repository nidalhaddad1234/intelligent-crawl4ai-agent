#!/usr/bin/env python3
"""
Test URL extraction functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.url_extractor import extract_urls_from_text, parse_message_with_urls

# Test cases
test_messages = [
    "Analyze the structure of this website:https://paris-change.com",
    "Check out https://example.com and www.test.org for data",
    "Please scrape example.com/products and another-site.io",
    "Analyze https://paris-change.com and suggest the best extraction strategy for: - Contact information - Product/service details - Pricing information",
    "Extract data from these sites: site1.com, site2.net, https://site3.org",
    "Just a message without any URLs",
    "Email me at test@example.com about site.com",  # Should extract site.com but not email
]

print("🧪 Testing URL Extraction...\n")

for i, message in enumerate(test_messages, 1):
    print(f"Test {i}: {message}")
    print("-" * 80)
    
    # Test URL extraction
    urls = extract_urls_from_text(message)
    print(f"Extracted URLs: {urls}")
    
    # Test message parsing
    cleaned_msg, extracted_urls = parse_message_with_urls(message)
    print(f"Cleaned message: '{cleaned_msg}'")
    print(f"URLs from parse: {extracted_urls}")
    print("\n")

print("✅ URL extraction tests completed!")
