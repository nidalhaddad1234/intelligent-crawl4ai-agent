#!/usr/bin/env python3
"""
Multi-Pass LLM Strategy
Multi-pass LLM strategy that extracts in multiple phases for maximum accuracy
"""

import time
import json
import logging
from typing import Dict, Any, List, Optional

from .adaptive_learning import AdaptiveLLMStrategy
from core.base_strategy import StrategyResult

class MultiPassLLMStrategy(AdaptiveLLMStrategy):
    """
    Multi-pass LLM strategy that extracts in multiple phases for maximum accuracy
    
    Examples:
    - First pass: identify content structure and key sections
    - Second pass: extract detailed information from identified sections
    - Third pass: validate and enrich extracted data
    """
    
    def __init__(self, ollama_client, chromadb_manager=None, **kwargs):
        super().__init__(ollama_client, chromadb_manager, **kwargs)
        self.pass_count = 3
        self.enable_structure_analysis = True
        self.enable_validation_pass = True
    
    async def extract(self, url: str, html_content: str, purpose: str, context: Dict[str, Any] = None) -> StrategyResult:
        start_time = time.time()
        
        try:
            extraction_phases = []
            
            # Pass 1: Structure Analysis
            structure_data = {}
            if self.enable_structure_analysis:
                structure_data = await self._pass_1_structure_analysis(url, html_content, purpose)
                extraction_phases.append({"phase": "structure", "success": bool(structure_data)})
            
            # Pass 2: Detailed Extraction
            detailed_data = await self._pass_2_detailed_extraction(
                url, html_content, purpose, structure_data, context
            )
            extraction_phases.append({"phase": "extraction", "success": bool(detailed_data)})
            
            # Pass 3: Validation and Enrichment
            final_data = detailed_data
            if self.enable_validation_pass and detailed_data:
                final_data = await self._pass_3_validation_enrichment(
                    url, html_content, purpose, detailed_data
                )
                extraction_phases.append({"phase": "validation", "success": bool(final_data)})
            
            # Calculate overall confidence
            confidence = self._calculate_multipass_confidence(structure_data, detailed_data, final_data)
            
            execution_time = time.time() - start_time
            
            return StrategyResult(
                success=bool(final_data),
                extracted_data=final_data,
                confidence_score=confidence,
                strategy_used="MultiPassLLMStrategy",
                execution_time=execution_time,
                metadata={
                    "passes_completed": len(extraction_phases),
                    "extraction_phases": extraction_phases,
                    "structure_analysis_enabled": self.enable_structure_analysis,
                    "validation_enabled": self.enable_validation_pass,
                    "structure_quality": len(structure_data) if structure_data else 0,
                    "detail_quality": len(detailed_data) if detailed_data else 0,
                    "final_quality": len(final_data) if final_data else 0
                }
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                extracted_data={},
                confidence_score=0.0,
                strategy_used="MultiPassLLMStrategy",
                execution_time=time.time() - start_time,
                metadata={"passes_completed": 0, "error_phase": "initialization"},
                error=str(e)
            )
    
    async def _pass_1_structure_analysis(self, url: str, html_content: str, purpose: str) -> Dict[str, Any]:
        """First pass: analyze content structure and identify key sections"""
        
        cleaned_content = self._prepare_content_for_llm(html_content)
        
        structure_prompt = f"""
Analyze this webpage content and identify the structure and key sections relevant to: {purpose}

URL: {url}
Purpose: {purpose}

CONTENT (First 4000 chars for analysis):
{cleaned_content[:4000]}

Your task is to identify and categorize the webpage structure for optimal data extraction.

Analyze and return:
1. Overall page type and purpose
2. Main content sections and their roles
3. Navigation and header information areas
4. Contact or business information locations
5. Special content areas (forms, testimonials, features, etc.)
6. Content organization patterns

Return JSON with comprehensive structure analysis:
{{
    "page_type": "corporate|product|news|directory|profile|landing|other",
    "content_organization": "single_column|multi_column|grid|sections|mixed",
    "main_sections": [
        {{"name": "section_name", "purpose": "section_purpose", "importance": "high|medium|low"}}
    ],
    "contact_areas": ["header", "footer", "sidebar", "dedicated_page"],
    "navigation_structure": ["main_nav", "breadcrumbs", "sidebar_nav"],
    "key_content_indicators": ["heading_patterns", "content_types"],
    "extraction_targets": [
        {{"area": "target_area", "priority": "high|medium|low", "content_type": "text|contact|structured"}}
    ],
    "content_complexity": "simple|moderate|complex",
    "recommended_approach": "direct|sectioned|comprehensive"
}}

Focus on providing actionable insights for the extraction phase.
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=structure_prompt,
                format="json",
                temperature=0.2  # Low temperature for consistent structure analysis
            )
            
            structure_data = json.loads(response)
            
            # Validate structure data
            if isinstance(structure_data, dict) and "page_type" in structure_data:
                return structure_data
            else:
                self.logger.warning("Structure analysis returned invalid format")
                return {}
            
        except Exception as e:
            self.logger.warning(f"Structure analysis failed: {e}")
            return {}
    
    async def _pass_2_detailed_extraction(self, url: str, html_content: str, purpose: str, 
                                        structure_data: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Second pass: detailed extraction using structure insights"""
        
        cleaned_content = self._prepare_content_for_llm(html_content)
        
        # Use structure data to guide extraction
        extraction_targets = structure_data.get("extraction_targets", [])
        page_type = structure_data.get("page_type", "unknown")
        content_complexity = structure_data.get("content_complexity", "moderate")
        recommended_approach = structure_data.get("recommended_approach", "comprehensive")
        
        # Get appropriate schema
        schema = self.purpose_schemas.get(purpose, self._get_generic_schema())
        
        # Create context-aware extraction prompt
        context_info = ""
        if context:
            context_info = f"\nAdditional Context: {json.dumps(context, indent=2)}"
        
        structure_guidance = ""
        if structure_data:
            structure_guidance = f"""
STRUCTURE INSIGHTS:
- Page Type: {page_type}
- Content Complexity: {content_complexity}
- Recommended Approach: {recommended_approach}
- Extraction Targets: {json.dumps(extraction_targets, indent=2)}
"""
        
        detailed_prompt = f"""
Based on the structure analysis, perform detailed extraction for: {purpose}

URL: {url}
{context_info}

{structure_guidance}

WEBPAGE CONTENT:
{cleaned_content}

EXTRACTION STRATEGY:
1. Use the structure insights to focus on high-priority areas
2. Apply the recommended approach ({recommended_approach})
3. Pay special attention to extraction targets with "high" priority
4. Adapt extraction depth based on content complexity ({content_complexity})
5. Extract comprehensive information while maintaining accuracy

EXTRACTION SCHEMA:
{json.dumps(schema, indent=2)}

FOCUSED EXTRACTION INSTRUCTIONS:
- For high-priority areas: Extract all available relevant information
- For medium-priority areas: Extract key information and details
- For low-priority areas: Extract basic information if clearly present
- Maintain data quality standards throughout
- Use the page type context ({page_type}) to guide extraction expectations

Return detailed extracted data following the schema exactly.
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=detailed_prompt,
                format="json",
                temperature=0.3  # Balanced temperature for detailed extraction
            )
            
            extracted_data = json.loads(response)
            
            # Validate extracted data against schema
            if self._validate_extraction_schema(extracted_data, schema):
                return extracted_data
            else:
                self.logger.warning("Detailed extraction failed schema validation")
                return {}
            
        except Exception as e:
            self.logger.warning(f"Detailed extraction failed: {e}")
            return {}
    
    async def _pass_3_validation_enrichment(self, url: str, html_content: str, 
                                          purpose: str, detailed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Third pass: validate and enrich extracted data"""
        
        if not detailed_data:
            return {}
        
        # Create validation and enrichment prompt
        validation_prompt = f"""
Validate and enrich this extracted data for quality, accuracy, and completeness.

URL: {url}
Purpose: {purpose}

EXTRACTED DATA TO VALIDATE:
{json.dumps(detailed_data, indent=2)}

VALIDATION AND ENRICHMENT TASKS:

1. DATA QUALITY VALIDATION:
   - Check for consistency and logical coherence
   - Validate format of emails, phone numbers, URLs, dates
   - Ensure all information appears factually correct
   - Remove any obviously incorrect or fabricated information

2. COMPLETENESS ENHANCEMENT:
   - Identify missing information that should be present for: {purpose}
   - Fill gaps with additional context where appropriate
   - Ensure all required fields for the purpose are addressed

3. FORMAT STANDARDIZATION:
   - Standardize date formats (YYYY-MM-DD when possible)
   - Normalize phone number formats
   - Clean and standardize address formats
   - Ensure consistent capitalization and formatting

4. ACCURACY VERIFICATION:
   - Cross-reference information for internal consistency
   - Verify that extracted information makes sense in context
   - Flag any potentially inaccurate information

5. ENRICHMENT:
   - Add clarifying context where helpful
   - Enhance incomplete information where possible
   - Provide additional relevant details if clearly derivable

IMPORTANT GUIDELINES:
- Only include information you are confident is accurate
- Maintain the original data structure and schema
- Mark any uncertain information clearly
- Prioritize accuracy over completeness
- Do not fabricate or guess missing information

Return the validated and enriched data in the same structure.
"""
        
        try:
            response = await self.ollama_client.generate(
                model="llama3.1",
                prompt=validation_prompt,
                format="json",
                temperature=0.1  # Very low temperature for validation accuracy
            )
            
            validated_data = json.loads(response)
            
            # Apply additional post-processing
            final_data = self._post_process_extraction(validated_data, purpose)
            
            # Ensure we didn't lose critical information during validation
            if len(final_data) < len(detailed_data) * 0.7:
                self.logger.warning("Validation pass removed too much data, using detailed extraction")
                return self._post_process_extraction(detailed_data, purpose)
            
            return final_data
            
        except Exception as e:
            self.logger.warning(f"Validation pass failed: {e}")
            # Return original data with basic post-processing if validation fails
            return self._post_process_extraction(detailed_data, purpose)
    
    def _calculate_multipass_confidence(self, structure_data: Dict[str, Any], 
                                      detailed_data: Dict[str, Any], 
                                      final_data: Dict[str, Any]) -> float:
        """Calculate confidence based on multi-pass results"""
        
        # Base confidence
        base_confidence = 0.4
        
        # Structure analysis contribution
        if structure_data:
            structure_quality = len(structure_data)
            structure_score = min(structure_quality * 0.02, 0.15)
            base_confidence += structure_score
            
            # Bonus for detailed structure analysis
            if structure_data.get("extraction_targets") and structure_data.get("page_type"):
                base_confidence += 0.1
        
        # Detailed extraction contribution
        if detailed_data:
            detail_quality = len(detailed_data)
            detail_score = min(detail_quality * 0.03, 0.2)
            base_confidence += detail_score
        
        # Final data quality contribution
        if final_data:
            final_quality = len(final_data)
            final_score = min(final_quality * 0.03, 0.2)
            base_confidence += final_score
            
            # Bonus for rich final data
            if final_quality >= 5:
                base_confidence += 0.05
        
        # Multi-pass validation bonus
        if structure_data and detailed_data and final_data:
            base_confidence += 0.15  # Multiple passes increase reliability
        
        return min(base_confidence, 1.0)
    
    def configure_passes(self, enable_structure: bool = True, enable_validation: bool = True):
        """Configure which passes to enable"""
        self.enable_structure_analysis = enable_structure
        self.enable_validation_pass = enable_validation
    
    def get_pass_configuration(self) -> Dict[str, Any]:
        """Get current pass configuration"""
        return {
            "total_passes": self.pass_count,
            "structure_analysis_enabled": self.enable_structure_analysis,
            "validation_pass_enabled": self.enable_validation_pass,
            "effective_passes": (
                1 +  # Always do detailed extraction
                (1 if self.enable_structure_analysis else 0) +
                (1 if self.enable_validation_pass else 0)
            )
        }
    
    def get_confidence_score(self, url: str, html_content: str, purpose: str) -> float:
        """Multi-pass strategy has higher confidence due to validation"""
        base_confidence = super().get_confidence_score(url, html_content, purpose)
        
        # Multi-pass bonus
        multipass_bonus = 0.1
        
        # Additional bonus based on enabled passes
        if self.enable_structure_analysis:
            multipass_bonus += 0.05
        if self.enable_validation_pass:
            multipass_bonus += 0.05
        
        return min(base_confidence + multipass_bonus, 1.0)
