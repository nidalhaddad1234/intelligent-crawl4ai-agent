#!/usr/bin/env python3
"""
HybridAI Service Bridge
Adapts HybridAIService to work with existing LLMService interface
"""

import json
import logging
from typing import Dict, Any, List, Optional
from ai_core.core.hybrid_ai_service import HybridAIService, create_production_ai_service

logger = logging.getLogger("hybrid_ai_bridge")

class HybridAIBridge:
    """
    Bridge class that makes HybridAIService compatible with LLMService interface
    """
    
    def __init__(self, hybrid_service: HybridAIService = None):
        self.hybrid_service = hybrid_service or create_production_ai_service()
    
    async def initialize(self) -> bool:
        """Initialize the bridge service"""
        try:
            # Test connectivity
            health = await self.hybrid_service.health_check()
            healthy_providers = [p for p, status in health.items() if status['status'] == 'healthy']
            
            if healthy_providers:
                logger.info(f"HybridAI bridge initialized with {len(healthy_providers)} healthy providers")
                return True
            else:
                logger.error("No healthy AI providers available")
                return False
        except Exception as e:
            logger.error(f"Failed to initialize HybridAI bridge: {e}")
            return False
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any],
                                model: str = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate structured JSON output using HybridAI service
        Adapts the interface to match LLMService.generate_structured()
        """
        
        # Create a planning-style prompt that will generate the desired JSON
        planning_prompt = f"""
{prompt}

CRITICAL: Respond with ONLY valid JSON following this exact schema:
{json.dumps(schema, indent=2)}

Requirements:
- Response must be valid JSON
- All required fields must be present
- Follow the schema structure exactly
- Do not include any text outside the JSON response
"""
        
        try:
            # Use HybridAI's generate_plan method with a dummy tools manifest
            dummy_tools = {"tools": []}
            plan_result, confidence = await self.hybrid_service.generate_plan(
                planning_prompt, dummy_tools
            )
            
            # If the result looks like our requested schema, return it
            # Otherwise, try to extract the structured data from the plan
            if self._matches_schema(plan_result, schema):
                return plan_result
            
            # Try to extract JSON from the plan description or other fields
            for field in ['description', 'reasoning', 'result']:
                if field in plan_result:
                    try:
                        extracted = json.loads(plan_result[field])
                        if self._matches_schema(extracted, schema):
                            return extracted
                    except (json.JSONDecodeError, TypeError):
                        continue
            
            # Fallback: return the plan result as-is
            return plan_result
            
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            return {"error": "Generation failed", "details": str(e)}
    
    async def generate(self, prompt: str, model: str = None, 
                      format: str = None, system: str = None,
                      temperature: float = None, max_tokens: int = None) -> Dict[str, Any]:
        """
        Generate text using HybridAI service
        Returns a response object similar to LLMService.generate()
        """
        
        try:
            # Create dummy tools for the planning interface
            dummy_tools = {"tools": []}
            
            # Use HybridAI's generate_plan method
            result, confidence = await self.hybrid_service.generate_plan(prompt, dummy_tools)
            
            # Extract text content from the result
            content = ""
            if isinstance(result, dict):
                content = result.get('description', '') or str(result)
            else:
                content = str(result)
            
            return {
                "content": content,
                "model": "hybrid_ai",
                "success": True,
                "processing_time": 0.0,
                "confidence": confidence,
                "metadata": {"provider": "hybrid_ai"}
            }
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return {
                "content": "",
                "model": "hybrid_ai", 
                "success": False,
                "processing_time": 0.0,
                "error": str(e)
            }
    
    async def analyze_website_content(self, url: str, html_content: str, 
                                    purpose: str) -> Dict[str, Any]:
        """Analyze website content using HybridAI"""
        
        prompt = f"""
Analyze this website for optimal web scraping strategy:

URL: {url}
Purpose: {purpose}
HTML Content (first 2000 chars): {html_content[:2000]}

Provide analysis as JSON with these fields:
- website_type: string (e-commerce, directory, social, news, corporate, etc.)
- content_patterns: array of strings
- extraction_strategy: string
- recommended_selectors: object with primary and fallback arrays
- challenges: array of strings  
- confidence: number 0-1
- reasoning: string
- data_quality: string
- success_probability: number 0-1
"""
        
        schema = {
            "type": "object",
            "properties": {
                "website_type": {"type": "string"},
                "content_patterns": {"type": "array", "items": {"type": "string"}},
                "extraction_strategy": {"type": "string"}, 
                "recommended_selectors": {
                    "type": "object",
                    "properties": {
                        "primary": {"type": "array", "items": {"type": "string"}},
                        "fallback": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "challenges": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "reasoning": {"type": "string"},
                "data_quality": {"type": "string"},
                "success_probability": {"type": "number", "minimum": 0, "maximum": 1}
            },
            "required": ["website_type", "extraction_strategy", "confidence", "reasoning"]
        }
        
        return await self.generate_structured(prompt, schema)
    
    async def extract_data_with_ai(self, html_content: str, extraction_instruction: str,
                                 schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract specific data from HTML using AI"""
        
        if schema:
            prompt = f"""
Extract data from this HTML content according to the instruction and schema:

Instruction: {extraction_instruction}
Schema: {json.dumps(schema, indent=2)}
HTML Content: {html_content[:4000]}

Return extracted data following the schema exactly.
"""
            return await self.generate_structured(prompt, schema)
        else:
            prompt = f"""
Extract data from this HTML content:
Instruction: {extraction_instruction}
HTML Content: {html_content[:4000]}

Return the extracted data in JSON format.
"""
            result = await self.generate(prompt, format="json")
            if result["success"]:
                try:
                    return json.loads(result["content"])
                except json.JSONDecodeError:
                    return {"extracted_text": result["content"]}
            else:
                return {"error": result.get("error", "Extraction failed")}
    
    def _matches_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Check if data roughly matches the expected schema"""
        
        if not isinstance(data, dict):
            return False
        
        # Check if required fields are present
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                return False
        
        # Basic type checking for properties
        properties = schema.get("properties", {})
        for field, field_schema in properties.items():
            if field not in data:
                continue
            
            expected_type = field_schema.get("type")
            value = data[field]
            
            if expected_type == "string" and not isinstance(value, str):
                return False
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False
            elif expected_type == "array" and not isinstance(value, list):
                return False
            elif expected_type == "object" and not isinstance(value, dict):
                return False
        
        return True
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        
        try:
            provider_status = self.hybrid_service.get_provider_status()
            health_status = await self.hybrid_service.health_check()
            
            return {
                "bridge_type": "HybridAI",
                "provider_status": provider_status,
                "health_status": health_status,
                "total_providers": len(provider_status),
                "healthy_providers": len([p for p in health_status.values() if p.get('status') == 'healthy'])
            }
        except Exception as e:
            return {"error": f"Failed to get stats: {e}"}
    
    async def cleanup(self):
        """Clean up resources"""
        # HybridAIService doesn't need explicit cleanup
        pass


# Factory function to create the bridge
def create_hybrid_ai_bridge() -> HybridAIBridge:
    """Create a HybridAI bridge with production configuration"""
    return HybridAIBridge()
