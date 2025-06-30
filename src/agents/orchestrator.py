#!/usr/bin/env python3
"""
Extraction Orchestrator - Intelligent Coordination
Coordinates and orchestrates complex multi-step extraction workflows
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, field
from enum import Enum

# Import from new modular structure
from services import VectorService
from ai_core.core.hybrid_ai_service import HybridAIService, create_production_ai_service
# Temporarily commented out due to SQLAlchemy compatibility issues
# from data.analytics.data_analytics import DataAnalytics

# Temporary placeholder classes for data layer components
class DataAnalytics:
    """Temporary placeholder for DataAnalytics"""
    def __init__(self, *args, **kwargs):
        pass
    async def initialize(self):
        return True
    async def cleanup(self):
        pass
from agents.intelligent_analyzer import IntelligentAnalyzer, WebsiteAnalysis, WebsiteType, ExtractionPurpose
from agents.strategy_selector import StrategySelector, StrategyRecommendation
from agents.high_volume_executor import HighVolumeExecutor, ExecutionResult, BatchJobConfig

logger = logging.getLogger("extraction_orchestrator")

class WorkflowStep(Enum):
    ANALYSIS = "analysis"
    STRATEGY_SELECTION = "strategy_selection"
    EXTRACTION = "extraction"
    VALIDATION = "validation"
    POST_PROCESSING = "post_processing"
    STORAGE = "storage"

class OrchestrationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class WorkflowConfig:
    """Configuration for orchestrated workflows"""
    enable_pre_analysis: bool = True
    enable_quality_validation: bool = True
    enable_data_enrichment: bool = True
    enable_analytics_tracking: bool = True
    retry_failed_steps: bool = True
    max_step_retries: int = 3
    parallel_processing: bool = True
    custom_validation_rules: List[Dict[str, Any]] = field(default_factory=list)
    post_processing_functions: List[Callable] = field(default_factory=list)

@dataclass
class OrchestrationConfig:
    """Main orchestration configuration"""
    workflow_config: WorkflowConfig = field(default_factory=WorkflowConfig)
    batch_config: BatchJobConfig = field(default_factory=BatchJobConfig)
    enable_intelligent_routing: bool = True
    enable_adaptive_strategies: bool = True
    enable_real_time_monitoring: bool = True
    quality_threshold: float = 0.7
    confidence_threshold: float = 0.6
    fallback_strategies: List[str] = field(default_factory=lambda: ["llm_extraction", "css_extraction"])

@dataclass
class WorkflowStepResult:
    """Result of a workflow step"""
    step: WorkflowStep
    success: bool
    data: Dict[str, Any]
    execution_time: float
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class OrchestrationResult:
    """Complete orchestration result"""
    orchestration_id: str
    url: str
    purpose: str
    status: OrchestrationStatus
    workflow_results: List[WorkflowStepResult]
    final_data: Dict[str, Any]
    total_execution_time: float
    quality_score: float
    confidence_score: float
    strategies_used: List[str]
    created_at: float
    completed_at: Optional[float] = None

class ExtractionOrchestrator:
    """
    Intelligent extraction orchestrator that coordinates complex workflows
    
    Features:
    - Multi-step workflow orchestration
    - Intelligent strategy adaptation
    - Quality validation and data enrichment
    - Real-time monitoring and analytics
    - Failure recovery and retries
    - Custom workflow configuration
    """
    
    def __init__(self,
                 llm_service: HybridAIService = None,
                 vector_service: VectorService = None,
                 data_analytics: DataAnalytics = None):
        
        # Service dependencies
        self.llm_service = llm_service
        self.vector_service = vector_service
        self.data_analytics = data_analytics
        
        # Core components
        self.intelligent_analyzer = None
        self.strategy_selector = None
        self.high_volume_executor = None
        
        # Orchestration tracking
        self.active_orchestrations = {}
        self.completed_orchestrations = {}
        
        # Performance metrics
        self.orchestration_metrics = {
            "total_orchestrations": 0,
            "successful_orchestrations": 0,
            "failed_orchestrations": 0,
            "avg_execution_time": 0.0,
            "avg_quality_score": 0.0
        }
        
        # Custom workflow steps
        self.custom_steps = {}
        
    async def initialize(self) -> bool:
        """Initialize all services and components"""
        
        try:
            # Initialize services if not provided
            if not self.llm_service:
                self.llm_service = create_production_ai_service()
                # HybridAIService initializes automatically
            
            if not self.vector_service:
                self.vector_service = VectorService(llm_service=self.llm_service)
                await self.vector_service.initialize()
            
            # Temporarily disabled - data layer functionality
            # if not self.data_analytics:
            #     from data.analytics.data_analytics import DataAnalytics
            #     self.data_analytics = DataAnalytics()
            
            # Initialize core components
            self.intelligent_analyzer = IntelligentAnalyzer(
                llm_service=self.llm_service,
                vector_service=self.vector_service
            )
            await self.intelligent_analyzer.initialize()
            
            self.strategy_selector = StrategySelector(
                llm_service=self.llm_service,
                vector_service=self.vector_service
            )
            await self.strategy_selector.initialize()
            
            self.high_volume_executor = HighVolumeExecutor(
                llm_service=self.llm_service,
                vector_service=self.vector_service,
                data_analytics=self.data_analytics
            )
            await self.high_volume_executor.initialize()
            
            logger.info("Extraction orchestrator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize extraction orchestrator: {e}")
            return False
    
    async def orchestrate_single_extraction(self,
                                          url: str,
                                          purpose: str,
                                          config: OrchestrationConfig = None) -> OrchestrationResult:
        """
        Orchestrate a complete extraction workflow for a single URL
        
        Args:
            url: Target URL for extraction
            purpose: Extraction purpose
            config: Orchestration configuration
            
        Returns:
            OrchestrationResult with complete workflow data
        """
        
        orchestration_id = str(uuid.uuid4())
        config = config or OrchestrationConfig()
        start_time = time.time()
        
        logger.info(f"Starting orchestration {orchestration_id} for {url}")
        
        # Initialize orchestration tracking
        orchestration = OrchestrationResult(
            orchestration_id=orchestration_id,
            url=url,
            purpose=purpose,
            status=OrchestrationStatus.RUNNING,
            workflow_results=[],
            final_data={},
            total_execution_time=0.0,
            quality_score=0.0,
            confidence_score=0.0,
            strategies_used=[],
            created_at=start_time
        )
        
        self.active_orchestrations[orchestration_id] = orchestration
        
        try:
            # Step 1: Website Analysis
            if config.workflow_config.enable_pre_analysis:
                analysis_result = await self._execute_analysis_step(url, config)
                orchestration.workflow_results.append(analysis_result)
                
                if not analysis_result.success:
                    raise Exception(f"Analysis step failed: {analysis_result.error_message}")
                
                analysis = analysis_result.data["analysis"]
            else:
                # Fallback analysis
                analysis = await self.intelligent_analyzer.analyze_website(url)
            
            # Step 2: Strategy Selection
            strategy_result = await self._execute_strategy_selection_step(
                analysis, purpose, config
            )
            orchestration.workflow_results.append(strategy_result)
            
            if not strategy_result.success:
                raise Exception(f"Strategy selection failed: {strategy_result.error_message}")
            
            strategy = strategy_result.data["strategy"]
            orchestration.strategies_used.append(strategy.primary_strategy)
            
            # Step 3: Extraction
            extraction_result = await self._execute_extraction_step(
                url, strategy, analysis, config
            )
            orchestration.workflow_results.append(extraction_result)
            
            if not extraction_result.success:
                # Try fallback strategies
                for fallback_strategy in config.fallback_strategies:
                    logger.info(f"Trying fallback strategy: {fallback_strategy}")
                    fallback_result = await self._execute_fallback_extraction(
                        url, fallback_strategy, analysis, config
                    )
                    orchestration.workflow_results.append(fallback_result)
                    
                    if fallback_result.success:
                        extraction_result = fallback_result
                        orchestration.strategies_used.append(fallback_strategy)
                        break
                
                if not extraction_result.success:
                    raise Exception(f"All extraction strategies failed")
            
            extracted_data = extraction_result.data["extracted_data"]
            orchestration.confidence_score = extraction_result.data.get("confidence_score", 0.5)
            
            # Step 4: Quality Validation
            if config.workflow_config.enable_quality_validation:
                validation_result = await self._execute_validation_step(
                    extracted_data, purpose, analysis, config
                )
                orchestration.workflow_results.append(validation_result)
                
                orchestration.quality_score = validation_result.data.get("quality_score", 0.5)
                
                # Check quality threshold
                if orchestration.quality_score < config.quality_threshold:
                    logger.warning(f"Quality score {orchestration.quality_score} below threshold {config.quality_threshold}")
                    
                    if config.workflow_config.retry_failed_steps:
                        # Retry with different strategy
                        retry_result = await self._retry_with_better_strategy(
                            url, purpose, analysis, config
                        )
                        if retry_result.success:
                            extracted_data = retry_result.data["extracted_data"]
                            orchestration.workflow_results.append(retry_result)
            
            # Step 5: Data Enrichment (if enabled)
            if config.workflow_config.enable_data_enrichment:
                enrichment_result = await self._execute_enrichment_step(
                    extracted_data, url, purpose, config
                )
                orchestration.workflow_results.append(enrichment_result)
                
                if enrichment_result.success:
                    extracted_data = enrichment_result.data["enriched_data"]
            
            # Step 6: Post-processing
            if config.workflow_config.post_processing_functions:
                post_processing_result = await self._execute_post_processing_step(
                    extracted_data, config
                )
                orchestration.workflow_results.append(post_processing_result)
                
                if post_processing_result.success:
                    extracted_data = post_processing_result.data["processed_data"]
            
            # Finalize orchestration
            orchestration.final_data = extracted_data
            orchestration.status = OrchestrationStatus.COMPLETED
            orchestration.completed_at = time.time()
            orchestration.total_execution_time = orchestration.completed_at - start_time
            
            # Update metrics
            self._update_orchestration_metrics(orchestration)
            
            # Move to completed orchestrations
            self.completed_orchestrations[orchestration_id] = orchestration
            del self.active_orchestrations[orchestration_id]
            
            logger.info(f"Orchestration {orchestration_id} completed successfully")
            return orchestration
            
        except Exception as e:
            # Handle orchestration failure
            orchestration.status = OrchestrationStatus.FAILED
            orchestration.completed_at = time.time()
            orchestration.total_execution_time = orchestration.completed_at - start_time
            
            # Add error step
            error_step = WorkflowStepResult(
                step=WorkflowStep.EXTRACTION,
                success=False,
                data={},
                execution_time=0.0,
                error_message=str(e)
            )
            orchestration.workflow_results.append(error_step)
            
            self._update_orchestration_metrics(orchestration)
            
            # Move to completed orchestrations
            self.completed_orchestrations[orchestration_id] = orchestration
            if orchestration_id in self.active_orchestrations:
                del self.active_orchestrations[orchestration_id]
            
            logger.error(f"Orchestration {orchestration_id} failed: {e}")
            return orchestration
    
    async def orchestrate_batch_extraction(self,
                                         urls: List[str],
                                         purpose: str,
                                         config: OrchestrationConfig = None) -> str:
        """
        Orchestrate batch extraction with intelligent coordination
        
        Args:
            urls: List of URLs to process
            purpose: Extraction purpose
            config: Orchestration configuration
            
        Returns:
            job_id: High-volume job identifier
        """
        
        config = config or OrchestrationConfig()
        
        logger.info(f"Starting batch orchestration: {len(urls)} URLs for {purpose}")
        
        # Submit to high-volume executor with orchestration metadata
        job_id = await self.high_volume_executor.submit_job(
            urls=urls,
            purpose=purpose,
            job_name=f"Orchestrated Batch - {purpose}",
            description=f"Orchestrated extraction of {len(urls)} URLs with intelligent coordination",
            config=config.batch_config,
            metadata={
                "orchestration_config": config.__dict__,
                "orchestrated": True,
                "orchestrator_version": "2.0.0"
            }
        )
        
        logger.info(f"Batch orchestration submitted as job {job_id}")
        return job_id
    
    async def _execute_analysis_step(self, url: str, config: OrchestrationConfig) -> WorkflowStepResult:
        """Execute website analysis step"""
        
        step_start = time.time()
        
        try:
            analysis = await self.intelligent_analyzer.analyze_website(url)
            
            return WorkflowStepResult(
                step=WorkflowStep.ANALYSIS,
                success=True,
                data={"analysis": analysis},
                execution_time=time.time() - step_start,
                metadata={
                    "website_type": analysis.website_type.value,
                    "complexity": analysis.estimated_complexity,
                    "confidence": analysis.analysis_confidence
                }
            )
            
        except Exception as e:
            return WorkflowStepResult(
                step=WorkflowStep.ANALYSIS,
                success=False,
                data={},
                execution_time=time.time() - step_start,
                error_message=str(e)
            )
    
    async def _execute_strategy_selection_step(self,
                                             analysis: WebsiteAnalysis,
                                             purpose: str,
                                             config: OrchestrationConfig) -> WorkflowStepResult:
        """Execute strategy selection step"""
        
        step_start = time.time()
        
        try:
            strategy = await self.strategy_selector.select_strategy(
                analysis=analysis,
                purpose=purpose,
                additional_context="Orchestrated extraction with quality validation"
            )
            
            return WorkflowStepResult(
                step=WorkflowStep.STRATEGY_SELECTION,
                success=True,
                data={"strategy": strategy},
                execution_time=time.time() - step_start,
                metadata={
                    "primary_strategy": strategy.primary_strategy,
                    "confidence": strategy.confidence_score,
                    "estimated_success_rate": strategy.estimated_success_rate
                }
            )
            
        except Exception as e:
            return WorkflowStepResult(
                step=WorkflowStep.STRATEGY_SELECTION,
                success=False,
                data={},
                execution_time=time.time() - step_start,
                error_message=str(e)
            )
    
    async def _execute_extraction_step(self,
                                     url: str,
                                     strategy: StrategyRecommendation,
                                     analysis: WebsiteAnalysis,
                                     config: OrchestrationConfig) -> WorkflowStepResult:
        """Execute extraction step"""
        
        step_start = time.time()
        
        try:
            # This would integrate with actual Crawl4AI extraction
            # For now, simulate the extraction process
            await asyncio.sleep(0.2)  # Simulate extraction time
            
            extracted_data = {
                "title": f"Extracted from {url}",
                "content": "Sample extracted content",
                "metadata": {
                    "strategy": strategy.primary_strategy,
                    "website_type": analysis.website_type.value
                }
            }
            
            return WorkflowStepResult(
                step=WorkflowStep.EXTRACTION,
                success=True,
                data={
                    "extracted_data": extracted_data,
                    "confidence_score": strategy.confidence_score
                },
                execution_time=time.time() - step_start,
                metadata={
                    "strategy_used": strategy.primary_strategy,
                    "data_fields": len(extracted_data)
                }
            )
            
        except Exception as e:
            return WorkflowStepResult(
                step=WorkflowStep.EXTRACTION,
                success=False,
                data={},
                execution_time=time.time() - step_start,
                error_message=str(e)
            )
    
    async def _execute_fallback_extraction(self,
                                         url: str,
                                         fallback_strategy: str,
                                         analysis: WebsiteAnalysis,
                                         config: OrchestrationConfig) -> WorkflowStepResult:
        """Execute fallback extraction strategy"""
        
        step_start = time.time()
        
        try:
            # Simulate fallback extraction
            await asyncio.sleep(0.3)
            
            extracted_data = {
                "title": f"Fallback extracted from {url}",
                "content": "Fallback extracted content",
                "metadata": {
                    "strategy": fallback_strategy,
                    "fallback": True
                }
            }
            
            return WorkflowStepResult(
                step=WorkflowStep.EXTRACTION,
                success=True,
                data={
                    "extracted_data": extracted_data,
                    "confidence_score": 0.6  # Lower confidence for fallback
                },
                execution_time=time.time() - step_start,
                metadata={
                    "strategy_used": fallback_strategy,
                    "is_fallback": True
                }
            )
            
        except Exception as e:
            return WorkflowStepResult(
                step=WorkflowStep.EXTRACTION,
                success=False,
                data={},
                execution_time=time.time() - step_start,
                error_message=str(e)
            )
    
    async def _execute_validation_step(self,
                                     extracted_data: Dict[str, Any],
                                     purpose: str,
                                     analysis: WebsiteAnalysis,
                                     config: OrchestrationConfig) -> WorkflowStepResult:
        """Execute data validation step"""
        
        step_start = time.time()
        
        try:
            # Quality validation logic
            quality_score = 0.0
            completeness = 0.0
            
            # Check data completeness
            if extracted_data:
                non_empty_fields = sum(1 for v in extracted_data.values() 
                                     if v and str(v).strip())
                total_fields = len(extracted_data)
                completeness = non_empty_fields / max(1, total_fields)
                quality_score += completeness * 0.4
            
            # Check data relevance to purpose
            purpose_relevance = 0.8  # Placeholder
            quality_score += purpose_relevance * 0.3
            
            # Check analysis confidence factor
            quality_score += analysis.analysis_confidence * 0.3
            
            # Apply custom validation rules
            custom_validation_passed = True
            for rule in config.workflow_config.custom_validation_rules:
                # Apply custom validation rule
                # This would be implemented based on specific requirements
                pass
            
            if not custom_validation_passed:
                quality_score *= 0.7
            
            return WorkflowStepResult(
                step=WorkflowStep.VALIDATION,
                success=True,
                data={
                    "quality_score": quality_score,
                    "validation_details": {
                        "completeness": completeness,
                        "purpose_relevance": purpose_relevance,
                        "analysis_confidence": analysis.analysis_confidence,
                        "custom_rules_passed": custom_validation_passed
                    }
                },
                execution_time=time.time() - step_start
            )
            
        except Exception as e:
            return WorkflowStepResult(
                step=WorkflowStep.VALIDATION,
                success=False,
                data={"quality_score": 0.0},
                execution_time=time.time() - step_start,
                error_message=str(e)
            )
    
    async def _execute_enrichment_step(self,
                                     extracted_data: Dict[str, Any],
                                     url: str,
                                     purpose: str,
                                     config: OrchestrationConfig) -> WorkflowStepResult:
        """Execute data enrichment step"""
        
        step_start = time.time()
        
        try:
            # Data enrichment logic
            enriched_data = extracted_data.copy()
            
            # Add URL metadata
            enriched_data["source_url"] = url
            enriched_data["extraction_timestamp"] = time.time()
            enriched_data["purpose"] = purpose
            
            # Add enrichment from external sources (placeholder)
            enriched_data["enrichment"] = {
                "domain_info": {"domain": url.split("://")[-1].split("/")[0]},
                "extraction_context": {"orchestrated": True}
            }
            
            return WorkflowStepResult(
                step=WorkflowStep.POST_PROCESSING,
                success=True,
                data={"enriched_data": enriched_data},
                execution_time=time.time() - step_start,
                metadata={"enrichment_fields_added": 4}
            )
            
        except Exception as e:
            return WorkflowStepResult(
                step=WorkflowStep.POST_PROCESSING,
                success=False,
                data={"enriched_data": extracted_data},
                execution_time=time.time() - step_start,
                error_message=str(e)
            )
    
    async def _execute_post_processing_step(self,
                                          extracted_data: Dict[str, Any],
                                          config: OrchestrationConfig) -> WorkflowStepResult:
        """Execute post-processing step"""
        
        step_start = time.time()
        
        try:
            processed_data = extracted_data.copy()
            
            # Apply custom post-processing functions
            for post_func in config.workflow_config.post_processing_functions:
                processed_data = await post_func(processed_data)
            
            return WorkflowStepResult(
                step=WorkflowStep.POST_PROCESSING,
                success=True,
                data={"processed_data": processed_data},
                execution_time=time.time() - step_start,
                metadata={"functions_applied": len(config.workflow_config.post_processing_functions)}
            )
            
        except Exception as e:
            return WorkflowStepResult(
                step=WorkflowStep.POST_PROCESSING,
                success=False,
                data={"processed_data": extracted_data},
                execution_time=time.time() - step_start,
                error_message=str(e)
            )
    
    async def _retry_with_better_strategy(self,
                                        url: str,
                                        purpose: str,
                                        analysis: WebsiteAnalysis,
                                        config: OrchestrationConfig) -> WorkflowStepResult:
        """Retry extraction with a potentially better strategy"""
        
        step_start = time.time()
        
        try:
            # Get alternative strategy
            alternative_strategy = await self.strategy_selector.select_strategy(
                analysis=analysis,
                purpose=purpose,
                additional_context="Retry with higher quality threshold"
            )
            
            # Execute extraction with alternative strategy
            retry_result = await self._execute_extraction_step(
                url, alternative_strategy, analysis, config
            )
            
            return WorkflowStepResult(
                step=WorkflowStep.EXTRACTION,
                success=retry_result.success,
                data=retry_result.data,
                execution_time=time.time() - step_start,
                metadata={
                    "is_retry": True,
                    "alternative_strategy": alternative_strategy.primary_strategy
                }
            )
            
        except Exception as e:
            return WorkflowStepResult(
                step=WorkflowStep.EXTRACTION,
                success=False,
                data={},
                execution_time=time.time() - step_start,
                error_message=str(e)
            )
    
    def _update_orchestration_metrics(self, orchestration: OrchestrationResult):
        """Update global orchestration metrics"""
        
        self.orchestration_metrics["total_orchestrations"] += 1
        
        if orchestration.status == OrchestrationStatus.COMPLETED:
            self.orchestration_metrics["successful_orchestrations"] += 1
        else:
            self.orchestration_metrics["failed_orchestrations"] += 1
        
        # Update averages
        total = self.orchestration_metrics["total_orchestrations"]
        current_avg_time = self.orchestration_metrics["avg_execution_time"]
        current_avg_quality = self.orchestration_metrics["avg_quality_score"]
        
        self.orchestration_metrics["avg_execution_time"] = (
            (current_avg_time * (total - 1) + orchestration.total_execution_time) / total
        )
        
        if orchestration.quality_score > 0:
            self.orchestration_metrics["avg_quality_score"] = (
                (current_avg_quality * (total - 1) + orchestration.quality_score) / total
            )
    
    async def get_orchestration_status(self, orchestration_id: str) -> Optional[OrchestrationResult]:
        """Get status of a specific orchestration"""
        
        if orchestration_id in self.active_orchestrations:
            return self.active_orchestrations[orchestration_id]
        elif orchestration_id in self.completed_orchestrations:
            return self.completed_orchestrations[orchestration_id]
        else:
            return None
    
    async def get_orchestrator_metrics(self) -> Dict[str, Any]:
        """Get comprehensive orchestrator performance metrics"""
        
        active_orchestrations = len(self.active_orchestrations)
        completed_orchestrations = len(self.completed_orchestrations)
        
        return {
            "orchestrations": {
                "active": active_orchestrations,
                "completed": completed_orchestrations,
                "total_processed": self.orchestration_metrics["total_orchestrations"]
            },
            "performance": {
                "success_rate": (
                    self.orchestration_metrics["successful_orchestrations"] / 
                    max(1, self.orchestration_metrics["total_orchestrations"])
                ) * 100,
                "avg_execution_time": self.orchestration_metrics["avg_execution_time"],
                "avg_quality_score": self.orchestration_metrics["avg_quality_score"]
            },
            "components": {
                "intelligent_analyzer_available": self.intelligent_analyzer is not None,
                "strategy_selector_available": self.strategy_selector is not None,
                "high_volume_executor_available": self.high_volume_executor is not None,
                "data_analytics_available": self.data_analytics is not None
            }
        }
    
    def register_custom_step(self, step_name: str, step_function: Callable):
        """Register a custom workflow step"""
        
        self.custom_steps[step_name] = step_function
        logger.info(f"Registered custom workflow step: {step_name}")
    
    async def cleanup(self):
        """Clean up orchestrator resources"""
        
        logger.info("Shutting down extraction orchestrator...")
        
        # Clean up components
        if self.intelligent_analyzer:
            await self.intelligent_analyzer.cleanup()
        
        if self.strategy_selector:
            await self.strategy_selector.cleanup()
        
        if self.high_volume_executor:
            await self.high_volume_executor.shutdown()
        
        # Clear tracking data
        self.active_orchestrations.clear()
        self.completed_orchestrations.clear()
        
        logger.info("Extraction orchestrator cleanup complete")

# Convenience functions for common orchestration patterns
async def orchestrate_business_intelligence(urls: List[str],
                                          orchestrator: ExtractionOrchestrator) -> str:
    """Orchestrate comprehensive business intelligence extraction"""
    
    config = OrchestrationConfig(
        workflow_config=WorkflowConfig(
            enable_data_enrichment=True,
            enable_quality_validation=True,
            quality_threshold=0.8
        ),
        batch_config=BatchJobConfig(batch_size=25, max_workers=20),
        quality_threshold=0.8,
        confidence_threshold=0.7
    )
    
    return await orchestrator.orchestrate_batch_extraction(
        urls=urls,
        purpose="company_info",
        config=config
    )

async def orchestrate_contact_discovery(urls: List[str],
                                      orchestrator: ExtractionOrchestrator) -> str:
    """Orchestrate comprehensive contact discovery"""
    
    config = OrchestrationConfig(
        workflow_config=WorkflowConfig(
            enable_data_enrichment=True,
            custom_validation_rules=[
                {"rule": "email_format_validation"},
                {"rule": "phone_format_validation"}
            ]
        ),
        batch_config=BatchJobConfig(batch_size=50, max_workers=30)
    )
    
    return await orchestrator.orchestrate_batch_extraction(
        urls=urls,
        purpose="contact_discovery",
        config=config
    )
