#!/usr/bin/env python3
"""
Enhanced Intelligent Analyzer
Production-ready website analysis with service-oriented architecture
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum
import time

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from crawl4ai.extraction_strategy import LLMExtractionStrategy, ExtractionStrategy, JsonCssExtractionStrategy

from services import VectorService
from ai_core.core.hybrid_ai_service import HybridAIService, create_production_ai_service

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
    UNKNOWN = "unknown"

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
    """Enhanced website analysis with comprehensive metadata"""
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
    
    # Enhanced fields
    data_quality_indicators: Dict[str, float]
    performance_metrics: Dict[str, float]
    accessibility_score: float
    seo_indicators: Dict[str, Any]
    security_features: List[str]
    analysis_confidence: float
    analysis_timestamp: float

class IntelligentAnalyzer:
    """
    Production-ready intelligent website analyzer using service architecture
    """
    
    def __init__(self, llm_service: HybridAIService = None, vector_service: VectorService = None):
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            page_timeout=30000
        )
        
        # Analysis cache for performance
        self.analysis_cache = {}
        self.cache_ttl = 3600  # 1 hour cache
        
    async def initialize(self) -> bool:
        """Initialize the analyzer with required services"""
        
        try:
            # Initialize services if not provided
            if not self.llm_service:
                self.llm_service = create_production_ai_service()
                # HybridAIService initializes automatically
            
            if not self.vector_service:
                from services import VectorService
                self.vector_service = VectorService(llm_service=self.llm_service)
                await self.vector_service.initialize()
            
            logger.info("Intelligent analyzer initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize intelligent analyzer: {e}")
            return False
    
    async def analyze_website(self, url: str, cache_enabled: bool = True) -> WebsiteAnalysis:
        """
        Comprehensive website analysis with caching and enhanced AI analysis
        
        Args:
            url: Website URL to analyze
            cache_enabled: Whether to use cached results
            
        Returns:
            WebsiteAnalysis object with comprehensive data
        """
        
        # Check cache first
        if cache_enabled and url in self.analysis_cache:
            cached_analysis, timestamp = self.analysis_cache[url]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Using cached analysis for {url}")
                return cached_analysis
        
        logger.info(f"Analyzing website: {url}")
        start_time = time.time()
        
        try:
            # Step 1: Reconnaissance crawl with enhanced data collection
            async with AsyncWebCrawler(config=self.browser_config) as crawler:
                recon_config = CrawlerRunConfig(
                    cache_mode="bypass",
                    wait_for="css:body",
                    timeout=15000,
                    js_code=self._get_enhanced_analysis_javascript(),
                    exclude_external_links=True
                )
                
                result = await crawler.arun(url=url, config=recon_config)
                
                # Step 2: Technical analysis from browser data
                tech_analysis = await self._extract_enhanced_technical_data(result)
                
                # Step 3: AI-powered comprehensive content analysis
                ai_analysis = await self._ai_analyze_content_comprehensive(
                    url, result.cleaned_html[:12000], result.metadata
                )
                
                # Step 4: Performance and quality assessment
                quality_metrics = self._assess_data_quality(result, tech_analysis)
                
                # Step 5: Security and accessibility analysis
                security_analysis = self._analyze_security_features(result.html)
                accessibility_score = self._calculate_accessibility_score(result.html)
                
                # Step 6: Check for similar analyzed websites
                similar_sites = await self._find_similar_analyzed_sites(ai_analysis)
                
                analysis_time = time.time() - start_time
                
                # Create comprehensive analysis
                analysis = WebsiteAnalysis(
                    url=url,
                    website_type=WebsiteType(ai_analysis.get("website_type", "unknown")),
                    has_javascript=tech_analysis.get("hasJavaScript", True),
                    has_infinite_scroll=tech_analysis.get("hasInfiniteScroll", False),
                    has_forms=tech_analysis.get("formsCount", 0) > 0,
                    has_auth_required=self._detect_auth_required(result.cleaned_html),
                    has_captcha=tech_analysis.get("hasCaptcha", False),
                    content_dynamically_loaded=len(tech_analysis.get("frameworks", [])) > 0,
                    estimated_complexity=ai_analysis.get("complexity", "medium"),
                    detected_frameworks=tech_analysis.get("frameworks", []),
                    anti_bot_measures=tech_analysis.get("antiBot", []),
                    content_patterns=ai_analysis.get("content_patterns", []),
                    
                    # Enhanced fields
                    data_quality_indicators=quality_metrics,
                    performance_metrics={
                        "analysis_time": analysis_time,
                        "page_load_estimate": tech_analysis.get("estimatedLoadTime", 0),
                        "content_size": len(result.cleaned_html),
                        "link_count": len(result.links) if hasattr(result, 'links') else 0
                    },
                    accessibility_score=accessibility_score,
                    seo_indicators={
                        "title_present": bool(result.metadata.get("title")),
                        "description_present": bool(result.metadata.get("description")),
                        "structured_data": tech_analysis.get("structuredData", False),
                        "meta_tags_count": tech_analysis.get("metaTagsCount", 0)
                    },
                    security_features=security_analysis,
                    analysis_confidence=ai_analysis.get("confidence", 0.5),
                    analysis_timestamp=time.time()
                )
                
                # Cache the analysis
                if cache_enabled:
                    self.analysis_cache[url] = (analysis, time.time())
                
                # Store analysis in vector service for learning
                await self._store_analysis_for_learning(analysis, ai_analysis)
                
                logger.info(f"Website analysis completed for {url} in {analysis_time:.2f}s")
                return analysis
                
        except Exception as e:
            logger.error(f"Website analysis failed for {url}: {e}")
            return self._create_fallback_analysis(url, str(e))
    
    def _get_enhanced_analysis_javascript(self) -> str:
        """Enhanced JavaScript for comprehensive website analysis"""
        
        return """
        // Enhanced website analysis with performance and accessibility checks
        window.websiteAnalysis = {
            // Basic structure
            hasJavaScript: true,
            frameworks: [],
            formsCount: document.forms.length,
            hasInfiniteScroll: false,
            hasCaptcha: false,
            antiBot: [],
            structuredData: false,
            
            // Content analysis
            contentTypes: [],
            hasDataTables: false,
            imageCount: document.images.length,
            linkCount: document.links.length,
            
            // Performance indicators
            estimatedLoadTime: 0,
            resourceCount: 0,
            
            // Accessibility indicators
            hasAltText: 0,
            hasAriaLabels: 0,
            hasHeadingStructure: false,
            
            // SEO indicators
            metaTagsCount: document.head.querySelectorAll('meta').length,
            hasOpenGraph: false,
            hasTwitterCards: false,
            
            // Security indicators
            hasCSP: false,
            mixedContent: false
        };
        
        // Framework detection with version info
        if (window.React || document.querySelector('[data-reactroot]') || document.querySelector('[data-react-checksum]')) {
            window.websiteAnalysis.frameworks.push('React');
        }
        if (window.Vue || document.querySelector('[data-v-]')) {
            window.websiteAnalysis.frameworks.push('Vue');
        }
        if (window.angular || document.querySelector('[ng-app]') || document.querySelector('[ng-controller]')) {
            window.websiteAnalysis.frameworks.push('Angular');
        }
        if (window.jQuery || window.$) {
            window.websiteAnalysis.frameworks.push('jQuery');
        }
        if (document.querySelector('[data-turbo]') || document.querySelector('[data-turbolinks]')) {
            window.websiteAnalysis.frameworks.push('Turbo');
        }
        
        // Structured data detection
        const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
        if (jsonLdScripts.length > 0) {
            window.websiteAnalysis.structuredData = true;
        }
        
        // Enhanced data tables detection
        const tables = document.querySelectorAll('table');
        window.websiteAnalysis.hasDataTables = tables.length > 2;
        
        // CAPTCHA detection with multiple providers
        const captchaSelectors = [
            '.g-recaptcha', '[data-sitekey]', 'iframe[src*="recaptcha"]', 
            '.h-captcha', '.cf-turnstile', '[data-hcaptcha-sitekey]'
        ];
        window.websiteAnalysis.hasCaptcha = captchaSelectors.some(sel => 
            document.querySelector(sel) !== null
        );
        
        // Anti-bot measures detection
        if (document.querySelector('[data-cf-beacon]') || document.querySelector('script[src*="cloudflare"]')) {
            window.websiteAnalysis.antiBot.push('Cloudflare');
        }
        if (document.querySelector('script[src*="distil"]') || document.querySelector('[data-distil]')) {
            window.websiteAnalysis.antiBot.push('Distil Networks');
        }
        if (document.querySelector('script[src*="imperva"]') || document.querySelector('[data-imperva]')) {
            window.websiteAnalysis.antiBot.push('Imperva');
        }
        
        // Performance analysis
        if (window.performance && window.performance.timing) {
            const timing = window.performance.timing;
            window.websiteAnalysis.estimatedLoadTime = timing.loadEventEnd - timing.navigationStart;
        }
        
        window.websiteAnalysis.resourceCount = document.querySelectorAll('script, link, img').length;
        
        // Accessibility analysis
        const imagesWithAlt = document.querySelectorAll('img[alt]').length;
        window.websiteAnalysis.hasAltText = imagesWithAlt / Math.max(1, document.images.length);
        
        window.websiteAnalysis.hasAriaLabels = document.querySelectorAll('[aria-label], [aria-labelledby]').length;
        
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        window.websiteAnalysis.hasHeadingStructure = headings.length > 0;
        
        // SEO indicators
        window.websiteAnalysis.hasOpenGraph = document.querySelector('meta[property^="og:"]') !== null;
        window.websiteAnalysis.hasTwitterCards = document.querySelector('meta[name^="twitter:"]') !== null;
        
        // Security indicators
        const cspMeta = document.querySelector('meta[http-equiv="Content-Security-Policy"]');
        window.websiteAnalysis.hasCSP = cspMeta !== null;
        
        // Check for mixed content (basic check)
        const httpResources = document.querySelectorAll('img[src^="http:"], script[src^="http:"], link[href^="http:"]');
        window.websiteAnalysis.mixedContent = httpResources.length > 0 && window.location.protocol === 'https:';
        
        // Infinite scroll detection (enhanced)
        const initialHeight = document.documentElement.scrollHeight;
        window.scrollTo(0, document.body.scrollHeight);
        setTimeout(() => {
            if (document.documentElement.scrollHeight > initialHeight + 100) {
                window.websiteAnalysis.hasInfiniteScroll = true;
            }
            
            // Check for common infinite scroll libraries
            if (window.InfiniteScroll || document.querySelector('[data-infinite-scroll]')) {
                window.websiteAnalysis.hasInfiniteScroll = true;
            }
        }, 2000);
        """
    
    async def _extract_enhanced_technical_data(self, crawl_result) -> Dict[str, Any]:
        """Extract enhanced technical analysis from crawl result"""
        
        try:
            html_content = crawl_result.html.lower()
            
            return {
                "hasJavaScript": any(framework in html_content for framework in 
                                   ['react', 'vue', 'angular', 'jquery', 'javascript']),
                "frameworks": self._detect_frameworks_enhanced(html_content),
                "formsCount": html_content.count('<form'),
                "hasInfiniteScroll": any(indicator in html_content for indicator in 
                                       ['infinite', 'lazy', 'pagination', 'load-more']),
                "hasCaptcha": any(captcha in html_content for captcha in 
                                ['recaptcha', 'captcha', 'hcaptcha', 'turnstile']),
                "antiBot": self._detect_anti_bot_enhanced(html_content),
                "structuredData": any(schema in html_content for schema in 
                                    ['application/ld+json', 'microdata', 'schema.org']),
                "metaTagsCount": html_content.count('<meta'),
                "imageCount": html_content.count('<img'),
                "linkCount": html_content.count('<a '),
                "hasOpenGraph": 'property="og:' in html_content,
                "hasTwitterCards": 'name="twitter:' in html_content,
                "resourceCount": (html_content.count('<script') + 
                                html_content.count('<link') + 
                                html_content.count('<img')),
                "estimatedComplexity": self._estimate_complexity_from_html(html_content)
            }
            
        except Exception as e:
            logger.warning(f"Enhanced technical analysis failed: {e}")
            return {}
    
    def _detect_frameworks_enhanced(self, html_content: str) -> List[str]:
        """Enhanced framework detection with more patterns"""
        
        frameworks = []
        framework_patterns = {
            'React': ['react', 'data-reactroot', 'data-react-checksum', '__REACT_DEVTOOLS'],
            'Vue': ['vue', 'data-v-', '__VUE__', 'v-if', 'v-for'],
            'Angular': ['angular', 'ng-app', 'ng-controller', 'ng-', '[ng-'],
            'jQuery': ['jquery', '$(', 'data-toggle'],
            'Svelte': ['svelte', '_svelte'],
            'Turbo': ['turbo', 'data-turbo', 'turbolinks'],
            'Alpine.js': ['alpine', 'x-data', 'x-show'],
            'HTMX': ['htmx', 'hx-'],
            'Stimulus': ['stimulus', 'data-controller']
        }
        
        for framework, patterns in framework_patterns.items():
            if any(pattern in html_content for pattern in patterns):
                frameworks.append(framework)
        
        return frameworks
    
    def _detect_anti_bot_enhanced(self, html_content: str) -> List[str]:
        """Enhanced anti-bot detection"""
        
        measures = []
        detection_patterns = {
            'Cloudflare': ['cloudflare', 'cf-beacon', 'cf-ray'],
            'Distil Networks': ['distil', 'distilnetworks'],
            'Imperva': ['imperva', 'incapsula'],
            'Bot Protection': ['bot', 'protection', 'antibot'],
            'Rate Limiting': ['rate limit', 'throttle', 'rate-limit'],
            'Fingerprinting': ['fingerprint', 'canvas', 'webgl'],
            'Challenge': ['challenge', 'verify', 'human']
        }
        
        for measure, patterns in detection_patterns.items():
            if any(pattern in html_content for pattern in patterns):
                measures.append(measure)
        
        return measures
    
    def _estimate_complexity_from_html(self, html_content: str) -> str:
        """Estimate website complexity from HTML analysis"""
        
        complexity_score = 0
        
        # JavaScript frameworks add complexity
        if any(fw in html_content for fw in ['react', 'vue', 'angular']):
            complexity_score += 3
        
        # Many scripts indicate complexity
        script_count = html_content.count('<script')
        if script_count > 20:
            complexity_score += 2
        elif script_count > 10:
            complexity_score += 1
        
        # Forms and interactive elements
        if html_content.count('<form') > 5:
            complexity_score += 2
        
        # Dynamic content indicators
        if any(indicator in html_content for indicator in ['ajax', 'xhr', 'fetch', 'websocket']):
            complexity_score += 2
        
        # Anti-bot measures
        if any(anti in html_content for anti in ['captcha', 'cloudflare', 'bot']):
            complexity_score += 1
        
        if complexity_score >= 6:
            return "high"
        elif complexity_score >= 3:
            return "medium"
        else:
            return "low"
    
    async def _ai_analyze_content_comprehensive(self, url: str, html_sample: str, 
                                              metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive AI-powered content analysis"""
        
        if not self.llm_service:
            return self._fallback_content_analysis()
        
        prompt = f"""
Analyze this website comprehensively for optimal web scraping and data extraction:

URL: {url}
Title: {metadata.get('title', 'Unknown')}
Description: {metadata.get('description', 'None')}
HTML Content Sample: {html_sample}

Provide detailed analysis for:

1. **Website Classification**: Classify as one of: directory_listing, e_commerce, social_media, news_article, corporate, form_heavy, spa_dynamic, data_table, unknown

2. **Content Structure**: Identify the main content patterns, data organization, and information hierarchy

3. **Extraction Complexity**: Rate as low/medium/high based on:
   - Dynamic content loading
   - JavaScript dependency
   - Data structure complexity
   - Anti-bot measures
   - Authentication requirements

4. **Data Quality Assessment**: Evaluate the structured nature and completeness of content

5. **Extraction Recommendations**: Suggest optimal approaches for data extraction

6. **Potential Challenges**: Identify specific obstacles for automated extraction

Respond in valid JSON format with confidence scores:
"""
        
        schema = {
            "type": "object",
            "properties": {
                "website_type": {"type": "string"},
                "complexity": {"type": "string", "enum": ["low", "medium", "high"]},
                "content_patterns": {"type": "array", "items": {"type": "string"}},
                "extraction_challenges": {"type": "array", "items": {"type": "string"}},
                "data_structure": {"type": "string"},
                "recommended_approach": {"type": "string"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "data_quality_score": {"type": "number", "minimum": 0, "maximum": 1},
                "content_completeness": {"type": "number", "minimum": 0, "maximum": 1},
                "extraction_difficulty": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["website_type", "complexity", "content_patterns", "confidence"]
        }
        
        try:
            return await self.llm_service.generate_structured(
                prompt=prompt,
                schema=schema
            )
        except Exception as e:
            logger.warning(f"AI content analysis failed: {e}")
            return self._fallback_content_analysis()
    
    def _assess_data_quality(self, crawl_result, tech_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Assess data quality indicators"""
        
        quality_metrics = {}
        
        # Content completeness
        html_length = len(crawl_result.cleaned_html) if crawl_result.cleaned_html else 0
        quality_metrics["content_length_score"] = min(1.0, html_length / 10000)  # Normalized to 10KB
        
        # Structured data presence
        quality_metrics["structured_data_score"] = 1.0 if tech_analysis.get("structuredData") else 0.0
        
        # Meta information completeness
        meta_score = 0.0
        if crawl_result.metadata.get("title"):
            meta_score += 0.4
        if crawl_result.metadata.get("description"):
            meta_score += 0.3
        if tech_analysis.get("hasOpenGraph"):
            meta_score += 0.3
        quality_metrics["meta_completeness_score"] = meta_score
        
        # Link quality (internal vs external balance)
        link_count = tech_analysis.get("linkCount", 0)
        quality_metrics["link_density_score"] = min(1.0, link_count / 50) if link_count > 0 else 0.0
        
        # Form accessibility
        form_count = tech_analysis.get("formsCount", 0)
        quality_metrics["interactivity_score"] = min(1.0, form_count / 5) if form_count > 0 else 0.5
        
        return quality_metrics
    
    def _analyze_security_features(self, html_content: str) -> List[str]:
        """Analyze security features present on the website"""
        
        security_features = []
        html_lower = html_content.lower()
        
        # HTTPS usage (would be better to check the actual protocol)
        if 'https://' in html_lower:
            security_features.append('HTTPS Links')
        
        # Content Security Policy
        if 'content-security-policy' in html_lower:
            security_features.append('CSP')
        
        # HSTS
        if 'strict-transport-security' in html_lower:
            security_features.append('HSTS')
        
        # X-Frame-Options
        if 'x-frame-options' in html_lower:
            security_features.append('X-Frame-Options')
        
        # SRI (Subresource Integrity)
        if 'integrity=' in html_lower:
            security_features.append('SRI')
        
        # Form CSRF protection
        if any(csrf in html_lower for csrf in ['csrf', '_token', 'authenticity_token']):
            security_features.append('CSRF Protection')
        
        return security_features
    
    def _calculate_accessibility_score(self, html_content: str) -> float:
        """Calculate basic accessibility score"""
        
        score = 0.0
        html_lower = html_content.lower()
        
        # Alt text on images
        img_count = html_lower.count('<img')
        img_with_alt = html_lower.count('alt=')
        if img_count > 0:
            score += (img_with_alt / img_count) * 0.3
        else:
            score += 0.3  # No images is fine
        
        # ARIA labels
        aria_count = html_lower.count('aria-')
        if aria_count > 0:
            score += min(0.2, aria_count / 20)  # Up to 0.2 for ARIA usage
        
        # Semantic HTML
        semantic_tags = ['header', 'nav', 'main', 'article', 'section', 'aside', 'footer']
        semantic_score = sum(1 for tag in semantic_tags if f'<{tag}' in html_lower)
        score += min(0.3, semantic_score / len(semantic_tags) * 0.3)
        
        # Headings structure
        headings = ['<h1', '<h2', '<h3', '<h4', '<h5', '<h6']
        heading_score = sum(1 for heading in headings if heading in html_lower)
        if heading_score > 0:
            score += 0.2
        
        return min(1.0, score)
    
    async def _find_similar_analyzed_sites(self, ai_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find similar previously analyzed websites"""
        
        if not self.vector_service:
            return []
        
        try:
            website_type = ai_analysis.get("website_type", "unknown")
            content_patterns = ai_analysis.get("content_patterns", [])
            
            query_text = f"Website type: {website_type}, patterns: {', '.join(content_patterns)}"
            
            similar_sites = await self.vector_service.find_similar_websites(
                target_url="",  # We're not comparing to a specific URL
                analysis=ai_analysis,
                limit=3
            )
            
            return [site.metadata for site in similar_sites]
            
        except Exception as e:
            logger.warning(f"Failed to find similar analyzed sites: {e}")
            return []
    
    async def _store_analysis_for_learning(self, analysis: WebsiteAnalysis, 
                                         ai_analysis: Dict[str, Any]):
        """Store analysis results for future learning"""
        
        if not self.vector_service:
            return
        
        try:
            analysis_data = {
                "website_type": analysis.website_type.value,
                "complexity": analysis.estimated_complexity,
                "frameworks": analysis.detected_frameworks,
                "content_patterns": analysis.content_patterns,
                "anti_bot_measures": analysis.anti_bot_measures,
                "data_quality_indicators": analysis.data_quality_indicators,
                "confidence": analysis.analysis_confidence,
                "structure_analysis": ai_analysis.get("data_structure", ""),
                "technologies": analysis.detected_frameworks + analysis.anti_bot_measures
            }
            
            await self.vector_service.store_website_analysis(analysis.url, analysis_data)
            
        except Exception as e:
            logger.warning(f"Failed to store analysis for learning: {e}")
    
    def _detect_auth_required(self, html: str) -> bool:
        """Enhanced authentication detection"""
        
        auth_indicators = [
            "login", "sign in", "log in", "authentication required",
            "please log in", "access denied", "unauthorized",
            "signin", "log-in", "member", "account", "password"
        ]
        
        html_lower = html.lower()
        
        # Check for auth indicators in text
        text_based_auth = any(indicator in html_lower for indicator in auth_indicators)
        
        # Check for login forms
        form_based_auth = (
            'type="password"' in html_lower or
            'name="password"' in html_lower or
            'id="password"' in html_lower
        )
        
        return text_based_auth or form_based_auth
    
    def _create_fallback_analysis(self, url: str, error: str = None) -> WebsiteAnalysis:
        """Create fallback analysis when main analysis fails"""
        
        return WebsiteAnalysis(
            url=url,
            website_type=WebsiteType.UNKNOWN,
            has_javascript=True,
            has_infinite_scroll=False,
            has_forms=False,
            has_auth_required=False,
            has_captcha=False,
            content_dynamically_loaded=True,
            estimated_complexity="medium",
            detected_frameworks=[],
            anti_bot_measures=[],
            content_patterns=["unknown"],
            data_quality_indicators={"error": 1.0},
            performance_metrics={"analysis_time": 0, "error": error or "Analysis failed"},
            accessibility_score=0.0,
            seo_indicators={},
            security_features=[],
            analysis_confidence=0.0,
            analysis_timestamp=time.time()
        )
    
    def _fallback_content_analysis(self) -> Dict[str, Any]:
        """Fallback content analysis when AI analysis fails"""
        
        return {
            "website_type": "unknown",
            "complexity": "medium",
            "content_patterns": ["unknown"],
            "extraction_challenges": ["ai_analysis_failed"],
            "confidence": 0.1,
            "data_quality_score": 0.5,
            "content_completeness": 0.5,
            "extraction_difficulty": 0.8
        }
    
    async def get_analysis_stats(self) -> Dict[str, Any]:
        """Get analyzer performance statistics"""
        
        return {
            "cache_size": len(self.analysis_cache),
            "cache_ttl": self.cache_ttl,
            "services_initialized": {
                "llm_service": self.llm_service is not None,
                "vector_service": self.vector_service is not None
            },
            "supported_website_types": [wt.value for wt in WebsiteType],
            "supported_purposes": [ep.value for ep in ExtractionPurpose]
        }
    
    async def cleanup(self):
        """Clean up resources"""
        
        self.analysis_cache.clear()
        
        if self.llm_service:
            await self.llm_service.cleanup()
        
        if self.vector_service:
            await self.vector_service.cleanup()
        
        logger.info("Intelligent analyzer cleanup completed")
