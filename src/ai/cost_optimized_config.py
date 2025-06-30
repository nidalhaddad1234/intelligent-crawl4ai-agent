#!/usr/bin/env python3
"""
Cost-Optimized AI Configuration
DeepSeek-first configuration for maximum cost efficiency
"""

import os
from typing import List
from .hybrid_ai_service import HybridAIService, AIConfig, AIProvider

def create_cost_optimized_ai_service() -> HybridAIService:
    """
    Create cost-optimized AI service with DeepSeek as primary provider
    
    Priority Order (by cost efficiency):
    1. DeepSeek: $0.14/1M tokens (70x cheaper than GPT-4)
    2. Groq: Fast and cheap
    3. Local Ollama: Free (if available)
    4. OpenRouter: Free models available
    5. OpenAI: Premium fallback
    6. Anthropic: Most expensive
    """
    configs = [
        # 1st Priority: DeepSeek (Best value)
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
        
        # 2nd Priority: Groq (Fast and cheap)
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
        
        # 3rd Priority: Local Ollama (Free)
        AIConfig(
            provider=AIProvider.LOCAL_OLLAMA,
            model=os.getenv('OLLAMA_MODEL', 'llama3.2:3b'),
            base_url=os.getenv('OLLAMA_URL', 'http://localhost:11434'),
            priority=3,
            max_tokens=2048,
            temperature=0.1,
            enabled=bool(os.getenv('OLLAMA_URL'))
        ),
        
        # 4th Priority: OpenRouter (Free models)
        AIConfig(
            provider=AIProvider.OPENROUTER,
            model=os.getenv('OPENROUTER_MODEL', 'meta-llama/llama-3.1-8b-instruct:free'),
            api_key=os.getenv('OPENROUTER_API_KEY'),
            base_url="https://openrouter.ai/api/v1",
            priority=4,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('OPENROUTER_API_KEY'))
        ),
        
        # 5th Priority: OpenAI (Premium fallback)
        AIConfig(
            provider=AIProvider.OPENAI,
            model=os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
            api_key=os.getenv('OPENAI_API_KEY'),
            priority=5,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('OPENAI_API_KEY'))
        ),
        
        # 6th Priority: Anthropic (Most expensive)
        AIConfig(
            provider=AIProvider.ANTHROPIC,
            model=os.getenv('ANTHROPIC_MODEL', 'claude-3-haiku-20240307'),
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            priority=6,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('ANTHROPIC_API_KEY'))
        )
    ]
    
    return HybridAIService(configs)


def create_speed_optimized_ai_service() -> HybridAIService:
    """Create speed-optimized AI service (Groq first)"""
    configs = [
        # 1st Priority: Groq (Fastest - 500+ tokens/sec)
        AIConfig(
            provider=AIProvider.GROQ,
            model="llama-3.1-8b-instant",
            api_key=os.getenv('GROQ_API_KEY'),
            base_url="https://api.groq.com/openai/v1",
            priority=1,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('GROQ_API_KEY'))
        ),
        
        # 2nd Priority: DeepSeek (Good speed + cost)
        AIConfig(
            provider=AIProvider.DEEPSEEK,
            model="deepseek-chat",
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1",
            priority=2,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('DEEPSEEK_API_KEY'))
        ),
        
        # 3rd Priority: OpenAI (Reliable but slower)
        AIConfig(
            provider=AIProvider.OPENAI,
            model="gpt-4o-mini",
            api_key=os.getenv('OPENAI_API_KEY'),
            priority=3,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('OPENAI_API_KEY'))
        ),
        
        # 4th Priority: Local Ollama (Variable speed)
        AIConfig(
            provider=AIProvider.LOCAL_OLLAMA,
            model="llama3.2:3b",
            base_url="http://localhost:11434",
            priority=4,
            max_tokens=2048,
            temperature=0.1,
            enabled=True
        )
    ]
    
    return HybridAIService(configs)


def create_quality_optimized_ai_service() -> HybridAIService:
    """Create quality-optimized AI service (best models first)"""
    configs = [
        # 1st Priority: OpenAI (Best quality)
        AIConfig(
            provider=AIProvider.OPENAI,
            model="gpt-4o-mini",
            api_key=os.getenv('OPENAI_API_KEY'),
            priority=1,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('OPENAI_API_KEY'))
        ),
        
        # 2nd Priority: Anthropic (Best reasoning)
        AIConfig(
            provider=AIProvider.ANTHROPIC,
            model="claude-3-haiku-20240307",
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            priority=2,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('ANTHROPIC_API_KEY'))
        ),
        
        # 3rd Priority: DeepSeek (Good quality, cheap)
        AIConfig(
            provider=AIProvider.DEEPSEEK,
            model="deepseek-chat",
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com/v1",
            priority=3,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('DEEPSEEK_API_KEY'))
        ),
        
        # 4th Priority: Groq (Fast fallback)
        AIConfig(
            provider=AIProvider.GROQ,
            model="llama-3.1-8b-instant",
            api_key=os.getenv('GROQ_API_KEY'),
            base_url="https://api.groq.com/openai/v1",
            priority=4,
            max_tokens=4096,
            temperature=0.1,
            enabled=bool(os.getenv('GROQ_API_KEY'))
        )
    ]
    
    return HybridAIService(configs)


# Usage examples
def get_ai_service_by_strategy(strategy: str = "cost") -> HybridAIService:
    """
    Get AI service based on optimization strategy
    
    Args:
        strategy: "cost", "speed", or "quality"
    """
    if strategy == "cost":
        return create_cost_optimized_ai_service()
    elif strategy == "speed":
        return create_speed_optimized_ai_service()
    elif strategy == "quality":
        return create_quality_optimized_ai_service()
    else:
        return create_cost_optimized_ai_service()  # Default to cost optimization
