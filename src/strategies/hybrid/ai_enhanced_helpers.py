#!/usr/bin/env python3
"""
AI Enhanced Strategy Helper Methods
Supporting methods for AI-enhanced extraction strategy
"""

import asyncio
import time
import logging
import json
from typing import Dict, Any, List, Optional, Tuple
from bs4 import BeautifulSoup
import re

logger = logging.getLogger("ai_enhanced_helpers")

class AIEnhancedHelpers:
    """Helper methods for AI-enhanced strategy"""
    
    @staticmethod
    async def ai_infer_data_schema(llm_service, content_analysis: Dict[str, Any], 
                                  purpose: str, config, schema_cache: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to infer expected data schema"""
        
        if not config.enable_schema_inference:
            return {}
        
        cache_key = f"schema_{purpose}_{hash(str(content_analysis))}"
        if config.enable_caching and cache_key in schema_cache:
            return schema_cache[cache_key]
        
        try:
            schema_prompt = f"""
Infer the optimal data schema for extracting information with purpose: {purpose}

Content Analysis:
{json.dumps(content_analysis, indent=2)}

Generate a JSON schema that defines:
1. Expected fields and their types
2. Required vs optional fields
3. Data format specifications
4. Validation constraints

Focus on practical extraction needs for the stated purpose.
"""
            
            schema_definition = {
                "type": "object",
                "properties": {
                    "fields": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "required": {"type": "boolean"},
                                "description": {"type": "string"},
                                "format": {"type": "string"},
                                "validation": {"type": "string"}
                            }
                        }
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["fields"]
            }
            
            schema_result = await llm_service.generate_structured(
                prompt=schema_prompt,
                schema=schema_definition
            )
            
            # Cache the result
            if config.enable_caching:
                schema_cache[cache_key] = schema_result
            
            return schema_result
            
        except Exception as e:
            logger.warning(f"Schema inference failed: {e}")
            return {}
    
    @staticmethod
    async def ai_generate_css_selectors(llm_service, content_analysis: Dict[str, Any],
                                       purpose: str, config) -> Dict[str, List[str]]:
        """Generate optimized CSS selectors using AI"""
        
        if not config.enable_selector_optimization:
            return {}
        
        try:
            selector_prompt = f"""
Generate optimal CSS selectors for data extraction:

Purpose: {purpose}
Content Type: {content_analysis.get('content_type', 'unknown')}
Key Areas: {content_analysis.get('key_content_areas', [])}
Data Patterns: {content_analysis.get('data_patterns', [])}

Generate CSS selectors for common data types needed for this purpose.
Provide multiple selector options per field for robustness.
Focus on semantic selectors that are likely to be stable.
"""
            
            selector_schema = {
                "type": "object",
                "properties": {
                    "selectors": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["selectors"]
            }
            
            selector_result = await llm_service.generate_structured(
                prompt=selector_prompt,
                schema=selector_schema
            )
            
            return selector_result.get("selectors", {})
            
        except Exception as e:
            logger.warning(f"CSS selector generation failed: {e}")
            return {}
    
    @staticmethod
    async def ai_create_extraction_instructions(llm_service, content_analysis: Dict[str, Any],
                                               purpose: str, schema: Dict[str, Any]) -> Dict[str, str]:
        """Create AI-powered extraction instructions"""
        
        try:
            instruction_prompt = f"""
Create detailed extraction instructions for purpose: {purpose}

Content Analysis: {json.dumps(content_analysis, indent=2)}
Expected Schema: {json.dumps(schema, indent=2)}

Generate specific instructions for extracting each type of data.
Include text processing, normalization, and formatting requirements.
Focus on accuracy and consistency.
"""
            
            instruction_schema = {
                "type": "object",
                "properties": {
                    "instructions": {
                        "type": "object",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["instructions"]
            }
            
            result = await llm_service.generate_structured(
                prompt=instruction_prompt,
                schema=instruction_schema
            )
            
            return result.get("instructions", {})
            
        except Exception as e:
            logger.warning(f"Extraction instruction creation failed: {e}")
            return {}
