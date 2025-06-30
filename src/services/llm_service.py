#!/usr/bin/env python3
"""
LLM Service
Enhanced wrapper for Ollama AI model operations with production features
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import aiohttp
import time

logger = logging.getLogger("llm_service")

@dataclass
class LLMConfig:
    """Configuration for LLM service"""
    base_url: str = "http://localhost:11434"
    default_model: str = "llama3.1"
    embedding_model: str = "nomic-embed-text"
    timeout_seconds: int = 300
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: int = 2048

@dataclass
class LLMResponse:
    """Structured response from LLM operations"""
    content: str
    model: str
    success: bool
    processing_time: float
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class LLMService:
    """
    Production-ready LLM service with enhanced error handling,
    monitoring, and optimization features
    """
    
    def __init__(self, config: LLMConfig = None):
        self.config = config or LLMConfig()
        self.session = None
        self.available_models = []
        self.model_cache = {}
        self.request_count = 0
        self.error_count = 0
        
    async def initialize(self) -> bool:
        """Initialize the LLM service with health checks"""
        
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds)
            )
            
            # Health check
            if not await self.health_check():
                raise Exception("Ollama service is not available")
            
            # Load available models
            await self.refresh_available_models()
            
            # Ensure required models are available
            await self.ensure_required_models()
            
            logger.info(f"LLM service initialized successfully with {len(self.available_models)} models")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            return False
    
    async def health_check(self) -> bool:
        """Check if Ollama service is healthy"""
        
        try:
            async with self.session.get(f"{self.config.base_url}/api/tags") as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def refresh_available_models(self) -> List[str]:
        """Refresh and return list of available models"""
        
        try:
            async with self.session.get(f"{self.config.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    self.available_models = [model["name"] for model in data.get("models", [])]
                    return self.available_models
                else:
                    logger.warning(f"Failed to get models: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Failed to refresh models: {e}")
            return []
    
    async def ensure_required_models(self) -> bool:
        """Ensure required models are installed"""
        
        required_models = [self.config.default_model, self.config.embedding_model]
        
        for model in required_models:
            if not any(model in available for available in self.available_models):
                logger.info(f"Pulling required model: {model}")
                if not await self.pull_model(model):
                    logger.error(f"Failed to pull required model: {model}")
                    return False
        
        return True
    
    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry with progress tracking"""
        
        try:
            logger.info(f"Pulling model: {model_name}")
            
            async with self.session.post(
                f"{self.config.base_url}/api/pull",
                json={"name": model_name}
            ) as response:
                if response.status == 200:
                    async for line in response.content:
                        try:
                            progress = json.loads(line)
                            if progress.get("status") == "success":
                                logger.info(f"Successfully pulled {model_name}")
                                await self.refresh_available_models()
                                return True
                        except json.JSONDecodeError:
                            continue
                
                logger.error(f"Failed to pull model {model_name}: {response.status}")
                return False
                
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            return False
    
    async def generate(self, prompt: str, model: str = None, 
                      format: str = None, system: str = None,
                      temperature: float = None, max_tokens: int = None) -> LLMResponse:
        """Generate text with comprehensive error handling and monitoring"""
        
        start_time = time.time()
        self.request_count += 1
        
        model = model or self.config.default_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
        
        try:
            # Validate model availability
            if not await self._ensure_model_available(model):
                raise Exception(f"Model {model} is not available")
            
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
            
            # Execute with retries
            for attempt in range(self.config.max_retries):
                try:
                    async with self.session.post(
                        f"{self.config.base_url}/api/generate",
                        json=request_data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            processing_time = time.time() - start_time
                            
                            return LLMResponse(
                                content=result.get("response", ""),
                                model=model,
                                success=True,
                                processing_time=processing_time,
                                tokens_used=result.get("eval_count"),
                                metadata={
                                    "prompt_tokens": result.get("prompt_eval_count"),
                                    "completion_tokens": result.get("eval_count"),
                                    "attempt": attempt + 1
                                }
                            )
                        else:
                            error_text = await response.text()
                            if attempt == self.config.max_retries - 1:
                                raise Exception(f"Generation failed: {response.status} - {error_text}")
                            
                            logger.warning(f"Generation attempt {attempt + 1} failed, retrying...")
                            await asyncio.sleep(2 ** attempt)  # Exponential backoff
                            
                except aiohttp.ClientError as e:
                    if attempt == self.config.max_retries - 1:
                        raise
                    logger.warning(f"Connection error on attempt {attempt + 1}, retrying...")
                    await asyncio.sleep(2 ** attempt)
                    
        except Exception as e:
            self.error_count += 1
            processing_time = time.time() - start_time
            logger.error(f"Generation failed after all retries: {e}")
            
            return LLMResponse(
                content="",
                model=model,
                success=False,
                processing_time=processing_time,
                error=str(e)
            )
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any],
                                model: str = None, max_retries: int = 3) -> Dict[str, Any]:
        """Generate structured JSON output with schema validation"""
        
        structured_prompt = f"""
{prompt}

Please respond in valid JSON format following this exact schema:
{json.dumps(schema, indent=2)}

Requirements:
- Response must be valid JSON
- All required fields must be present
- Follow the schema structure exactly
- Do not include any text outside the JSON response
"""
        
        model = model or self.config.default_model
        
        for attempt in range(max_retries):
            try:
                response = await self.generate(
                    prompt=structured_prompt,
                    model=model,
                    format="json",
                    temperature=0.3  # Lower temperature for consistency
                )
                
                if not response.success:
                    if attempt == max_retries - 1:
                        return {"error": "LLM generation failed", "details": response.error}
                    continue
                
                # Parse and validate JSON
                try:
                    result = json.loads(response.content)
                    
                    # Validate against schema
                    if self._validate_schema(result, schema):
                        return result
                    else:
                        logger.warning(f"Schema validation failed on attempt {attempt + 1}")
                        if attempt == max_retries - 1:
                            return {
                                "error": "Schema validation failed",
                                "raw_response": response.content,
                                "expected_schema": schema
                            }
                        
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parsing failed on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        return {
                            "error": "Invalid JSON response",
                            "raw_response": response.content
                        }
                
                # Wait before retry
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Structured generation attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return {"error": "Generation failed", "details": str(e)}
        
        return {"error": "All generation attempts failed"}
    
    async def embeddings(self, text: str, model: str = None) -> List[float]:
        """Generate embeddings for text with error handling"""
        
        model = model or self.config.embedding_model
        
        try:
            if not await self._ensure_model_available(model):
                raise Exception(f"Embedding model {model} is not available")
            
            request_data = {
                "model": model,
                "prompt": text
            }
            
            async with self.session.post(
                f"{self.config.base_url}/api/embeddings",
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
        """Analyze website content for optimal scraping strategy"""
        
        prompt = f"""
Analyze this website for optimal web scraping strategy:

URL: {url}
Purpose: {purpose}
HTML Content (first 5000 chars): {html_content[:5000]}

Provide a comprehensive analysis including:
1. Website type (e-commerce, directory, social, news, corporate, etc.)
2. Content structure and patterns
3. Best extraction approach (CSS selectors, AI extraction, JSON-LD, etc.)
4. Potential challenges (JavaScript, auth, captcha, rate limiting, etc.)
5. Recommended CSS selectors for the purpose
6. Data quality assessment
7. Success probability estimation

Focus on practical, actionable insights for web scraping.
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
        
        return await self.generate_structured(
            prompt=prompt,
            schema=schema,
            model=self.config.default_model
        )
    
    async def extract_data_with_ai(self, html_content: str, extraction_instruction: str,
                                 schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract specific data from HTML using AI"""
        
        if schema:
            prompt = f"""
Extract data from this HTML content according to the instruction and schema:

Instruction: {extraction_instruction}

Schema: {json.dumps(schema, indent=2)}

HTML Content: {html_content[:8000]}

Requirements:
- Extract data accurately according to the instruction
- Follow the provided schema exactly
- Return null for fields that cannot be found
- Ensure all extracted data is properly formatted
"""
            
            return await self.generate_structured(
                prompt=prompt,
                schema=schema,
                model=self.config.default_model
            )
        else:
            prompt = f"""
Extract data from this HTML content:

Instruction: {extraction_instruction}

HTML Content: {html_content[:8000]}

Return the extracted data in a clear, structured JSON format.
Include all relevant information found in the HTML.
"""
            
            response = await self.generate(
                prompt=prompt,
                model=self.config.default_model,
                format="json"
            )
            
            if response.success:
                try:
                    return json.loads(response.content)
                except json.JSONDecodeError:
                    return {"extracted_text": response.content}
            else:
                return {"error": response.error}
    
    async def optimize_css_selectors(self, html_content: str, target_content: str,
                                   current_selectors: List[str]) -> List[str]:
        """Use AI to optimize CSS selectors for better extraction"""
        
        prompt = f"""
Optimize these CSS selectors for better data extraction:

Target content to extract: {target_content}
Current selectors: {current_selectors}

HTML sample: {html_content[:5000]}

Provide improved CSS selectors that are:
1. More specific and accurate for the target content
2. Less likely to break with minor page changes
3. More efficient and performant
4. Robust against common website variations

Return only the improved selectors as a JSON array.
"""
        
        try:
            response = await self.generate(
                prompt=prompt,
                model=self.config.default_model,
                format="json"
            )
            
            if response.success:
                result = json.loads(response.content)
                if isinstance(result, list):
                    return result
                elif isinstance(result, dict) and "selectors" in result:
                    return result["selectors"]
            
            # Return original selectors if optimization fails
            logger.warning("Selector optimization failed, returning original selectors")
            return current_selectors
            
        except Exception as e:
            logger.error(f"Selector optimization failed: {e}")
            return current_selectors
    
    async def _ensure_model_available(self, model: str) -> bool:
        """Ensure a model is available, pull if necessary"""
        
        if any(model in available for available in self.available_models):
            return True
        
        logger.info(f"Model {model} not available, attempting to pull...")
        return await self.pull_model(model)
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate data against JSON schema (basic implementation)"""
        
        if schema.get("type") != "object":
            return True
        
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Check required fields
        for field in required:
            if field not in data:
                logger.warning(f"Required field '{field}' missing from response")
                return False
        
        # Check field types
        for field, field_schema in properties.items():
            if field not in data:
                continue
            
            value = data[field]
            expected_type = field_schema.get("type")
            
            if expected_type == "string" and not isinstance(value, str):
                return False
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False
            elif expected_type == "array" and not isinstance(value, list):
                return False
            elif expected_type == "object" and not isinstance(value, dict):
                return False
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False
        
        return True
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get service performance statistics"""
        
        return {
            "requests_processed": self.request_count,
            "errors_encountered": self.error_count,
            "success_rate": (self.request_count - self.error_count) / max(self.request_count, 1),
            "available_models": self.available_models,
            "default_model": self.config.default_model,
            "embedding_model": self.config.embedding_model,
            "service_health": await self.health_check()
        }
    
    async def cleanup(self):
        """Clean up resources"""
        if self.session:
            await self.session.close()
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
