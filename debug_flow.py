#!/usr/bin/env python3
"""
Debug script to test the complete flow
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.url_extractor import parse_message_with_urls

# Test the flow
test_messages = [
    "Analyze https://paris-change.com",
    "how much is paris-change.com is changing the euro to dollars ?",
    "Scrape data from example.com",
]

print("🧪 Testing Message Flow...\n")

for msg in test_messages:
    print(f"Input: '{msg}'")
    cleaned, urls = parse_message_with_urls(msg)
    print(f"Cleaned: '{cleaned}'")
    print(f"URLs: {urls}")
    print(f"Intent: ", end="")
    
    # Check intent
    msg_lower = cleaned.lower()
    if any(keyword in msg_lower for keyword in ['analyze', 'check', 'examine']):
        print("ANALYZE")
    elif any(keyword in msg_lower for keyword in ['scrape', 'extract', 'get data']):
        print("SCRAPE")
    else:
        print("UNKNOWN")
    print("-" * 50)
