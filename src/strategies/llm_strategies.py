#!/usr/bin/env python3
"""
LLM-Based Extraction Strategies
AI-powered strategies for complex content understanding and extraction
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from .base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

class IntelligentLLMStrategy(BaseExtractionStrategy):
    """
    General-purpose intelligent extraction using LLM reasoning
    
    Examples:
    - Extract complex relationship data from corporate websites
    - Understand context-dependent information
    - Handle unstructured content intelligently
    """
    
    def __init__(self, ollama_client, **kwargs):
        super().__init__(strategy_type=StrategyType.LLM, **kwargs)
        self.ollama_client = ollama_client
        
        # Define extraction schemas for different purposes
        self.purpose_schemas = {
            "company_info": {
                "type": "object",
                "properties": {
                    "company_name": {"type": "string"},
                    "industry": {"type": "string"},
                    "description": {"type": "string"},
                    "founded": {"type": "string"},
                    "headquarters": {"type": "string"},
                    "employees": {"type": "string"},
                    "website": {"type": "string"},
                    "contact_email": {"type": "string"},
                    "phone": {"type": "string"},
                    "leadership": {"type": "array", "items": {"type": "string"}},
                    "services": {"type": "array", "items": {"type": "string"}},
                    "achievements": {"type": "array", "items": {"type": "string"}}
                }
            },
            "contact_discovery": {
                "type": "object", 
                "properties": {
                    "emails": {"type": "array", "items": {"type": "string"}},
                    "phones": {"type": "array", "items": {"type": "string"}},
                    "addresses": {"type": "array", "items": {"type": "string"}},
                    "social_media": {"type": "array", "items": {"type": "string"}},
                    "contact_persons": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "email": {"type": "string"},
                            "phone": {"type": "string"}
                        }
                    }},
                    "office_locations": {"type": "array", "items": {"type": "string"}},
                    "support_channels": {"type": "array", "items": {"type": "string"}}
                }
            },
            "profile_info": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "title": {"type": "string"},
                    "company": {"type": "string"},
                    "location": {"type": "string"},
                    "bio": {"type": "string"},
                    "experience": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "company": {"type": "string"},
                            "role": {"type": "string"},
                            "duration": {"type": "string"}
                        }
                    }},
                    "education": {"type": "array", "items": {"type": "string"}},
                    "skills": {"type": "array", "items": {"type": "string"}},
                    "connections": {"type": "string"},
                    "contact_info": {"type": "object"}
                }
            },
            "news_content": {
                "type": "object",
                "properties": {
                    "headline": {"type": "string"},
                    "subheadline": {"type": "string"},
                    "author": {"type": "string"},
                    "publish_date": {"type": "string"},
                    "content": {"type": "string"},
                    "summary": {"type": "string"},
                    "key_points": {"type": "array", "items": {"type": "string"}},
                    "quotes": {"type": "array", "items": {"type": "string"}},
                    "sources": {"type": "array", "items": {"type": "string"}},
                    "category": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                }
            }
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Clean and prepare content for LLM
            cleaned_content = self._prepare_content_for_llm(html_content)
            
            # Get appropriate schema for purpose
            schema = self.purpose_schemas.get(purpose, self._get_generic_schema())
            
            # Create extraction prompt
            prompt = self._create_extraction_prompt(url, cleaned_content, purpose, schema, context)
            
            # Execute LLM extraction
            extracted_data = await self._llm_extract(prompt, schema)
            
            # Validate and clean results
            if extracted_data:
                extracted_data = self._post_process_extraction(extracted_data, purpose)
                confidence = self._calculate_llm_confidence(extracted_data, schema)
            else:
                confidence = 0.1
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extracted_data),
                extracted_data=extracted_data,
                confidence_score=confidence,
                strategy_used="IntelligentLLMStrategy",
                execution_time=execution_time,
                metadata={
                    "content_length": len(cleaned_content),
                    "schema_used": purpose,
                    "llm_model": "llama3.1"
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="IntelligentLLMStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    def _prepare_content_for_llm(self, html_content: str) -> str:
        """Clean and prepare HTML content for LLM processing"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Get text content with basic structure preserved
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        cleaned = '\n'.join(lines)
        
        # Limit content length for LLM processing (8000 chars for context)
        if len(cleaned) > 8000:
            # Try to keep important sections
            sections = cleaned.split('\n\n')
            important_content = []
            current_length = 0
            
            for section in sections:
                if current_length + len(section) < 7500:
                    important_content.append(section)
                    current_length += len(section)
                else:
                    break
            
            cleaned = '\n\n'.join(important_content)
            cleaned += "\n\n[Content truncated for processing...]"
        
        return cleaned
    
    def _create_extraction_prompt(self, url: str, content: str, purpose: str, 
                                schema: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """Create detailed extraction prompt for LLM"""
        
        context_info = ""
        if context:
            context_info = f"\nAdditional Context: {json.dumps(context, indent=2)}"
        
        prompt = f"""
You are an expert data extraction specialist. Extract comprehensive information from this webpage content.

URL: {url}
Purpose: {purpose}
{context_info}

EXTRACTION INSTRUCTIONS:
1. Analyze the content carefully and extract ALL relevant information for the purpose: {purpose}
2. Be thorough and accurate - don't make up information that isn't present
3. Follow the exact schema structure provided
4. For arrays, include all relevant items found
5. For contact information, be precise with formatting
6. Maintain original context and meaning

WEBPAGE CONTENT:
{content}

REQUIRED OUTPUT SCHEMA:
{json.dumps(schema, indent=2)}

IMPORTANT GUIDELINES:
- Extract only factual information present in the content
- Use proper formatting for emails, phones, URLs
- For dates, use consistent format (YYYY-MM-DD when possible)
- For arrays, include all relevant items, not just the first one
- For company/person names, use the full official name
- For descriptions, capture the essence while keeping it concise

Return ONLY valid JSON following the schema exactly. No explanations or additional text.
"""
        
        return prompt
    
    async def _llm_extract(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Execute LLM extraction with error handling and retries"""
        
        for attempt in range(self.max_retries):
            try:
                response = await self.ollama_client.generate(
                    model="llama3.1",
                    prompt=prompt,
                    format="json",
                    temperature=0.3,  # Lower temperature for more consistent extraction
                    max_tokens=2048
                )
                
                # Parse JSON response
                extracted_data = json.loads(response)
                
                # Validate against schema (basic validation)
                if self._validate_extraction_schema(extracted_data, schema):
                    return extracted_data
                else:
                    self.logger.warning(f"Schema validation failed on attempt {attempt + 1}")
                    
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
                
            except Exception as e:
                self.logger.warning(f"LLM extraction error on attempt {attempt + 1}: {e}")
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(1)
        
        return {}
    
    def _validate_extraction_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Basic schema validation for extracted data"""
        if not isinstance(data, dict):
            return False
        
        properties = schema.get("properties", {})
        
        # Check if we have at least some expected properties with valid data
        valid_properties = 0
        
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                value = data[prop_name]
                prop_type = prop_schema.get("type")
                
                if prop_type == "string" and isinstance(value, str) and value.strip():
                    valid_properties += 1
                elif prop_type == "array" and isinstance(value, list) and value:
                    valid_properties += 1
                elif prop_type == "object" and isinstance(value, dict) and value:
                    valid_properties += 1
        
        # Consider valid if we have at least 2 valid properties
        return valid_properties >= 2
    
    def _post_process_extraction(self, data: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Post-process extracted data for quality and consistency"""
        
        processed = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Clean up string values
                cleaned = value.strip()
                if cleaned and cleaned.lower() not in ['null', 'none', 'n/a', 'unknown']:
                    processed[key] = cleaned
            
            elif isinstance(value, list):
                # Clean up list values
                cleaned_list = []
                for item in value:
                    if isinstance(item, str):
                        cleaned_item = item.strip()
                        if cleaned_item and cleaned_item.lower() not in ['null', 'none', 'n/a']:
                            cleaned_list.append(cleaned_item)
                    elif isinstance(item, dict):
                        # Recursively clean objects in arrays
                        cleaned_obj = self._post_process_extraction(item, purpose)
                        if cleaned_obj:
                            cleaned_list.append(cleaned_obj)
                
                if cleaned_list:
                    processed[key] = cleaned_list
            
            elif isinstance(value, dict):
                # Recursively process nested objects
                cleaned_obj = self._post_process_extraction(value, purpose)
                if cleaned_obj:
                    processed[key] = cleaned_obj
        
        return processed
    
    def _calculate_llm_confidence(self, data: Dict[str, Any], schema: Dict[str, Any]) -> float:
        """Calculate confidence score based on extraction completeness and quality"""
        
        if not data:
            return 0.0
        
        properties = schema.get("properties", {})
        if not properties:
            return 0.5
        
        # Calculate completeness score
        filled_properties = 0
        quality_score = 0.0
        
        for prop_name, prop_schema in properties.items():
            if prop_name in data:
                value = data[prop_name]
                prop_type = prop_schema.get("type")
                
                filled_properties += 1
                
                # Quality assessment
                if prop_type == "string":
                    if isinstance(value, str) and len(value) > 3:
                        quality_score += 1.0
                    else:
                        quality_score += 0.3
                
                elif prop_type == "array":
                    if isinstance(value, list):
                        if len(value) > 0:
                            quality_score += min(len(value) * 0.2, 1.0)
                        else:
                            quality_score += 0.1
                
                elif prop_type == "object":
                    if isinstance(value, dict) and value:
                        quality_score += min(len(value) * 0.1, 1.0)
        
        # Combine completeness and quality
        completeness = filled_properties / len(properties)
        avg_quality = quality_score / len(properties) if properties else 0
        
        # LLM strategies get bonus for understanding context
        confidence = (completeness * 0.6 + avg_quality * 0.4) + 0.1
        
        return min(confidence, 1.0)
    
    def _get_generic_schema(self) -> Dict[str, Any]:
        """Generic schema for unknown purposes"""
        return {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "main_content": {"type": "string"},
                "key_information": {"type": "array", "items": {"type": "string"}},
                "contact_info": {"type": "object"},
                "metadata": {"type": "object"}
            }
        }
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Estimate confidence for LLM extraction"""
        
        # LLM strategies are versatile but slower
        base_confidence = 0.7
        
        # Check content complexity (LLM handles complex content better)
        content_length = len(html_content)
        if content_length > 10000:
            base_confidence += 0.1
        
        # Check for structured data (LLM can understand context better)
        if 'json' in html_content.lower() or 'schema' in html_content.lower():
            base_confidence += 0.05
        
        # Purpose-specific adjustments
        if purpose in self.purpose_schemas:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """LLM strategy supports most purposes"""
        return True  # LLM is versatile and can handle most extraction purposes

class ContextAwareLLMStrategy(IntelligentLLMStrategy):
    """
    Advanced LLM strategy that uses context and learning for better extraction
    
    Examples:
    - Learn from previous extractions to improve accuracy
    - Use domain knowledge for industry-specific extraction
    - Adapt to website patterns over time
    """
    
    def __init__(self, ollama_client, chromadb_manager=None, **kwargs):
        super().__init__(ollama_client, **kwargs)
        self.chromadb_manager = chromadb_manager
        self.context_memory = {}
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        # Get domain-specific context
        domain_context = await self._get_domain_context(url, purpose)
        
        # Combine with provided context
        enhanced_context = context or {}
        if domain_context:
            enhanced_context.update(domain_context)
        
        # Use parent method with enhanced context
        result = await super().extract(url, html_content, purpose, enhanced_context)
        
        # Learn from successful extractions
        if result.success and self.chromadb_manager:
            await self._store_learning_context(url, purpose, result.extracted_data, enhanced_context)
        
        return result
    
    async def _get_domain_context(self, url: str, purpose: str) -> Dict[str, Any]:
        """Get domain-specific context from previous extractions"""
        
        if not self.chromadb_manager:
            return {}
        
        try:
            # Extract domain from URL
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            # Query similar extractions from same domain
            similar_extractions = await self.chromadb_manager.query_similar_strategies(
                query_text=f"{domain} {purpose}",
                website_type="unknown",
                purpose=purpose,
                limit=3
            )
            
            if similar_extractions:
                # Extract patterns from successful extractions
                patterns = self._extract_patterns_from_history(similar_extractions)
                return {"domain_patterns": patterns, "domain": domain}
            
        except Exception as e:
            self.logger.warning(f"Failed to get domain context: {e}")
        
        return {}
    
    def _extract_patterns_from_history(self, extractions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract common patterns from historical extractions"""
        
        patterns = {
            "common_fields": [],
            "field_patterns": {},
            "success_indicators": []
        }
        
        # Analyze successful extractions for patterns
        for extraction in extractions:
            if extraction.get("success_rate", 0) > 0.8:
                # Track common fields
                config = extraction.get("extraction_config", {})
                if isinstance(config, dict):
                    patterns["common_fields"].extend(config.keys())
        
        # Remove duplicates and get most common
        if patterns["common_fields"]:
            from collections import Counter
            field_counts = Counter(patterns["common_fields"])
            patterns["common_fields"] = [field for field, count in field_counts.most_common(10)]
        
        return patterns
    
    async def _store_learning_context(self, url: str, purpose: str, extracted_data: Dict[str, Any], context: Dict[str, Any]):
        """Store successful extraction context for future learning"""
        
        learning_data = {
            "url": url,
            "purpose": purpose,
            "extracted_fields": list(extracted_data.keys()),
            "context_used": context,
            "timestamp": time.time(),
            "strategy": "ContextAwareLLMStrategy"
        }
        
        try:
            await self.chromadb_manager.store_strategy_learning(learning_data)
        except Exception as e:
            self.logger.warning(f"Failed to store learning context: {e}")

class AdaptiveLLMStrategy(ContextAwareLLMStrategy):
    """
    Self-adapting LLM strategy that improves extraction prompts based on results
    
    Examples:
    - Automatically adjust extraction prompts based on success rates
    - Learn optimal prompt patterns for different website types
    - Adapt to new content patterns dynamically
    """
    
    def __init__(self, ollama_client, chromadb_manager=None, **kwargs):
        super().__init__(ollama_client, chromadb_manager, **kwargs)
        self.prompt_variations = {}
        self.success_metrics = {}
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        # Get adaptive prompt based on historical performance
        adaptive_prompt_elements = await self._get_adaptive_prompt_elements(url, purpose)
        
        # Enhanced context with adaptive elements
        enhanced_context = context or {}
        enhanced_context.update(adaptive_prompt_elements)
        
        result = await super().extract(url, html_content, purpose, enhanced_context)
        
        # Track performance for adaptation
        await self._track_performance(url, purpose, result, adaptive_prompt_elements)
        
        return result
    
    async def _get_adaptive_prompt_elements(self, url: str, purpose: str) -> Dict[str, Any]:
        """Get adaptive prompt elements based on historical performance"""
        
        # Check if we have learned prompt patterns for this purpose
        prompt_key = f"{purpose}_{self._get_url_pattern(url)}"
        
        if prompt_key in self.prompt_variations:
            return self.prompt_variations[prompt_key]
        
        # Default adaptive elements
        return {
            "extraction_hints": self._get_purpose_specific_hints(purpose),
            "quality_indicators": self._get_quality_indicators(purpose)
        }
    
    def _get_purpose_specific_hints(self, purpose: str) -> List[str]:
        """Get specific hints for different extraction purposes"""
        
        hints_map = {
            "company_info": [
                "Look for 'About Us' or 'Company' sections",
                "Check footer for contact information",
                "Look for leadership team or executive information",
                "Find mission/vision statements"
            ],
            "contact_discovery": [
                "Scan entire page for email addresses",
                "Look for 'Contact', 'Support', or 'Help' sections",
                "Check social media links",
                "Find physical addresses and phone numbers"
            ],
            "product_data": [
                "Look for pricing information",
                "Find product specifications or features",
                "Check for customer reviews or ratings",
                "Look for product images and descriptions"
            ],
            "news_content": [
                "Identify headline and subheadings",
                "Find author and publication date",
                "Extract main article content",
                "Look for quotes and key statistics"
            ]
        }
        
        return hints_map.get(purpose, ["Extract all relevant information carefully"])
    
    def _get_quality_indicators(self, purpose: str) -> List[str]:
        """Get quality indicators for different purposes"""
        
        indicators_map = {
            "company_info": ["company_name", "description", "contact_email"],
            "contact_discovery": ["emails", "phones", "addresses"],
            "product_data": ["name", "price", "description"],
            "news_content": ["headline", "content", "author"]
        }
        
        return indicators_map.get(purpose, ["main_content"])
    
    def _get_url_pattern(self, url: str) -> str:
        """Extract URL pattern for categorization"""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Common pattern recognition
        if 'about' in parsed.path:
            return "about_page"
        elif 'contact' in parsed.path:
            return "contact_page"
        elif 'product' in parsed.path:
            return "product_page"
        elif 'news' in parsed.path or 'blog' in parsed.path:
            return "content_page"
        else:
            return "general_page"
    
    async def _track_performance(self, url: str, purpose: str, result: StrategyResult, prompt_elements: Dict[str, Any]):
        """Track performance for continuous adaptation"""
        
        prompt_key = f"{purpose}_{self._get_url_pattern(url)}"
        
        if prompt_key not in self.success_metrics:
            self.success_metrics[prompt_key] = {
                "attempts": 0,
                "successes": 0,
                "avg_confidence": 0.0,
                "best_elements": prompt_elements
            }
        
        metrics = self.success_metrics[prompt_key]
        metrics["attempts"] += 1
        
        if result.success:
            metrics["successes"] += 1
            
            # Update average confidence
            metrics["avg_confidence"] = (
                (metrics["avg_confidence"] * (metrics["attempts"] - 1) + result.confidence_score) /
                metrics["attempts"]
            )
            
            # Update best elements if this was better
            if result.confidence_score > metrics["avg_confidence"]:
                metrics["best_elements"] = prompt_elements
                self.prompt_variations[prompt_key] = prompt_elements

class MultiPassLLMStrategy(AdaptiveLLMStrategy):
    """
    Multi-pass LLM strategy that extracts in multiple phases for maximum accuracy
    
    Examples:
    - First pass: identify content structure and key sections
    - Second pass: extract detailed information from identified sections
    - Third pass: validate and enrich extracted data
    """
    
    def __init__(self, ollama_client, chromadb_manager=None, **kwargs):
        super().__init__(ollama_client, chromadb_manager, **kwargs)
        self.pass_count = 3
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Pass 1: Structure Analysis
            structure_data = await self._pass_1_structure_analysis(url, html_content, purpose)
            
            # Pass 2: Detailed Extraction
            detailed_data = await self._pass_2_detailed_extraction(
                url, html_content, purpose, structure_data, context
            )
            
            # Pass 3: Validation and Enrichment
            final_data = await self._pass_3_validation_enrichment(
                url, html_content, purpose, detailed_data
            )
            
            # Calculate overall confidence
            confidence = self._calculate_multipass_confidence(structure_data, detailed_data, final_data)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(final_data),
                extracted_data=final_data,
                confidence_score=confidence,
                strategy_used="MultiPassLLMStrategy",
                execution_time=execution_time,
                metadata={
                    "passes_completed": 3,
                    "structure_quality": len(structure_data),
                    "detail_quality": len(detailed_data),
                    "final_quality": len(final_data)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="MultiPassLLMStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _pass_1_structure_analysis(self, url: str, html_content: str, purpose: str) -> Dict[str, Any]:
        """First pass: analyze content structure and identify key sections"""
        
        cleaned_content = self._prepare_content_for_llm(html_content)
        
        structure_prompt = f"""
Analyze this webpage content and identify the structure and key sections relevant to: {purpose}

URL: {url}
Purpose: {purpose}

CONTENT:
{cleaned_content[:4000]}  # Shorter content for structure analysis

Identify and return:
1. Main content sections and their purposes
2. Navigation and header information
3. Contact or business information areas
4. Special sections (forms, testimonials, features, etc.)
5. Overall page type and purpose

Return JSON with structure analysis:
{{
    "page_type": "corporate|product|news|directory|profile|other",
    "main_sections": ["section1", "section2", ...],
    "contact_areas": ["area1", "area2", ...],
    "key_content_indicators": ["indicator1", "indicator2", ...],
    "extraction_targets": ["target1", "target2", ...]
}}
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=structure_prompt,
                format="json",
                temperature=0.2
            )
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Structure analysis failed: {e}")
            return {}
    
    async def _pass_2_detailed_extraction(self, url: str, html_content: str, purpose: str, 
                                        structure_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Second pass: detailed extraction using structure insights"""
        
        cleaned_content = self._prepare_content_for_llm(html_content)
        
        # Use structure data to guide extraction
        extraction_targets = structure_data.get("extraction_targets", [])
        page_type = structure_data.get("page_type", "unknown")
        
        # Get appropriate schema
        schema = self.purpose_schemas.get(purpose, self._get_generic_schema())
        
        detailed_prompt = f"""
Based on the structure analysis, extract detailed information for: {purpose}

URL: {url}
Page Type: {page_type}
Extraction Targets: {extraction_targets}
Structure Context: {json.dumps(structure_data, indent=2)}

CONTENT:
{cleaned_content}

FOCUSED EXTRACTION INSTRUCTIONS:
1. Focus on the identified extraction targets: {extraction_targets}
2. Use the page type context ({page_type}) to guide extraction
3. Be thorough in extracting information from relevant sections
4. Maintain high accuracy and don't fabricate information

OUTPUT SCHEMA:
{json.dumps(schema, indent=2)}

Return detailed extracted data following the schema exactly.
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=detailed_prompt,
                format="json",
                temperature=0.3
            )
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Detailed extraction failed: {e}")
            return {}
    
    async def _pass_3_validation_enrichment(self, url: str, html_content: str, 
                                          purpose: str, detailed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Third pass: validate and enrich extracted data"""
        
        if not detailed_data:
            return {}
        
        validation_prompt = f"""
Validate and enrich this extracted data for quality and completeness.

URL: {url}
Purpose: {purpose}

EXTRACTED DATA:
{json.dumps(detailed_data, indent=2)}

VALIDATION AND ENRICHMENT TASKS:
1. Check data quality and consistency
2. Validate email formats, phone numbers, URLs
3. Ensure completeness for the extraction purpose
4. Remove any obviously incorrect or fabricated information
5. Enrich with additional context where appropriate
6. Standardize formats (dates, phones, addresses)

Return the validated and enriched data in the same structure, but with:
- Corrected formatting
- Validated contact information
- Removed invalid entries
- Added confidence indicators where appropriate

Only return data that you are confident is accurate.
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=validation_prompt,
                format="json",
                temperature=0.1  # Very low temperature for validation
            )
            
            validated_data = json.loads(response)
            
            # Additional validation using built-in methods
            return self._post_process_extraction(validated_data, purpose)
            
        except Exception as e:
            self.logger.warning(f"Validation pass failed: {e}")
            # Return original data if validation fails
            return self._post_process_extraction(detailed_data, purpose)
    
    def _calculate_multipass_confidence(self, structure_data: Dict[str, Any], 
                                      detailed_data: Dict[str, Any], 
                                      final_data: Dict[str, Any]) -> float:
        """Calculate confidence based on multi-pass results"""
        
        # Base confidence from final data
        base_confidence = 0.5
        
        # Structure analysis quality
        if structure_data:
            structure_score = min(len(structure_data) * 0.1, 0.2)
            base_confidence += structure_score
        
        # Detailed extraction quality
        if detailed_data:
            detail_score = min(len(detailed_data) * 0.05, 0.2)
            base_confidence += detail_score
        
        # Final data quality
        if final_data:
            final_score = min(len(final_data) * 0.05, 0.2)
            base_confidence += final_score
        
        # Multi-pass bonus (multiple passes increase reliability)
        base_confidence += 0.1
        
        return min(base_confidence, 1.0)
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Multi-pass strategy has higher confidence due to validation"""
        base_confidence = super().get_confidence_score(url, html_content, purpose)
        return min(base_confidence + 0.15, 1.0)  # Bonus for multi-pass validation
