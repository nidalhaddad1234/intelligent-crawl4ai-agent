#!/usr/bin/env python3
"""
Context-Aware LLM Strategy
Advanced LLM strategy that uses context and learning for better extraction
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse

from .intelligent_base import IntelligentLLMStrategy
from core.base_strategy import StrategyResult

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
        
        # Update metadata with context information
        if hasattr(result, 'metadata'):
            result.metadata.update({
                "context_enhanced": bool(domain_context),
                "domain_context_used": bool(domain_context),
                "learning_stored": result.success and self.chromadb_manager is not None
            })
        
        return result
    
    async def _get_domain_context(self, url: str, purpose: str) -> Dict[str, Any]:
        """Get domain-specific context from previous extractions"""
        
        if not self.chromadb_manager:
            return self._get_local_domain_context(url, purpose)
        
        try:
            # Extract domain from URL
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
            self.logger.warning(f"Failed to get domain context from ChromaDB: {e}")
            # Fallback to local context
            return self._get_local_domain_context(url, purpose)
        
        return {}
    
    def _get_local_domain_context(self, url: str, purpose: str) -> Dict[str, Any]:
        """Get domain context from local memory"""
        
        try:
            domain = urlparse(url).netloc
            context_key = f"{domain}_{purpose}"
            
            if context_key in self.context_memory:
                context_data = self.context_memory[context_key]
                
                # Return context if we have sufficient data
                if context_data.get("extraction_count", 0) >= 2:
                    return {
                        "domain_patterns": context_data.get("patterns", {}),
                        "domain": domain,
                        "local_context": True
                    }
        except Exception as e:
            self.logger.warning(f"Failed to get local domain context: {e}")
        
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
                
                # Track success indicators
                indicators = extraction.get("success_indicators", [])
                if isinstance(indicators, list):
                    patterns["success_indicators"].extend(indicators)
        
        # Remove duplicates and get most common
        if patterns["common_fields"]:
            from collections import Counter
            field_counts = Counter(patterns["common_fields"])
            patterns["common_fields"] = [field for field, count in field_counts.most_common(10)]
        
        if patterns["success_indicators"]:
            from collections import Counter
            indicator_counts = Counter(patterns["success_indicators"])
            patterns["success_indicators"] = [ind for ind, count in indicator_counts.most_common(5)]
        
        return patterns
    
    async def _store_learning_context(self, url: str, purpose: str, extracted_data: Dict[str, Any], context: Dict[str, Any]):
        """Store successful extraction context for future learning"""
        
        # Store in ChromaDB if available
        if self.chromadb_manager:
            await self._store_chromadb_learning(url, purpose, extracted_data, context)
        
        # Store in local memory
        self._store_local_learning(url, purpose, extracted_data, context)
    
    async def _store_chromadb_learning(self, url: str, purpose: str, extracted_data: Dict[str, Any], context: Dict[str, Any]):
        """Store learning data in ChromaDB"""
        
        learning_data = {
            "url": url,
            "purpose": purpose,
            "extracted_fields": list(extracted_data.keys()),
            "context_used": context,
            "timestamp": time.time(),
            "strategy": "ContextAwareLLMStrategy",
            "success_indicators": self._identify_success_indicators(extracted_data)
        }
        
        try:
            await self.chromadb_manager.store_strategy_learning(learning_data)
        except Exception as e:
            self.logger.warning(f"Failed to store learning context in ChromaDB: {e}")
    
    def _store_local_learning(self, url: str, purpose: str, extracted_data: Dict[str, Any], context: Dict[str, Any]):
        """Store learning data in local memory"""
        
        try:
            domain = urlparse(url).netloc
            context_key = f"{domain}_{purpose}"
            
            if context_key not in self.context_memory:
                self.context_memory[context_key] = {
                    "extraction_count": 0,
                    "patterns": {
                        "common_fields": [],
                        "success_indicators": []
                    }
                }
            
            memory = self.context_memory[context_key]
            memory["extraction_count"] += 1
            
            # Update patterns
            memory["patterns"]["common_fields"].extend(extracted_data.keys())
            memory["patterns"]["success_indicators"].extend(
                self._identify_success_indicators(extracted_data)
            )
            
            # Keep only recent patterns (last 20 extractions worth)
            if memory["extraction_count"] > 20:
                memory["patterns"]["common_fields"] = memory["patterns"]["common_fields"][-100:]
                memory["patterns"]["success_indicators"] = memory["patterns"]["success_indicators"][-50:]
            
        except Exception as e:
            self.logger.warning(f"Failed to store local learning context: {e}")
    
    def _identify_success_indicators(self, extracted_data: Dict[str, Any]) -> List[str]:
        """Identify indicators that suggest successful extraction"""
        
        indicators = []
        
        # Field completeness indicators
        if len(extracted_data) >= 5:
            indicators.append("high_field_count")
        
        # Contact information indicators
        contact_fields = ["email", "phone", "address", "contact_email", "telephone"]
        if any(field in extracted_data for field in contact_fields):
            indicators.append("contact_info_present")
        
        # Content quality indicators
        for key, value in extracted_data.items():
            if isinstance(value, str) and len(value) > 50:
                indicators.append("detailed_text_content")
                break
        
        # Array data indicators
        for key, value in extracted_data.items():
            if isinstance(value, list) and len(value) > 2:
                indicators.append("multiple_items_found")
                break
        
        return indicators
    
    def get_context_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored context and learning"""
        
        total_contexts = len(self.context_memory)
        total_extractions = sum(
            context.get("extraction_count", 0) 
            for context in self.context_memory.values()
        )
        
        # Get most active domains
        active_domains = sorted(
            self.context_memory.items(),
            key=lambda x: x[1].get("extraction_count", 0),
            reverse=True
        )[:5]
        
        return {
            "total_domain_contexts": total_contexts,
            "total_extractions_learned": total_extractions,
            "chromadb_available": self.chromadb_manager is not None,
            "most_active_domains": [
                {
                    "domain_purpose": domain,
                    "extraction_count": data.get("extraction_count", 0)
                }
                for domain, data in active_domains
            ]
        }
    
    def clear_local_context(self, domain: str = None, purpose: str = None):
        """Clear stored context data"""
        
        if domain and purpose:
            # Clear specific domain-purpose combination
            context_key = f"{domain}_{purpose}"
            if context_key in self.context_memory:
                del self.context_memory[context_key]
        elif domain:
            # Clear all contexts for a domain
            keys_to_remove = [
                key for key in self.context_memory.keys() 
                if key.startswith(f"{domain}_")
            ]
            for key in keys_to_remove:
                del self.context_memory[key]
        else:
            # Clear all context
            self.context_memory.clear()
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Context-aware strategy has higher confidence when context is available"""
        
        base_confidence = super().get_confidence_score(url, html_content, purpose)
        
        # Check if we have domain context
        try:
            domain = urlparse(url).netloc
            context_key = f"{domain}_{purpose}"
            
            if context_key in self.context_memory:
                extraction_count = self.context_memory[context_key].get("extraction_count", 0)
                if extraction_count >= 2:
                    # Boost confidence based on learning
                    learning_bonus = min(extraction_count * 0.02, 0.15)
                    base_confidence += learning_bonus
        except Exception:
            pass
        
        return min(base_confidence, 1.0)
