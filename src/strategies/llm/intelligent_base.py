#!/usr/bin/env python3
"""
Intelligent LLM Strategy - Base Implementation
General-purpose intelligent extraction using LLM reasoning
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

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
        self.max_retries = kwargs.get('max_retries', 2)
        
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
