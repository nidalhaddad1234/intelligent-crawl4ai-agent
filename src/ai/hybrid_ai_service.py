"""
Hybrid AI Service - Supports both Local (Ollama) and Cloud APIs
Provides fallback capabilities and unified interface
"""

import json
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import requests
import openai
from anthropic import Anthropic
import os
from datetime import datetime


logger = logging.getLogger(__name__)


class AIProvider(Enum):
    """Supported AI providers"""
    LOCAL_OLLAMA = "local_ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    TOGETHER = "together"
    DEEPSEEK = "deepseek"
    OPENROUTER = "openrouter"


@dataclass
class AIConfig:
    """Configuration for AI providers"""
    provider: AIProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 2048
    temperature: float = 0.1
    timeout: int = 30
    enabled: bool = True
    priority: int = 1  # Lower number = higher priority


class HybridAIService:
    """
    Unified AI service that supports multiple providers with automatic fallback
    """
    
    def __init__(self, configs: List[AIConfig] = None):
        """
        Initialize with provider configurations
        
        Args:
            configs: List of AI provider configurations
        """
        self.configs = configs or self._load_default_configs()
        self.clients = {}
        self._initialize_clients()
        
        # Sort by priority
        self.configs.sort(key=lambda x: x.priority)
        
        # Statistics
        self.stats = {
            'requests_by_provider': {},
            'success_rates': {},
            'avg_response_times': {},
            'last_used': {}
        }
    
    def _load_default_configs(self) -> List[AIConfig]:
        """Load configurations from environment variables"""
        configs = []
        
        # Local Ollama (highest priority if available)
        if os.getenv('OLLAMA_URL'):
            configs.append(AIConfig(
                provider=AIProvider.LOCAL_OLLAMA,
                model=os.getenv('OLLAMA_MODEL', 'llama3.2:3b'),
                base_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'),
                priority=1,
                enabled=True
            ))
        
        # OpenAI (if API key provided)
        if os.getenv('OPENAI_API_KEY'):
            configs.append(AIConfig(
                provider=AIProvider.OPENAI,
                model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                api_key=os.getenv('OPENAI_API_KEY'),
                priority=2,
                max_tokens=4096,
                enabled=True
            ))
        
        # Anthropic Claude (if API key provided)
        if os.getenv('ANTHROPIC_API_KEY'):
            configs.append(AIConfig(
                provider=AIProvider.ANTHROPIC,
                model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
                api_key=os.getenv('ANTHROPIC_API_KEY'),
                priority=3,
                max_tokens=4096,
                enabled=True
            ))
        
        # Groq (fast and cheap)
        if os.getenv('GROQ_API_KEY'):
            configs.append(AIConfig(
                provider=AIProvider.GROQ,
                model=os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
                api_key=os.getenv('GROQ_API_KEY'),
                base_url="https://api.groq.com/openai/v1",
                priority=4,
                max_tokens=2048,
                enabled=True
            ))
        
        # DeepSeek (very cheap and good)
        if os.getenv('DEEPSEEK_API_KEY'):
            configs.append(AIConfig(
                provider=AIProvider.DEEPSEEK,
                model=os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
                api_key=os.getenv('DEEPSEEK_API_KEY'),
                base_url="https://api.deepseek.com/v1",
                priority=5,
                max_tokens=4096,
                enabled=True
            ))
        
        # OpenRouter (access to many models)
        if os.getenv('OPENROUTER_API_KEY'):
            configs.append(AIConfig(
                provider=AIProvider.OPENROUTER,
                model=os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.1-8b-instruct:free'),
                api_key=os.getenv('OPENROUTER_API_KEY'),
                base_url="https://openrouter.ai/api/v1",
                priority=6,
                max_tokens=4096,
                enabled=True
            ))
        
        return configs
    
    def _initialize_clients(self):
        """Initialize API clients for each provider"""
        for config in self.configs:
            if not config.enabled:
                continue
                
            try:
                if config.provider == AIProvider.OPENAI:
                    self.clients[config.provider] = openai.OpenAI(
                        api_key=config.api_key
                    )
                elif config.provider == AIProvider.ANTHROPIC:
                    self.clients[config.provider] = Anthropic(
                        api_key=config.api_key
                    )
                elif config.provider == AIProvider.GROQ:
                    self.clients[config.provider] = openai.OpenAI(
                        api_key=config.api_key,
                        base_url=config.base_url
                    )
                elif config.provider == AIProvider.DEEPSEEK:
                    self.clients[config.provider] = openai.OpenAI(
                        api_key=config.api_key,
                        base_url=config.base_url
                    )
                elif config.provider == AIProvider.OPENROUTER:
                    self.clients[config.provider] = openai.OpenAI(
                        api_key=config.api_key,
                        base_url=config.base_url
                    )
                # Local Ollama doesn't need a client
                
                logger.info(f"Initialized {config.provider.value} with model {config.model}")
                
            except Exception as e:
                logger.error(f"Failed to initialize {config.provider.value}: {e}")
                config.enabled = False
    
    async def generate_plan(self, user_request: str, tools: Dict[str, Any]) -> Tuple[Dict[str, Any], float]:
        """
        Generate an execution plan using the best available AI provider
        
        Args:
            user_request: User's natural language request
            tools: Available tools manifest
            
        Returns:
            Tuple of (plan_data, confidence)
        """
        prompt = self._build_planning_prompt(user_request, tools)
        
        # Try providers in priority order
        for config in self.configs:
            if not config.enabled:
                continue
                
            try:
                start_time = datetime.now()
                
                logger.info(f"Trying {config.provider.value} for planning")
                
                if config.provider == AIProvider.LOCAL_OLLAMA:
                    response = await self._call_ollama(prompt, config)
                elif config.provider == AIProvider.OPENAI:
                    response = await self._call_openai(prompt, config)
                elif config.provider == AIProvider.ANTHROPIC:
                    response = await self._call_anthropic(prompt, config)
                elif config.provider == AIProvider.GROQ:
                    response = await self._call_groq(prompt, config)
                elif config.provider == AIProvider.DEEPSEEK:
                    response = await self._call_deepseek(prompt, config)
                elif config.provider == AIProvider.OPENROUTER:
                    response = await self._call_openrouter(prompt, config)
                else:
                    continue
                
                # Parse and validate response
                plan_data = self._parse_response(response)
                confidence = plan_data.get('confidence', 0.8)
                
                # Update statistics
                response_time = (datetime.now() - start_time).total_seconds()
                self._update_stats(config.provider, True, response_time)
                
                logger.info(f"Successfully generated plan using {config.provider.value}")
                return plan_data, confidence
                
            except Exception as e:
                logger.warning(f"{config.provider.value} failed: {e}")
                self._update_stats(config.provider, False, 0)
                continue
        
        # All providers failed
        logger.error("All AI providers failed, using fallback plan")
        return self._create_fallback_plan(user_request), 0.1
    
    async def _call_ollama(self, prompt: str, config: AIConfig) -> str:
        """Call local Ollama API"""
        response = requests.post(
            f"{config.base_url}/api/generate",
            json={
                "model": config.model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens
                }
            },
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "{}")
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    async def _call_openai(self, prompt: str, config: AIConfig) -> str:
        """Call OpenAI API"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are an AI planning assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic(self, prompt: str, config: AIConfig) -> str:
        """Call Anthropic Claude API"""
        client = self.clients[config.provider]
        
        response = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    async def _call_groq(self, prompt: str, config: AIConfig) -> str:
        """Call Groq API"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are an AI planning assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def _call_deepseek(self, prompt: str, config: AIConfig) -> str:
        """Call DeepSeek API"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are an AI planning assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def _call_openrouter(self, prompt: str, config: AIConfig) -> str:
        """Call OpenRouter API"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are an AI planning assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            # Note: Not all OpenRouter models support response_format
        )
        
        return response.choices[0].message.content
    
    def _build_planning_prompt(self, request: str, tools: Dict[str, Any]) -> str:
        """Build optimized prompt for any AI provider"""
        tool_summary = []
        for tool in tools.get("tools", []):
            params = [p["name"] for p in tool.get("parameters", []) if p.get("required")]
            tool_summary.append(f"- {tool['name']}: {tool['description']} (params: {', '.join(params)})")
        
        return f"""You are an AI planning assistant that creates precise JSON execution plans.

CRITICAL: Respond with ONLY valid JSON. No explanations, no markdown, no extra text.

Available tools:
{chr(10).join(tool_summary)}

Create a step-by-step plan for: {request}

Return this exact JSON structure:
{{
  "description": "Clear description of what the plan accomplishes",
  "confidence": 0.85,
  "steps": [
    {{
      "step_id": 1,
      "tool": "exact_tool_name_from_list_above",
      "description": "What this step does",
      "parameters": {{"param1": "value1", "param2": "value2"}},
      "depends_on": [],
      "error_handling": "retry"
    }}
  ]
}}

Rules:
- Use ONLY tools from the list above
- If request mentions URLs, start with crawl_web
- If request mentions "analyze", use analyze_content
- If request mentions "export" or "CSV", use export_csv
- Make step_id sequential (1, 2, 3...)
- Set confidence between 0.0 and 1.0
- Return ONLY the JSON, nothing else"""
    
    def _parse_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response and extract JSON"""
        try:
            # Try direct JSON parsing first
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from text
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                raise ValueError("No valid JSON found in response")
    
    def _create_fallback_plan(self, request: str) -> Dict[str, Any]:
        """Create a simple fallback plan when all AI providers fail"""
        return {
            "description": f"Fallback plan for: {request}",
            "confidence": 0.1,
            "steps": [
                {
                    "step_id": 1,
                    "tool": "crawl_web",
                    "description": "Extract data from web page",
                    "parameters": {"strategy": "auto"},
                    "depends_on": [],
                    "error_handling": "retry"
                }
            ]
        }
    
    def _update_stats(self, provider: AIProvider, success: bool, response_time: float):
        """Update provider statistics"""
        provider_name = provider.value
        
        if provider_name not in self.stats['requests_by_provider']:
            self.stats['requests_by_provider'][provider_name] = 0
            self.stats['success_rates'][provider_name] = []
            self.stats['avg_response_times'][provider_name] = []
        
        self.stats['requests_by_provider'][provider_name] += 1
        self.stats['success_rates'][provider_name].append(1 if success else 0)
        if success:
            self.stats['avg_response_times'][provider_name].append(response_time)
        self.stats['last_used'][provider_name] = datetime.now().isoformat()
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status and statistics for all providers"""
        status = {}
        
        for config in self.configs:
            provider_name = config.provider.value
            
            # Calculate statistics
            total_requests = self.stats['requests_by_provider'].get(provider_name, 0)
            success_rate = 0
            avg_response_time = 0
            
            if total_requests > 0:
                successes = self.stats['success_rates'][provider_name]
                success_rate = sum(successes) / len(successes)
                
                response_times = self.stats['avg_response_times'][provider_name]
                if response_times:
                    avg_response_time = sum(response_times) / len(response_times)
            
            status[provider_name] = {
                'enabled': config.enabled,
                'model': config.model,
                'priority': config.priority,
                'total_requests': total_requests,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'last_used': self.stats['last_used'].get(provider_name),
                'status': 'healthy' if success_rate > 0.8 else 'degraded' if success_rate > 0.5 else 'unhealthy'
            }
        
        return status
    
    def switch_provider_priority(self, provider: AIProvider, new_priority: int):
        """Change provider priority dynamically"""
        for config in self.configs:
            if config.provider == provider:
                config.priority = new_priority
                break
        
        # Re-sort by priority
        self.configs.sort(key=lambda x: x.priority)
        logger.info(f"Updated {provider.value} priority to {new_priority}")
    
    def disable_provider(self, provider: AIProvider):
        """Disable a provider"""
        for config in self.configs:
            if config.provider == provider:
                config.enabled = False
                logger.info(f"Disabled provider {provider.value}")
                break
    
    def enable_provider(self, provider: AIProvider):
        """Enable a provider"""
        for config in self.configs:
            if config.provider == provider:
                config.enabled = True
                logger.info(f"Enabled provider {provider.value}")
                break
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any],
                                model: str = None, max_retries: int = 3) -> Dict[str, Any]:
        """
        Generate structured JSON output using the best available AI provider
        
        Args:
            prompt: Input prompt for generation
            schema: JSON schema for the expected output
            model: Optional model override
            max_retries: Maximum retry attempts
            
        Returns:
            Dict containing the structured response
        """
        
        # Build structured prompt
        structured_prompt = f"""
{prompt}

CRITICAL: Respond with ONLY valid JSON following this exact schema:
{json.dumps(schema, indent=2)}

Requirements:
- Response must be valid JSON
- All required fields must be present
- Follow the schema structure exactly
- Do not include any text outside the JSON response
"""
        
        # Try providers in priority order
        for config in self.configs:
            if not config.enabled:
                continue
                
            try:
                start_time = datetime.now()
                
                logger.debug(f"Trying {config.provider.value} for structured generation")
                
                if config.provider == AIProvider.LOCAL_OLLAMA:
                    response = await self._call_ollama_structured(structured_prompt, config)
                elif config.provider == AIProvider.OPENAI:
                    response = await self._call_openai_structured(structured_prompt, config)
                elif config.provider == AIProvider.ANTHROPIC:
                    response = await self._call_anthropic_structured(structured_prompt, config)
                elif config.provider == AIProvider.GROQ:
                    response = await self._call_groq_structured(structured_prompt, config)
                elif config.provider == AIProvider.DEEPSEEK:
                    response = await self._call_deepseek_structured(structured_prompt, config)
                elif config.provider == AIProvider.OPENROUTER:
                    response = await self._call_openrouter_structured(structured_prompt, config)
                else:
                    continue
                
                # Parse and validate response
                result = self._parse_response(response)
                
                # Validate against schema
                if self._validate_schema(result, schema):
                    response_time = (datetime.now() - start_time).total_seconds()
                    self._update_stats(config.provider, True, response_time)
                    
                    logger.debug(f"Successfully generated structured output using {config.provider.value}")
                    return result
                else:
                    logger.warning(f"Schema validation failed for {config.provider.value}")
                    continue
                
            except Exception as e:
                logger.warning(f"{config.provider.value} structured generation failed: {e}")
                self._update_stats(config.provider, False, 0)
                continue
        
        # All providers failed
        logger.error("All AI providers failed for structured generation")
        return {"error": "All providers failed", "schema": schema}
    
    async def generate_text(self, prompt: str, model: str = None, 
                           temperature: float = None, max_tokens: int = None) -> Dict[str, Any]:
        """
        Generate plain text using the best available AI provider
        
        Args:
            prompt: Input prompt for generation
            model: Optional model override
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            
        Returns:
            Dict containing response content and metadata
        """
        
        # Try providers in priority order
        for config in self.configs:
            if not config.enabled:
                continue
                
            try:
                start_time = datetime.now()
                
                # Override config values if provided
                effective_temp = temperature if temperature is not None else config.temperature
                effective_tokens = max_tokens if max_tokens is not None else config.max_tokens
                
                logger.debug(f"Trying {config.provider.value} for text generation")
                
                if config.provider == AIProvider.LOCAL_OLLAMA:
                    response = await self._call_ollama_text(prompt, config, effective_temp, effective_tokens)
                elif config.provider == AIProvider.OPENAI:
                    response = await self._call_openai_text(prompt, config, effective_temp, effective_tokens)
                elif config.provider == AIProvider.ANTHROPIC:
                    response = await self._call_anthropic_text(prompt, config, effective_temp, effective_tokens)
                elif config.provider == AIProvider.GROQ:
                    response = await self._call_groq_text(prompt, config, effective_temp, effective_tokens)
                elif config.provider == AIProvider.DEEPSEEK:
                    response = await self._call_deepseek_text(prompt, config, effective_temp, effective_tokens)
                elif config.provider == AIProvider.OPENROUTER:
                    response = await self._call_openrouter_text(prompt, config, effective_temp, effective_tokens)
                else:
                    continue
                
                response_time = (datetime.now() - start_time).total_seconds()
                self._update_stats(config.provider, True, response_time)
                
                logger.debug(f"Successfully generated text using {config.provider.value}")
                return {
                    "content": response,
                    "provider": config.provider.value,
                    "model": config.model,
                    "success": True,
                    "response_time": response_time
                }
                
            except Exception as e:
                logger.warning(f"{config.provider.value} text generation failed: {e}")
                self._update_stats(config.provider, False, 0)
                continue
        
        # All providers failed
        logger.error("All AI providers failed for text generation")
        return {
            "content": "",
            "provider": "none",
            "model": "none",
            "success": False,
            "error": "All providers failed"
        }
    
    async def _call_ollama_structured(self, prompt: str, config: AIConfig) -> str:
        """Call Ollama for structured output"""
        response = requests.post(
            f"{config.base_url}/api/generate",
            json={
                "model": config.model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.max_tokens
                }
            },
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "{}")
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    async def _call_openai_structured(self, prompt: str, config: AIConfig) -> str:
        """Call OpenAI for structured output"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds only in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic_structured(self, prompt: str, config: AIConfig) -> str:
        """Call Anthropic for structured output"""
        client = self.clients[config.provider]
        
        response = client.messages.create(
            model=config.model,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    async def _call_groq_structured(self, prompt: str, config: AIConfig) -> str:
        """Call Groq for structured output"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds only in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def _call_deepseek_structured(self, prompt: str, config: AIConfig) -> str:
        """Call DeepSeek for structured output"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds only in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            response_format={"type": "json_object"}
        )
        
        return response.choices[0].message.content
    
    async def _call_openrouter_structured(self, prompt: str, config: AIConfig) -> str:
        """Call OpenRouter for structured output"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that responds only in valid JSON format."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=config.max_tokens,
            temperature=config.temperature
            # Note: Not all OpenRouter models support response_format
        )
        
        return response.choices[0].message.content
    
    async def _call_ollama_text(self, prompt: str, config: AIConfig, temperature: float, max_tokens: int) -> str:
        """Call Ollama for plain text"""
        response = requests.post(
            f"{config.base_url}/api/generate",
            json={
                "model": config.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            },
            timeout=config.timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            raise Exception(f"Ollama API error: {response.status_code}")
    
    async def _call_openai_text(self, prompt: str, config: AIConfig, temperature: float, max_tokens: int) -> str:
        """Call OpenAI for plain text"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic_text(self, prompt: str, config: AIConfig, temperature: float, max_tokens: int) -> str:
        """Call Anthropic for plain text"""
        client = self.clients[config.provider]
        
        response = client.messages.create(
            model=config.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return response.content[0].text
    
    async def _call_groq_text(self, prompt: str, config: AIConfig, temperature: float, max_tokens: int) -> str:
        """Call Groq for plain text"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    async def _call_deepseek_text(self, prompt: str, config: AIConfig, temperature: float, max_tokens: int) -> str:
        """Call DeepSeek for plain text"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    async def _call_openrouter_text(self, prompt: str, config: AIConfig, temperature: float, max_tokens: int) -> str:
        """Call OpenRouter for plain text"""
        client = self.clients[config.provider]
        
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content
    
    async def analyze_website_content(self, url: str, html_content: str, 
                                    purpose: str) -> Dict[str, Any]:
        """
        Analyze website content for optimal scraping strategy
        
        Args:
            url: Website URL
            html_content: HTML content to analyze
            purpose: Purpose of the extraction
            
        Returns:
            Dict containing analysis results
        """
        
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
        
        return await self.generate_structured(prompt=prompt, schema=schema)
    
    async def generate(self, prompt: str, model: str = None, 
                      format: str = None, system: str = None,
                      temperature: float = None, max_tokens: int = None) -> Dict[str, Any]:
        """
        Generate text with a response format similar to LLMService
        
        Args:
            prompt: Input prompt
            model: Optional model override
            format: Output format (json, text)
            system: System message
            temperature: Temperature override
            max_tokens: Max tokens override
            
        Returns:
            Dict with content, success, and metadata
        """
        
        # Build full prompt with system message if provided
        full_prompt = prompt
        if system:
            full_prompt = f"System: {system}\n\nUser: {prompt}"
        
        # Use generate_text method
        result = await self.generate_text(
            prompt=full_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Convert to LLMService-compatible format
        if result["success"]:
            content = result["content"]
            
            # If JSON format requested, try to parse and reformat
            if format == "json":
                try:
                    parsed = json.loads(content)
                    content = json.dumps(parsed, indent=2)
                except json.JSONDecodeError:
                    # If not valid JSON, wrap in JSON
                    content = json.dumps({"response": content})
            
            return {
                "content": content,
                "model": result["model"],
                "success": True,
                "processing_time": result["response_time"],
                "metadata": {
                    "provider": result["provider"]
                }
            }
        else:
            return {
                "content": "",
                "model": "unknown",
                "success": False,
                "processing_time": 0.0,
                "error": result.get("error", "Generation failed")
            }
    
    def _validate_schema(self, data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Validate data against JSON schema (basic implementation)"""
        
        if not isinstance(data, dict):
            return False
        
        # Check if required fields are present
        required = schema.get("required", [])
        for field in required:
            if field not in data:
                logger.warning(f"Required field '{field}' missing from response")
                return False
        
        # Check field types
        properties = schema.get("properties", {})
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
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all providers"""
        health_status = {}
        test_prompt = "Generate JSON: {\"test\": \"success\"}"
        
        for config in self.configs:
            if not config.enabled:
                health_status[config.provider.value] = {
                    'status': 'disabled',
                    'response_time': None,
                    'error': None
                }
                continue
            
            try:
                start_time = datetime.now()
                
                if config.provider == AIProvider.LOCAL_OLLAMA:
                    response = await self._call_ollama(test_prompt, config)
                elif config.provider == AIProvider.OPENAI:
                    response = await self._call_openai(test_prompt, config)
                elif config.provider == AIProvider.ANTHROPIC:
                    response = await self._call_anthropic(test_prompt, config)
                elif config.provider == AIProvider.GROQ:
                    response = await self._call_groq(test_prompt, config)
                elif config.provider == AIProvider.DEEPSEEK:
                    response = await self._call_deepseek(test_prompt, config)
                elif config.provider == AIProvider.OPENROUTER:
                    response = await self._call_openrouter(test_prompt, config)
                
                response_time = (datetime.now() - start_time).total_seconds()
                
                # Try to parse response
                parsed = self._parse_response(response)
                
                health_status[config.provider.value] = {
                    'status': 'healthy',
                    'response_time': response_time,
                    'error': None
                }
                
            except Exception as e:
                health_status[config.provider.value] = {
                    'status': 'unhealthy',
                    'response_time': None,
                    'error': str(e)
                }
        
        return health_status


# Example usage and configuration
def create_production_ai_service() -> HybridAIService:
    """Create production-ready AI service with cost-optimized provider order"""
    configs = [
        # Primary: DeepSeek (70x cheaper than GPT-4, excellent quality)
        AIConfig(
            provider=AIProvider.DEEPSEEK,
            model="deepseek-chat",
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1",
            priority=1,  # HIGHEST PRIORITY
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('DEEPSEEK_API_KEY'))
        ),
        
        # Secondary: Groq (fast and cheap)
        AIConfig(
            provider=AIProvider.GROQ,
            model="llama-3.1-8b-instant",
            api_key=os.getenv('GROQ_API_KEY'),
            base_url="https://api.groq.com/openai/v1",
            priority=2,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('GROQ_API_KEY'))
        ),
        
        # Tertiary: Local Ollama (free)
        AIConfig(
            provider=AIProvider.LOCAL_OLLAMA,
            model="llama3.2:3b",
            base_url="http://localhost:11434",
            priority=3,
            max_tokens=2048,
            temperature=0.1,
            enabled=bool(os.getenv('OLLAMA_URL', 'http://localhost:11434'))
        ),
        
        # Quaternary: OpenRouter (free models available)
        AIConfig(
            provider=AIProvider.OPENROUTER,
            model="meta-llama/llama-3.1-8b-instruct:free",
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url="https://openrouter.ai/api/v1",
            priority=4,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('OPENROUTER_API_KEY'))
        ),
        
        # Fifth: OpenAI (premium fallback - more expensive)
        AIConfig(
            provider=AIProvider.OPENAI,
            model="gpt-4o-mini",
            api_key=os.getenv('OPENAI_API_KEY'),
            priority=5,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('OPENAI_API_KEY'))
        ),
        
        # Sixth: Anthropic (most expensive)
        AIConfig(
            provider=AIProvider.ANTHROPIC,
            model="claude-3-haiku-20240307",
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            priority=6,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('ANTHROPIC_API_KEY'))
        )
    ]
    
    return HybridAIService(configs)
