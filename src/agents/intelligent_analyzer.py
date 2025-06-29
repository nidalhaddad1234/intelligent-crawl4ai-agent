#!/usr/bin/env python3
"""
Intelligent Website Analyzer
Analyzes websites and selects optimal extraction strategies
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, CSSExtractionStrategy, JsonCssExtractionStrategy

logger = logging.getLogger("intelligent_analyzer")

class WebsiteType(Enum):
    DIRECTORY_LISTING = "directory_listing"
    E_COMMERCE = "e_commerce"
    SOCIAL_MEDIA = "social_media"
    NEWS_ARTICLE = "news_article"
    CORPORATE = "corporate"
    FORM_HEAVY = "form_heavy"
    SPA_DYNAMIC = "spa_dynamic"
    DATA_TABLE = "data_table"

class ExtractionPurpose(Enum):
    COMPANY_INFO = "company_info"
    CONTACT_DISCOVERY = "contact_discovery"
    PRODUCT_DATA = "product_data"
    PROFILE_INFO = "profile_info"
    NEWS_CONTENT = "news_content"
    FORM_AUTOMATION = "form_automation"
    GENERAL_DATA = "general_data"

@dataclass
class WebsiteAnalysis:
    url: str
    website_type: WebsiteType
    has_javascript: bool
    has_infinite_scroll: bool
    has_forms: bool
    has_auth_required: bool
    has_captcha: bool
    content_dynamically_loaded: bool
    estimated_complexity: str
    detected_frameworks: List[str]
    anti_bot_measures: List[str]
    content_patterns: List[str]
    
class IntelligentWebsiteAnalyzer:
    """Analyzes websites and determines optimal extraction strategies"""
    
    def __init__(self, ollama_client):
        self.ollama_client = ollama_client
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            page_timeout=30000
        )
    
    async def analyze_website(self, url: str) -> WebsiteAnalysis:
        """Comprehensive website analysis using AI + direct inspection"""
        
        logger.info(f"Analyzing website: {url}")
        
        # Step 1: Quick reconnaissance crawl
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            recon_config = CrawlerRunConfig(
                cache_mode="bypass",
                wait_for="css:body",
                timeout=15000,
                js_code=self._get_analysis_javascript(),
                exclude_external_links=True
            )
            
            try:
                result = await crawler.arun(url=url, config=recon_config)
                
                # Step 2: Extract technical analysis
                tech_analysis = await self._extract_technical_data(result)
                
                # Step 3: AI-powered content analysis
                ai_analysis = await self._ai_analyze_content(url, result.cleaned_html[:8000])
                
                # Step 4: Combine analyses
                return WebsiteAnalysis(
                    url=url,
                    website_type=WebsiteType(ai_analysis.get("website_type", "corporate")),
                    has_javascript=tech_analysis.get("hasJavaScript", True),
                    has_infinite_scroll=tech_analysis.get("hasInfiniteScroll", False),
                    has_forms=tech_analysis.get("formsCount", 0) > 0,
                    has_auth_required=self._detect_auth_required(result.cleaned_html),
                    has_captcha=tech_analysis.get("hasCaptcha", False),
                    content_dynamically_loaded=len(tech_analysis.get("frameworks", [])) > 0,
                    estimated_complexity=ai_analysis.get("complexity", "medium"),
                    detected_frameworks=tech_analysis.get("frameworks", []),
                    anti_bot_measures=tech_analysis.get("antiBot", []),
                    content_patterns=ai_analysis.get("content_patterns", [])
                )
                
            except Exception as e:
                logger.warning(f"Website analysis failed for {url}: {e}")
                return self._fallback_analysis(url)
    
    def _get_analysis_javascript(self) -> str:
        """JavaScript code to analyze website characteristics"""
        return """
        // Comprehensive website analysis
        window.websiteAnalysis = {
            hasJavaScript: true,
            frameworks: [],
            formsCount: document.forms.length,
            hasInfiniteScroll: false,
            hasCaptcha: false,
            antiBot: [],
            contentTypes: [],
            structuredData: false,
            hasDataTables: false,
            socialLinks: [],
            contactInfo: []
        };
        
        // Detect JavaScript frameworks
        if (window.React || document.querySelector('[data-reactroot]')) {
            window.websiteAnalysis.frameworks.push('React');
        }
        if (window.Vue || document.querySelector('[data-v-]')) {
            window.websiteAnalysis.frameworks.push('Vue');
        }
        if (window.angular || document.querySelector('[ng-app]')) {
            window.websiteAnalysis.frameworks.push('Angular');
        }
        if (window.jQuery || window.$) {
            window.websiteAnalysis.frameworks.push('jQuery');
        }
        
        // Check for structured data
        if (document.querySelector('script[type="application/ld+json"]')) {
            window.websiteAnalysis.structuredData = true;
        }
        
        // Check for data tables
        if (document.querySelectorAll('table').length > 2) {
            window.websiteAnalysis.hasDataTables = true;
        }
        
        // Detect CAPTCHA
        const captchaSelectors = ['.g-recaptcha', '[data-sitekey]', 'iframe[src*="recaptcha"]', '.h-captcha'];
        window.websiteAnalysis.hasCaptcha = captchaSelectors.some(sel => 
            document.querySelector(sel) !== null
        );
        
        // Detect anti-bot measures
        if (document.querySelector('[data-cf-beacon]') || document.querySelector('script[src*="cloudflare"]')) {
            window.websiteAnalysis.antiBot.push('Cloudflare');
        }
        if (document.querySelector('script[src*="bot"]') || document.querySelector('[data-bot-protection]')) {
            window.websiteAnalysis.antiBot.push('Bot Detection');
        }
        
        // Look for contact information patterns
        const bodyText = document.body.innerText.toLowerCase();
        if (bodyText.includes('@') && bodyText.includes('.com')) {
            window.websiteAnalysis.contactInfo.push('email');
        }
        if (bodyText.match(/\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b/)) {
            window.websiteAnalysis.contactInfo.push('phone');
        }
        
        // Detect infinite scroll (basic check)
        const initialHeight = document.documentElement.scrollHeight;
        window.scrollTo(0, document.body.scrollHeight);
        setTimeout(() => {
            if (document.documentElement.scrollHeight > initialHeight) {
                window.websiteAnalysis.hasInfiniteScroll = true;
            }
        }, 2000);
        """
    
    async def _extract_technical_data(self, crawl_result) -> Dict[str, Any]:
        """Extract technical analysis data from crawl result"""
        try:
            # This would normally extract the JavaScript analysis results
            # For now, return basic analysis based on HTML content
            html_content = crawl_result.html.lower()
            
            return {
                "hasJavaScript": any(framework in html_content for framework in ['react', 'vue', 'angular', 'jquery']),
                "frameworks": self._detect_frameworks(html_content),
                "formsCount": html_content.count('<form'),
                "hasInfiniteScroll": 'infinite' in html_content or 'lazy' in html_content,
                "hasCaptcha": any(captcha in html_content for captcha in ['recaptcha', 'captcha', 'hcaptcha']),
                "antiBot": self._detect_anti_bot(html_content),
                "structuredData": 'application/ld+json' in html_content
            }
        except Exception as e:
            logger.warning(f"Technical analysis failed: {e}")
            return {}
    
    def _detect_frameworks(self, html_content: str) -> List[str]:
        """Detect JavaScript frameworks from HTML"""
        frameworks = []
        if 'react' in html_content or 'data-reactroot' in html_content:
            frameworks.append('React')
        if 'vue' in html_content or 'data-v-' in html_content:
            frameworks.append('Vue')
        if 'angular' in html_content or 'ng-app' in html_content:
            frameworks.append('Angular')
        if 'jquery' in html_content:
            frameworks.append('jQuery')
        return frameworks
    
    def _detect_anti_bot(self, html_content: str) -> List[str]:
        """Detect anti-bot measures"""
        measures = []
        if 'cloudflare' in html_content:
            measures.append('Cloudflare')
        if 'bot' in html_content and 'protection' in html_content:
            measures.append('Bot Protection')
        if 'rate limit' in html_content:
            measures.append('Rate Limiting')
        return measures
    
    async def _ai_analyze_content(self, url: str, html_sample: str) -> Dict[str, Any]:
        """Use AI to analyze website content and classify"""
        
        prompt = f"""
        Analyze this website and provide a detailed classification:
        
        URL: {url}
        HTML Content Sample: {html_sample}
        
        Please determine:
        1. Website Type: Choose from directory_listing, e_commerce, social_media, news_article, corporate, form_heavy, spa_dynamic, data_table
        2. Complexity Level: low, medium, or high
        3. Content Patterns: What types of structured content are present
        4. Extraction Challenges: What makes this site difficult to scrape
        
        Respond ONLY in valid JSON format:
        {{
            "website_type": "directory_listing",
            "complexity": "medium", 
            "content_patterns": ["business_listings", "contact_info", "addresses"],
            "extraction_challenges": ["dynamic_loading", "pagination"],
            "recommended_approach": "css_extraction",
            "confidence": 0.85
        }}
        """
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=prompt,
                format="json"
            )
            
            return json.loads(response)
            
        except Exception as e:
            logger.warning(f"AI content analysis failed: {e}")
            return {
                "website_type": "corporate",
                "complexity": "medium",
                "content_patterns": ["general"],
                "extraction_challenges": ["unknown"]
            }
    
    def _detect_auth_required(self, html: str) -> bool:
        """Detect if authentication is required"""
        auth_indicators = [
            "login", "sign in", "authentication required", 
            "please log in", "access denied", "unauthorized"
        ]
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in auth_indicators)
    
    def _fallback_analysis(self, url: str) -> WebsiteAnalysis:
        """Fallback analysis when main analysis fails"""
        return WebsiteAnalysis(
            url=url,
            website_type=WebsiteType.CORPORATE,
            has_javascript=True,
            has_infinite_scroll=False,
            has_forms=False,
            has_auth_required=False,
            has_captcha=False,
            content_dynamically_loaded=True,
            estimated_complexity="medium",
            detected_frameworks=[],
            anti_bot_measures=[],
            content_patterns=["unknown"]
        )
    
    async def execute_extraction(self, url: str, strategy) -> Dict[str, Any]:
        """Execute extraction using the selected strategy"""
        
        async with AsyncWebCrawler(config=self.browser_config) as crawler:
            
            # Configure extraction strategy
            if strategy.primary_strategy == "css_extraction":
                extraction_strategy = CSSExtractionStrategy(strategy.extraction_config)
            elif strategy.primary_strategy == "llm_extraction":
                extraction_strategy = LLMExtractionStrategy(
                    provider="ollama/llama3.1",
                    api_token="unused",
                    api_base="http://localhost:11434/v1",
                    schema=strategy.extraction_config.get("schema"),
                    extraction_type="schema" if "schema" in strategy.extraction_config else "text",
                    instruction=strategy.extraction_config.get("instruction", "Extract relevant data")
                )
            elif strategy.primary_strategy == "json_css_extraction":
                extraction_strategy = JsonCssExtractionStrategy(strategy.extraction_config)
            else:
                # Fallback to LLM
                extraction_strategy = LLMExtractionStrategy(
                    provider="ollama/llama3.1",
                    api_token="unused",
                    api_base="http://localhost:11434/v1",
                    instruction="Extract all relevant data from this webpage"
                )
            
            run_config = CrawlerRunConfig(
                extraction_strategy=extraction_strategy,
                cache_mode="bypass",
                **strategy.browser_config
            )
            
            try:
                result = await crawler.arun(url=url, config=run_config)
                
                extracted_data = {}
                if result.extracted_content:
                    try:
                        extracted_data = json.loads(result.extracted_content)
                    except:
                        extracted_data = {"text": result.extracted_content}
                
                return {
                    "success": True,
                    "url": url,
                    "strategy_used": strategy.primary_strategy,
                    "extracted_data": extracted_data,
                    "metadata": {
                        "title": result.metadata.get("title", ""),
                        "description": result.metadata.get("description", ""),
                        "word_count": len(result.cleaned_html.split()) if result.cleaned_html else 0,
                        "links_found": len(result.links) if hasattr(result, 'links') else 0
                    },
                    "strategy_reasoning": strategy.reasoning,
                    "confidence_score": strategy.estimated_success_rate
                }
                
            except Exception as e:
                logger.error(f"Extraction failed for {url}: {e}")
                
                # Try fallback strategies
                for fallback_strategy in strategy.fallback_strategies:
                    try:
                        if fallback_strategy == "css_extraction":
                            fallback_extraction = CSSExtractionStrategy({
                                "content": "body *:not(script):not(style)"
                            })
                        else:
                            fallback_extraction = LLMExtractionStrategy(
                                provider="ollama/llama3.1",
                                api_base="http://localhost:11434/v1",
                                instruction="Extract any relevant data from this webpage"
                            )
                        
                        run_config.extraction_strategy = fallback_extraction
                        result = await crawler.arun(url=url, config=run_config)
                        
                        return {
                            "success": True,
                            "url": url,
                            "strategy_used": f"{strategy.primary_strategy} -> {fallback_strategy}",
                            "extracted_data": json.loads(result.extracted_content) if result.extracted_content else {},
                            "metadata": {"fallback_used": True},
                            "note": "Primary strategy failed, used fallback"
                        }
                        
                    except Exception as fallback_error:
                        logger.warning(f"Fallback {fallback_strategy} also failed: {fallback_error}")
                        continue
                
                return {
                    "success": False,
                    "url": url,
                    "error": str(e),
                    "strategy_attempted": strategy.primary_strategy,
                    "fallbacks_tried": strategy.fallback_strategies
                }
    
    async def scrape_with_authentication(self, url: str, strategy, credentials: Dict[str, str]) -> Dict[str, Any]:
        """Execute scraping with authentication handling"""
        # This would integrate with the authentication automation
        # For now, return a placeholder implementation
        
        logger.info(f"Scraping with authentication: {url}")
        
        # TODO: Implement authentication workflow
        # 1. Detect login requirements
        # 2. Perform login with credentials
        # 3. Execute extraction with authenticated session
        # 4. Handle session management
        
        return {
            "success": False,
            "message": "Authentication scraping not yet implemented",
            "url": url
        }
