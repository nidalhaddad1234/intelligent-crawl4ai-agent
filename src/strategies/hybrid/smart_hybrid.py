#!/usr/bin/env python3
"""
Smart Hybrid Strategy
Intelligent hybrid that dynamically chooses the best combination of CSS and LLM
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from bs4 import BeautifulSoup

from core.base_strategy import BaseExtractionStrategy, StrategyResult, StrategyType

class SmartHybridStrategy(BaseExtractionStrategy):
    """
    Intelligent hybrid that dynamically chooses the best combination of CSS and LLM
    
    Examples:
    - Analyze page structure to determine optimal extraction approach
    - Use CSS for structured sections, LLM for complex content
    - Automatically adapt strategy based on content type
    """
    
    def __init__(self, ollama_client, **kwargs):
        super().__init__(strategy_type=StrategyType.HYBRID, **kwargs)
        self.ollama_client = ollama_client
        
        # Initialize component strategies (would need to import these)
        self.css_strategies = {}
        self.llm_strategy = None
        self._initialize_component_strategies()
    
    def _initialize_component_strategies(self):
        """Initialize component strategies (placeholder for now)"""
        # This would be populated with actual strategy instances
        # For now, using placeholders to maintain structure
        self.css_strategies = {
            "directory": None,  # DirectoryCSSStrategy(),
            "ecommerce": None,  # EcommerceCSSStrategy(),
            "news": None        # NewsCSSStrategy()
        }
        # self.llm_strategy = IntelligentLLMStrategy(self.ollama_client)
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            # Phase 1: Analyze content to determine optimal strategy mix
            strategy_plan = await self._analyze_and_plan_extraction(url, html_content, purpose)
            
            # Phase 2: Execute planned extraction
            extraction_results = await self._execute_strategy_plan(url, html_content, purpose, strategy_plan, context)
            
            # Phase 3: Merge and validate results
            final_data = self._merge_strategy_results(extraction_results, purpose)
            
            confidence = self._calculate_smart_hybrid_confidence(extraction_results, strategy_plan)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(final_data),
                extracted_data=final_data,
                confidence_score=confidence,
                strategy_used="SmartHybridStrategy",
                execution_time=execution_time,
                metadata={
                    "strategy_plan": strategy_plan,
                    "strategies_used": list(extraction_results.keys()),
                    "plan_confidence": strategy_plan.get("confidence", 0.5)
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="SmartHybridStrategy",
                execution_time=time.time() - start_time,
                metadata={},
                error=str(e)
            )
    
    async def _analyze_and_plan_extraction(self, url: str, html_content: str, purpose: str) -> Dict[str, Any]:
        """Analyze content and create extraction strategy plan"""
        
        analysis_prompt = f"""
Analyze this webpage and create an optimal extraction strategy plan.

URL: {url}
Purpose: {purpose}

Content Analysis (first 3000 chars):
{html_content[:3000]}

Determine:
1. Content structure type (directory, e-commerce, news, corporate, etc.)
2. Best extraction approach for each section
3. Whether to use CSS selectors, LLM extraction, or both
4. Confidence in recommended approach

Return JSON plan:
{{
    "content_type": "directory|ecommerce|news|corporate|social|other",
    "complexity": "low|medium|high",
    "recommended_strategies": {{
        "primary": "css|llm|hybrid",
        "secondary": "css|llm|none",
        "css_areas": ["area1", "area2"],
        "llm_areas": ["area1", "area2"]
    }},
    "confidence": 0.8,
    "reasoning": "explanation of strategy choice"
}}
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=analysis_prompt,
                format="json",
                temperature=0.2
            )
            
            return json.loads(response)
            
        except Exception as e:
            self.logger.warning(f"Strategy planning failed: {e}")
            # Return default plan
            return {
                "content_type": "corporate",
                "complexity": "medium",
                "recommended_strategies": {
                    "primary": "hybrid",
                    "secondary": "llm",
                    "css_areas": ["contact", "basic_info"],
                    "llm_areas": ["content", "complex_info"]
                },
                "confidence": 0.5,
                "reasoning": "Default hybrid approach due to analysis failure"
            }
    
    async def _execute_strategy_plan(self, url: str, html_content: str, purpose: str, 
                                   strategy_plan: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute the planned extraction strategies"""
        
        results = {}
        recommended = strategy_plan.get("recommended_strategies", {})
        content_type = strategy_plan.get("content_type", "corporate")
        
        # Execute primary strategy
        primary_strategy = recommended.get("primary", "hybrid")
        
        if primary_strategy == "css" or primary_strategy == "hybrid":
            # Execute appropriate CSS strategy
            css_result = await self._execute_css_strategy(url, html_content, purpose, content_type)
            if css_result and css_result.get("success"):
                results["css"] = css_result.get("extracted_data", {})
        
        if primary_strategy == "llm" or primary_strategy == "hybrid":
            # Execute LLM strategy
            llm_result = await self._execute_llm_strategy(url, html_content, purpose, context)
            if llm_result and llm_result.get("success"):
                results["llm"] = llm_result.get("extracted_data", {})
        
        # Execute secondary strategy if primary didn't provide enough data
        if len(results) == 0 or self._needs_secondary_strategy(results, purpose):
            secondary_strategy = recommended.get("secondary", "none")
            
            if secondary_strategy == "css" and "css" not in results:
                css_result = await self._execute_css_strategy(url, html_content, purpose, content_type)
                if css_result and css_result.get("success"):
                    results["css_secondary"] = css_result.get("extracted_data", {})
            
            elif secondary_strategy == "llm" and "llm" not in results:
                llm_result = await self._execute_llm_strategy(url, html_content, purpose, context)
                if llm_result and llm_result.get("success"):
                    results["llm_secondary"] = llm_result.get("extracted_data", {})
        
        return results
    
    async def _execute_css_strategy(self, url: str, html_content: str, purpose: str, content_type: str) -> Optional[Dict[str, Any]]:
        """Execute appropriate CSS strategy based on content type"""
        
        # For now, return a basic CSS extraction since we don't have the full strategies imported
        # In the full implementation, this would use the actual CSS strategies
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            basic_data = {}
            
            # Basic extraction patterns
            title_element = soup.find('h1') or soup.find('title')
            if title_element:
                basic_data['title'] = title_element.get_text(strip=True)
            
            # Look for contact information
            phone_elements = soup.select('a[href^="tel:"], .phone, .telephone')
            for elem in phone_elements:
                phone = elem.get('href', '').replace('tel:', '') or elem.get_text(strip=True)
                if phone:
                    basic_data['phone'] = phone
                    break
            
            email_elements = soup.select('a[href^="mailto:"]')
            for elem in email_elements:
                email = elem.get('href', '').replace('mailto:', '')
                if email:
                    basic_data['email'] = email
                    break
            
            return {
                "success": bool(basic_data),
                "extracted_data": basic_data
            }
            
        except Exception as e:
            self.logger.warning(f"CSS strategy execution failed: {e}")
            return {"success": False, "extracted_data": {}}
    
    async def _execute_llm_strategy(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Execute LLM strategy"""
        
        if not self.ollama_client:
            return {"success": False, "extracted_data": {}}
        
        # Simplified LLM extraction
        extraction_prompt = f"""
Extract relevant information from this webpage for the purpose: {purpose}

URL: {url}
Content (first 4000 chars):
{html_content[:4000]}

Extract and return JSON with relevant fields for: {purpose}
Focus on finding key information like names, contact details, descriptions, etc.

Return clean JSON:
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=extraction_prompt,
                format="json",
                temperature=0.3
            )
            
            extracted_data = json.loads(response)
            return {
                "success": isinstance(extracted_data, dict) and bool(extracted_data),
                "extracted_data": extracted_data if isinstance(extracted_data, dict) else {}
            }
            
        except Exception as e:
            self.logger.warning(f"LLM strategy execution failed: {e}")
            return {"success": False, "extracted_data": {}}
    
    def _needs_secondary_strategy(self, results: Dict[str, Any], purpose: str) -> bool:
        """Determine if secondary strategy is needed"""
        
        # Check if we have sufficient data for the purpose
        min_fields = {
            "company_info": 3,
            "contact_discovery": 2,
            "product_data": 2,
            "news_content": 2
        }
        
        required_fields = min_fields.get(purpose, 2)
        
        for strategy_result in results.values():
            if isinstance(strategy_result, dict) and len(strategy_result) >= required_fields:
                return False  # We have sufficient data
        
        return True  # Need more data
    
    def _merge_strategy_results(self, results: Dict[str, Any], purpose: str) -> Dict[str, Any]:
        """Merge results from multiple strategies"""
        
        merged = {}
        
        # Priority order: CSS (most reliable) -> LLM (most comprehensive)
        strategy_priority = ["css", "llm", "css_secondary", "llm_secondary"]
        
        for strategy in strategy_priority:
            if strategy in results:
                data = results[strategy]
                if isinstance(data, dict):
                    # Merge data, giving priority to existing values
                    for key, value in data.items():
                        if key not in merged and value and str(value).strip():
                            merged[key] = value
        
        return merged
    
    def _calculate_smart_hybrid_confidence(self, results: Dict[str, Any], strategy_plan: Dict[str, Any]) -> float:
        """Calculate confidence based on strategy plan execution"""
        
        base_confidence = strategy_plan.get("confidence", 0.5)
        
        # Execution bonus
        if len(results) > 1:
            base_confidence += 0.15  # Multiple strategies provide validation
        elif len(results) == 1:
            base_confidence += 0.05
        
        # Data quality bonus
        total_fields = sum(len(data) if isinstance(data, dict) else 0 for data in results.values())
        if total_fields > 5:
            base_confidence += 0.1
        elif total_fields > 3:
            base_confidence += 0.05
        
        return min(base_confidence, 1.0)
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Smart hybrid has high confidence due to adaptive approach"""
        return 0.8  # High confidence due to intelligent adaptation
    
    def supports_purpose(self, purpose: str) -> bool:
        """Smart hybrid supports all purposes"""
        return True
