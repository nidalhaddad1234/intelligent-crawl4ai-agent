#!/usr/bin/env python3
"""
Improved Web UI Server - Patch for URL extraction
Apply this patch to web_ui_server.py
"""

# Add this import at the top of web_ui_server.py:
# from src.utils.url_extractor import parse_message_with_urls, extract_urls_from_text

# Replace the process_chat_message method with this improved version:

async def process_chat_message(self, session_id: str, message: str, urls: Optional[List[str]] = None) -> str:
    """Process a chat message and determine the appropriate action"""
    
    # Extract URLs from message if not provided separately
    extracted_urls = []
    cleaned_message = message
    
    if not urls:
        # Try to extract URLs from the message text
        cleaned_message, extracted_urls = parse_message_with_urls(message)
        urls = extracted_urls if extracted_urls else None
    
    # Combine URLs from parameter and extracted URLs
    all_urls = []
    if urls:
        all_urls.extend(urls)
    if extracted_urls:
        all_urls.extend([url for url in extracted_urls if url not in urls])
    
    # Remove duplicates
    all_urls = list(dict.fromkeys(all_urls)) if all_urls else None
    
    # Log for debugging
    logger.info(f"Processing message: '{cleaned_message}' with URLs: {all_urls}")
    
    # Use cleaned message for intent detection
    message_lower = cleaned_message.lower()
    
    # Analyze intent - check for analyze/check/examine keywords
    if any(keyword in message_lower for keyword in ['analyze', 'analyse', 'check', 'examine', 'inspect', 'review']):
        if all_urls and len(all_urls) == 1:
            return await self._handle_analysis_request(all_urls[0], message)
        elif all_urls and len(all_urls) > 1:
            # Analyze multiple sites
            responses = []
            for i, url in enumerate(all_urls[:3], 1):  # Limit to 3 for UI clarity
                responses.append(f"\n**Analysis {i}: {url}**")
                analysis = await self._handle_single_analysis(url)
                responses.append(analysis)
            return "\n".join(responses)
        else:
            return "To analyze a website, please provide a URL. For example: 'Analyze https://example.com' or use the URL input field below."
    
    # Scraping intent - check for scrape/extract/crawl/get keywords
    elif any(keyword in message_lower for keyword in ['scrape', 'extract', 'get data', 'crawl', 'fetch', 'pull', 'collect', 'gather']):
        if all_urls:
            return await self._handle_scraping_request(session_id, message, all_urls)
        else:
            return "I'd be happy to help you scrape data! Please provide the URLs you'd like me to process. You can type them directly (e.g., 'Scrape https://example.com') or use the URL input field."
    
    # Job status intent
    elif any(keyword in message_lower for keyword in ['job', 'status', 'progress', 'check job', 'job status']):
        return await self._handle_job_status_request(message)
    
    # Search intent
    elif any(keyword in message_lower for keyword in ['search', 'find', 'look for', 'query']):
        return await self._handle_search_request(message)
    
    # Export intent
    elif any(keyword in message_lower for keyword in ['export', 'download', 'save', 'csv', 'excel', 'json']):
        return await self._handle_export_request(message)
    
    # Help intent
    elif any(keyword in message_lower for keyword in ['help', 'what can you do', 'capabilities', 'how to', 'guide']):
        return self._get_help_message()
    
    # If URLs are present but no clear intent, suggest actions
    elif all_urls:
        url_list = '\n'.join([f"• {url}" for url in all_urls[:5]])
        return f"I found these URLs in your message:\n{url_list}\n\nWhat would you like me to do with them?\n\n**Quick Actions:**\n• Type 'analyze' to analyze the website structure\n• Type 'scrape' to extract data\n• Type 'scrape contact info' to extract contact details\n• Type 'scrape products' to extract product information"
    
    else:
        return self._get_conversational_response(message)

# Add this helper method for single URL analysis:
async def _handle_single_analysis(self, url: str) -> str:
    """Handle analysis for a single URL"""
    try:
        # Initialize analyzer if needed
        if not self.website_analyzer:
            return "❌ Website analyzer is not initialized. Please check system status."
        
        # Analyze the website
        analysis = await self.website_analyzer.analyze_website(url)
        
        # Format the analysis result
        framework = analysis.get('framework', 'Unknown')
        has_api = analysis.get('has_api', False)
        anti_bot = analysis.get('anti_bot_measures', [])
        recommended_strategy = analysis.get('recommended_strategy', 'DirectoryCSSStrategy')
        confidence = analysis.get('confidence', 0.5)
        
        anti_bot_status = 'Detected: ' + ', '.join(anti_bot) if anti_bot else 'None detected'
        
        return f"""🔍 **Website Analysis for {url}:**

• **Framework**: {framework}
• **Has API**: {'Yes' if has_api else 'No'}
• **Anti-bot measures**: {anti_bot_status}
• **Recommended strategy**: {recommended_strategy}
• **Confidence**: {confidence:.0%}

**Extraction Capabilities Detected:**
{self._get_extraction_capabilities(analysis)}

Would you like me to proceed with scraping using the recommended strategy?"""
        
    except Exception as e:
        logger.error(f"Analysis request failed: {e}")
        return f"❌ Sorry, I couldn't analyze the website: {str(e)}"

# Add helper method for extraction capabilities:
def _get_extraction_capabilities(self, analysis: Dict[str, Any]) -> str:
    """Get extraction capabilities from analysis"""
    capabilities = []
    
    # Check for common data types
    if analysis.get('has_products', False):
        capabilities.append("• 🛍️ Product listings with prices")
    if analysis.get('has_contact', False):
        capabilities.append("• 📧 Contact information (email, phone, address)")
    if analysis.get('has_business_info', False):
        capabilities.append("• 🏢 Business details and descriptions")
    if analysis.get('has_reviews', False):
        capabilities.append("• ⭐ Reviews and ratings")
    if analysis.get('has_social_links', False):
        capabilities.append("• 🔗 Social media links")
    
    return '\n'.join(capabilities) if capabilities else "• 📄 General content extraction available"

# Update the _handle_analysis_request method:
async def _handle_analysis_request(self, url: str, message: str) -> str:
    """Handle a website analysis request"""
    
    # Check if specific analysis is requested
    message_lower = message.lower()
    
    if 'contact' in message_lower:
        analysis_type = "contact information extraction"
    elif 'product' in message_lower:
        analysis_type = "product data extraction"
    elif 'price' in message_lower or 'pricing' in message_lower:
        analysis_type = "pricing information extraction"
    elif 'review' in message_lower:
        analysis_type = "reviews and ratings extraction"
    else:
        analysis_type = "general data extraction"
    
    response = await self._handle_single_analysis(url)
    response += f"\n\n**Specific Request**: Optimized for {analysis_type}"
    
    return response
