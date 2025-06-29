#!/usr/bin/env python3
"""
Ollama Client
Handles communication with local Ollama AI models
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
import aiohttp

logger = logging.getLogger("ollama_client")

class OllamaClient:
    """Client for interacting with Ollama local AI models"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.session = None
        self.available_models = []
        
    async def initialize(self):
        """Initialize the Ollama client and check available models"""
        
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=300)  # 5 minute timeout
        )
        
        try:
            # Check if Ollama is running
            await self.health_check()
            
            # Get list of available models
            await self.refresh_available_models()
            
            # Ensure required models are available
            await self.ensure_required_models()
            
            logger.info(f"Ollama client initialized with models: {self.available_models}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama client: {e}")
            raise
    
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    return True
                else:
                    raise Exception(f"Ollama health check failed: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            raise
    
    async def refresh_available_models(self):
        """Refresh the list of available models"""
        
        try:
            async with self.session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_models = [model["name"] for model in data.get("models", [])]
                else:
                    logger.warning(f"Failed to get models: {response.status}")
                    
        except Exception as e:
            logger.error(f"Failed to refresh models: {e}")
    
    async def ensure_required_models(self):
        """Ensure required models are installed"""
        
        required_models = [
            "llama3.1",
            "nomic-embed-text"
        ]
        
        for model in required_models:
            if not any(model in available for available in self.available_models):
                logger.warning(f"Required model '{model}' not found. Attempting to pull...")
                await self.pull_model(model)
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry"""
        
        try:
            logger.info(f"Pulling model: {model_name}")
            
            async with self.session.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                if response.status == 200:
                    # Stream the pull progress
                    async for line in response.content:
                        try:
                            progress = json.loads(line)
                            if progress.get("status") == "success":
                                logger.info(f"Successfully pulled {model_name}")
                                await self.refresh_available_models()
                                return True
                        except json.JSONDecodeError:
                            continue
                else:
                    logger.error(f"Failed to pull model {model_name}: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    async def generate(self, model: str, prompt: str, format: str = None, 
                      system: str = None, temperature: float = 0.7,
                      max_tokens: int = 2048) -> str:
        """Generate text using Ollama model"""
        
        try:
            # Ensure model is available
            if not any(model in available for available in self.available_models):
                logger.warning(f"Model {model} not available. Attempting to pull...")
                if not await self.pull_model(model):
                    raise Exception(f"Failed to pull model {model}")
            
            request_data = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }
            
            if format:
                request_data["format"] = format
            
            if system:
                request_data["system"] = system
            
            async with self.session.post(
                f"{self.base_url}/api/generate",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("response", "")
                else:
                    error_text = await response.text()
                    raise Exception(f"Generation failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to generate with {model}: {e}")
            raise
    
    async def generate_structured(self, model: str, prompt: str, 
                                schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured output with JSON schema validation"""
        
        # Add schema information to prompt
        structured_prompt = f"""
        {prompt}
        
        Please respond in valid JSON format following this schema:
        {json.dumps(schema, indent=2)}
        
        Ensure your response is valid JSON and follows the schema exactly.
        """
        
        try:
            response = await self.generate(
                model=model,
                prompt=structured_prompt,
                format="json",
                temperature=0.3  # Lower temperature for more consistent structure
            )
            
            # Parse and validate JSON
            result = json.loads(response)
            
            # Basic schema validation (simplified)
            if self._validate_schema(result, schema):
                return result
            else:
                logger.warning("Generated JSON doesn't match schema")
                return {"error": "Schema validation failed", "raw_response": response}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return {"error": "Invalid JSON response", "raw_response": response}
        except Exception as e:
            logger.error(f"Structured generation failed: {e}")
            raise
    
    async def embeddings(self, text: str, model: str = "nomic-embed-text") -> List[float]:
        """Generate embeddings for text"""
        
        try:
            request_data = {
                "model": model,
                "prompt": text
            }
            
            async with self.session.post(
                f"{self.base_url}/api/embeddings",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("embedding", [])
                else:
                    error_text = await response.text()
                    raise Exception(f"Embeddings failed: {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    async def analyze_website_content(self, url: str, html_content: str, 
                                    purpose: str) -> Dict[str, Any]:
        """Use AI to analyze website content for scraping strategy"""
        
        prompt = f"""
        Analyze this website for optimal web scraping strategy:
        
        URL: {url}
        Purpose: {purpose}
        HTML Content (first 5000 chars): {html_content[:5000]}
        
        Analyze:
        1. Website type (e-commerce, directory, social, news, corporate, etc.)
        2. Content structure and patterns
        3. Best extraction approach (CSS selectors, AI extraction, JSON-LD, etc.)
        4. Potential challenges (JavaScript, auth, captcha, etc.)
        5. Recommended selectors for the purpose
        
        Focus on practical, actionable insights for web scraping.
        """
        
        schema = {
            "type": "object",
            "properties": {
                "website_type": {"type": "string"},
                "content_patterns": {"type": "array", "items": {"type": "string"}},
                "extraction_strategy": {"type": "string"},
                "recommended_selectors": {"type": "object"},
                "challenges": {"type": "array", "items": {"type": "string"}},
                "confidence": {"type": "number"},
                "reasoning": {"type": "string"}
            }
        }
        
        return await self.generate_structured(
            model="llama3.1",
            prompt=prompt,
            schema=schema
        )
    
    async def extract_data_with_ai(self, html_content: str, extraction_instruction: str,
                                 schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Use AI to extract specific data from HTML content"""
        
        if schema:
            prompt = f"""
            Extract data from this HTML content according to the instruction and schema:
            
            Instruction: {extraction_instruction}
            
            Schema: {json.dumps(schema, indent=2)}
            
            HTML Content: {html_content[:8000]}
            
            Extract the data accurately and return in the specified schema format.
            """
            
            return await self.generate_structured(
                model="llama3.1",
                prompt=prompt,
                schema=schema
            )
        else:
            prompt = f"""
            Extract data from this HTML content:
            
            Instruction: {extraction_instruction}
            
            HTML Content: {html_content[:8000]}
            
            Return the extracted data in a clear, structured format.
            """
            
            response = await self.generate(
                model="llama3.1",
                prompt=prompt,
                format="json"
            )
            
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                return {"extracted_text": response}
    
    async def optimize_css_selectors(self, html_content: str, target_content: str,
                                   current_selectors: List[str]) -> List[str]:
        """Use AI to optimize CSS selectors for better extraction"""
        
        prompt = f"""
        Optimize these CSS selectors for better data extraction:
        
        Target content to extract: {target_content}
        Current selectors: {current_selectors}
        
        HTML sample: {html_content[:5000]}
        
        Provide improved CSS selectors that are:
        1. More specific and accurate
        2. Less likely to break with page changes
        3. More efficient for the target content
        
        Return only the improved selectors as a JSON array.
        """
        
        try:
            response = await self.generate(
                model="llama3.1",
                prompt=prompt,
                format="json"
            )
            
            result = json.loads(response)
            if isinstance(result, list):
                return result
            elif isinstance(result, dict) and "selectors" in result:
                return result["selectors"]
            else:
                return current_selectors
                
        except Exception as e:
            logger.error(f"Selector optimization failed: {e}")
            return current_selectors
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Simple schema validation (basic implementation)"""
        
        if schema.get("type") != "object":
            return True  # Skip validation for non-object schemas
        
        required_properties = schema.get("properties", {})
        
        for prop_name, prop_schema in required_properties.items():
            if prop_name not in data:
                if prop_name in schema.get("required", []):
                    return False
                continue
            
            # Basic type checking
            expected_type = prop_schema.get("type")
            actual_value = data[prop_name]
            
            if expected_type == "string" and not isinstance(actual_value, str):
                return False
            elif expected_type == "number" and not isinstance(actual_value, (int, float)):
                return False
            elif expected_type == "array" and not isinstance(actual_value, list):
                return False
            elif expected_type == "object" and not isinstance(actual_value, dict):
                return False
        
        return True
    
    async def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """Get information about a specific model"""
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/show",
                json={"name": model_name}
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return {"error": f"Model info failed: {response.status}"}
                    
        except Exception as e:
            logger.error(f"Failed to get model info: {e}")
            return {"error": str(e)}
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
