#!/usr/bin/env python3
"""
AI-Enhanced Strategy
Advanced AI-powered extraction strategy that leverages multiple AI capabilities
including content understanding, selector optimization, and intelligent data validation
"""

import asyncio
import time
import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from dataclasses import dataclass
from bs4 import BeautifulSoup
import re

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType
from ai_core.core.hybrid_ai_service import HybridAIService
from services.vector_service import VectorService
from .ai_enhanced_helpers import AIEnhancedHelpers

logger = logging.getLogger("ai_enhanced")

@dataclass
class AIEnhancementConfig:
    """Configuration for AI enhancement features"""
    enable_content_understanding: bool = True
    enable_selector_optimization: bool = True
    enable_data_validation: bool = True
    enable_semantic_extraction: bool = True
    enable_schema_inference: bool = True
    confidence_threshold: float = 0.6
    max_ai_attempts: int = 3
    temperature: float = 0.3
    enable_caching: bool = True

@dataclass
class AIExtractionPlan:
    """AI-generated extraction plan"""
    extraction_approach: str
    confidence: float
    css_selectors: Dict[str, List[str]]
    fallback_selectors: Dict[str, List[str]]
    extraction_instructions: Dict[str, str]
    validation_rules: Dict[str, Any]
    expected_schema: Dict[str, Any]

class AIEnhancedStrategy(BaseExtractionStrategy):
    """
    Advanced AI-powered extraction strategy that uses multiple AI capabilities
    to understand content, optimize selectors, and validate extracted data
    """
    
    def __init__(self, llm_service: HybridAIService,
                 vector_service: VectorService = None,
                 config: AIEnhancementConfig = None, **kwargs):
        super().__init__(strategy_type=StrategyType.HYBRID, **kwargs)
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.config = config or AIEnhancementConfig()
        
        # Caching for optimization
        self.extraction_cache = {}
        self.selector_cache = {}
        self.schema_cache = {}
        
        # Performance tracking
        self.ai_performance_stats = {
            "extractions_performed": 0,
            "successful_extractions": 0,
            "ai_improvements_applied": 0,
            "schema_inferences": 0,
            "selector_optimizations": 0
        }
    
    async def extract(self, url: str, html_content: str, purpose: str, 
                      context: Dict[str, Any] = None) -> StrategyResult:
        """Execute AI-enhanced extraction"""
        
        start_time = time.time()
        context = context or {}
        
        try:
            # Step 1: AI Content Understanding
            content_analysis = await self._ai_content_understanding(url, html_content, purpose)
            
            # Step 2: Generate AI Extraction Plan
            extraction_plan = await self._generate_ai_extraction_plan(
                content_analysis, purpose, context
            )
            
            # Step 3: Execute Enhanced Extraction
            extraction_result = await self._execute_ai_enhanced_extraction(
                url, html_content, extraction_plan, context
            )
            
            # Step 4: AI Data Validation and Enhancement
            if self.config.enable_data_validation and extraction_result:
                extraction_result = await AIEnhancedHelpers.ai_validate_and_enhance_data(
                    self.llm_service, extraction_result, extraction_plan, purpose, self.config
                )
            
            # Step 5: Calculate AI-enhanced confidence
            confidence = self._calculate_ai_confidence(
                extraction_result, extraction_plan, content_analysis
            )
            
            # Update performance stats
            self.ai_performance_stats["extractions_performed"] += 1
            if extraction_result:
                self.ai_performance_stats["successful_extractions"] += 1
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(extraction_result),
                extracted_data=extraction_result or {},
                confidence_score=confidence,
                strategy_used="AIEnhancedStrategy",
                execution_time=execution_time,
                metadata={
                    "content_analysis": content_analysis,
                    "extraction_plan": {
                        "approach": extraction_plan.extraction_approach,
                        "confidence": extraction_plan.confidence,
                        "ai_selectors_used": len(extraction_plan.css_selectors),
                        "validation_rules": len(extraction_plan.validation_rules)
                    },
                    "ai_enhancements_applied": self._count_ai_enhancements(extraction_plan),
                    "schema_inferred": bool(extraction_plan.expected_schema)
                }
            )
            
        except Exception as e:
            logger.error(f"AI-enhanced extraction failed: {e}")
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="AIEnhancedStrategy",
                execution_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _ai_content_understanding(self, url: str, html_content: str, 
                                       purpose: str) -> Dict[str, Any]:
        """Use AI to understand content structure and context"""
        
        # Check cache first
        cache_key = f"content_{hash(url + purpose)}"
        if self.config.enable_caching and cache_key in self.extraction_cache:
            return self.extraction_cache[cache_key]
        
        try:
            # Create content summary for AI analysis
            content_summary = self._create_content_summary(html_content)
            
            analysis_prompt = f"""
Perform deep content analysis for web extraction:

URL: {url}
Purpose: {purpose}
Content Summary: {content_summary}

Analyze and provide:
1. Content type and structure
2. Data organization patterns
3. Key content areas and their characteristics
4. Potential extraction challenges
5. Recommended extraction approach
6. Data validation requirements

Focus on understanding the semantic structure and optimal extraction strategy.
"""
            
            schema = {
                "type": "object",
                "properties": {
                    "content_type": {"type": "string"},
                    "structure_complexity": {"type": "string", "enum": ["low", "medium", "high"]},
                    "data_patterns": {"type": "array", "items": {"type": "string"}},
                    "key_content_areas": {"type": "array", "items": {"type": "string"}},
                    "extraction_challenges": {"type": "array", "items": {"type": "string"}},
                    "recommended_approach": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "semantic_elements": {"type": "object"},
                    "data_quality_indicators": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["content_type", "structure_complexity", "recommended_approach", "confidence"]
            }
            
            analysis = await self.llm_service.generate_structured(
                prompt=analysis_prompt,
                schema=schema
            )
            
            # Cache the result
            if self.config.enable_caching:
                self.extraction_cache[cache_key] = analysis
            
            return analysis
            
        except Exception as e:
            logger.warning(f"AI content understanding failed: {e}")
            return {
                "content_type": "unknown",
                "structure_complexity": "medium",
                "recommended_approach": "css_with_ai_fallback",
                "confidence": 0.5
            }
    
    def _create_content_summary(self, html_content: str) -> str:
        """Create intelligent content summary for AI analysis"""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extract key structural elements
            title = soup.find('title')
            title_text = title.get_text() if title else ""
            
            # Meta information
            meta_description = soup.find('meta', attrs={'name': 'description'})
            description = meta_description.get('content', '') if meta_description else ""
            
            # Main content indicators
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))
            
            # Structured data
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            has_structured_data = len(json_ld_scripts) > 0
            
            # Content statistics
            total_text_length = len(soup.get_text())
            paragraph_count = len(soup.find_all('p'))
            list_count = len(soup.find_all(['ul', 'ol']))
            table_count = len(soup.find_all('table'))
            form_count = len(soup.find_all('form'))
            
            # Create summary
            summary = f"""
Title: {title_text[:100]}
Description: {description[:200]}
Content Length: {total_text_length} characters
Structure: {paragraph_count} paragraphs, {list_count} lists, {table_count} tables, {form_count} forms
Structured Data: {'Yes' if has_structured_data else 'No'}
Main Content Area: {'Identified' if main_content else 'Not clearly identified'}
"""
            
            # Add sample content from main areas
            if main_content:
                sample_text = main_content.get_text()[:300]
                summary += f"\nSample Content: {sample_text}"
            
            return summary.strip()
            
        except Exception as e:
            logger.warning(f"Content summary creation failed: {e}")
            return f"HTML content analysis failed: {str(e)}"
    
    async def _generate_ai_extraction_plan(self, content_analysis: Dict[str, Any],
                                          purpose: str, context: Dict[str, Any]) -> AIExtractionPlan:
        """Generate comprehensive AI extraction plan"""
        
        try:
            # Infer expected schema
            expected_schema = await AIEnhancedHelpers.ai_infer_data_schema(
                self.llm_service, content_analysis, purpose, self.config, self.schema_cache
            )
            
            # Generate optimized selectors
            css_selectors = await AIEnhancedHelpers.ai_generate_css_selectors(
                self.llm_service, content_analysis, purpose, self.config
            )
            
            # Create extraction instructions
            extraction_instructions = await AIEnhancedHelpers.ai_create_extraction_instructions(
                self.llm_service, content_analysis, purpose, expected_schema
            )
            
            # Generate validation rules
            validation_rules = await self._ai_create_validation_rules(expected_schema, purpose)
            
            # Determine extraction approach
            complexity = content_analysis.get("structure_complexity", "medium")
            
            if complexity == "high" or "challenging" in str(content_analysis.get("extraction_challenges", [])):
                extraction_approach = "ai_semantic_primary"
            elif complexity == "low" and css_selectors:
                extraction_approach = "css_primary_ai_enhance"
            else:
                extraction_approach = "balanced_hybrid"
            
            confidence = min(
                content_analysis.get("confidence", 0.5),
                0.9 if css_selectors else 0.6,
                0.8 if expected_schema else 0.5
            )
            
            return AIExtractionPlan(
                extraction_approach=extraction_approach,
                confidence=confidence,
                css_selectors=css_selectors,
                fallback_selectors=await AIEnhancedHelpers.generate_fallback_selectors(css_selectors),
                extraction_instructions=extraction_instructions,
                validation_rules=validation_rules,
                expected_schema=expected_schema
            )
            
        except Exception as e:
            logger.warning(f"AI extraction plan generation failed: {e}")
            return AIExtractionPlan(
                extraction_approach="ai_fallback",
                confidence=0.4,
                css_selectors={},
                fallback_selectors={},
                extraction_instructions={},
                validation_rules={},
                expected_schema={}
            )
    
    async def _ai_create_validation_rules(self, schema: Dict[str, Any], 
                                         purpose: str) -> Dict[str, Any]:
        """Create AI-powered data validation rules"""
        
        try:
            validation_prompt = f"""
Create validation rules for extracted data:

Purpose: {purpose}
Schema: {json.dumps(schema, indent=2)}

Generate validation rules including:
1. Format validation (email, phone, URL, etc.)
2. Content validation (length, patterns, etc.)
3. Consistency checks
4. Required field validation

Return practical validation rules for data quality assurance.
"""
            
            validation_schema = {
                "type": "object",
                "properties": {
                    "validation_rules": {
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "properties": {
                                "format": {"type": "string"},
                                "pattern": {"type": "string"},
                                "min_length": {"type": "number"},
                                "max_length": {"type": "number"},
                                "required": {"type": "boolean"}
                            }
                        }
                    }
                },
                "required": ["validation_rules"]
            }
            
            result = await self.llm_service.generate_structured(
                prompt=validation_prompt,
                schema=validation_schema
            )
            
            return result.get("validation_rules", {})
            
        except Exception as e:
            logger.warning(f"Validation rule creation failed: {e}")
            return {}
    
    async def _execute_ai_enhanced_extraction(self, url: str, html_content: str,
                                            plan: AIExtractionPlan, 
                                            context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute extraction using AI-enhanced plan"""
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            return await AIEnhancedHelpers.execute_ai_enhanced_extraction(
                soup, html_content, plan, self.llm_service, self.config, context
            )
            
        except Exception as e:
            logger.error(f"AI-enhanced extraction execution failed: {e}")
            return {}
    
    def _calculate_ai_confidence(self, extracted_data: Dict[str, Any],
                                plan: AIExtractionPlan, content_analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for AI-enhanced extraction"""
        
        base_confidence = plan.confidence
        
        # Data quality bonus
        if extracted_data:
            data_completeness = min(len(extracted_data) / max(len(plan.expected_schema.get('fields', {})), 1), 1.0)
            base_confidence += data_completeness * 0.15
        
        # AI enhancement bonus
        ai_enhancements = self._count_ai_enhancements(plan)
        enhancement_bonus = min(ai_enhancements * 0.05, 0.2)
        base_confidence += enhancement_bonus
        
        # Content analysis confidence factor
        content_confidence = content_analysis.get("confidence", 0.5)
        base_confidence = (base_confidence + content_confidence) / 2
        
        return min(base_confidence, 1.0)
    
    def _count_ai_enhancements(self, plan: AIExtractionPlan) -> int:
        """Count AI enhancements applied"""
        
        count = 0
        if plan.css_selectors:
            count += 1
        if plan.expected_schema:
            count += 1
        if plan.validation_rules:
            count += 1
        if plan.extraction_instructions:
            count += 1
        
        return count
    
    def get_ai_performance_stats(self) -> Dict[str, Any]:
        """Get AI performance statistics"""
        
        stats = self.ai_performance_stats.copy()
        
        if stats["extractions_performed"] > 0:
            stats["success_rate"] = stats["successful_extractions"] / stats["extractions_performed"]
        else:
            stats["success_rate"] = 0.0
        
        stats["ai_enhancement_rate"] = stats.get("ai_improvements_applied", 0) / max(stats["extractions_performed"], 1)
        
        return stats
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """AI-enhanced strategy has high confidence due to multiple AI capabilities"""
        
        # Base confidence for AI enhancement
        base_confidence = 0.75
        
        # Boost based on enabled features
        feature_bonus = 0.0
        if self.config.enable_content_understanding:
            feature_bonus += 0.05
        if self.config.enable_selector_optimization:
            feature_bonus += 0.05
        if self.config.enable_data_validation:
            feature_bonus += 0.05
        if self.config.enable_semantic_extraction:
            feature_bonus += 0.05
        if self.config.enable_schema_inference:
            feature_bonus += 0.05
        
        # Performance bonus based on historical success
        if self.ai_performance_stats["extractions_performed"] > 5:
            success_rate = (self.ai_performance_stats["successful_extractions"] / 
                          self.ai_performance_stats["extractions_performed"])
            performance_bonus = success_rate * 0.1
        else:
            performance_bonus = 0.0
        
        return min(base_confidence + feature_bonus + performance_bonus, 1.0)
    
    def supports_purpose(self, purpose: str) -> bool:
        """AI-enhanced strategy supports all purposes through semantic understanding"""
        return True  # AI can handle any purpose through semantic understanding
    
    def clear_cache(self):
        """Clear all caches"""
        self.extraction_cache.clear()
        self.selector_cache.clear()
        self.schema_cache.clear()
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache usage statistics"""
        return {
            "extraction_cache_size": len(self.extraction_cache),
            "selector_cache_size": len(self.selector_cache),
            "schema_cache_size": len(self.schema_cache),
            "caching_enabled": self.config.enable_caching
        }
