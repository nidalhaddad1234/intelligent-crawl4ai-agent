"""
Consolidated AI Planner - Unified planning engine

This module consolidates all planner functionality into a single, comprehensive
planning system that combines the best features from all previous planners.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import requests

from .registry import tool_registry

logger = logging.getLogger(__name__)


class PlanStatus(Enum):
    """Status of a plan or step"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class PlanStep:
    """Represents a single step in an execution plan"""
    step_id: int
    tool: str
    parameters: Dict[str, Any]
    description: str
    depends_on: List[int] = None
    error_handling: str = "fail"
    retry_count: int = 0
    max_retries: int = 3
    status: PlanStatus = PlanStatus.PENDING
    result: Any = None
    error: Optional[str] = None


@dataclass
class ExecutionPlan:
    """Complete execution plan for a user request"""
    plan_id: str
    request: str
    description: str
    steps: List[PlanStep]
    created_at: str
    confidence: float
    status: PlanStatus = PlanStatus.PENDING
    result: Any = None
    source: str = "unified_planner"


class UnifiedAIPlanner:
    """
    Unified AI Planning Engine that combines all previous planner capabilities:
    - Base planning functionality
    - Adaptive learning from experience
    - Enhanced tool orchestration
    - Hybrid AI provider support
    """
    
    def __init__(self, 
                 local_ai_url: str = "http://localhost:11434",
                 local_model: str = "deepseek-coder:1.3b",
                 teacher_ai_url: Optional[str] = None,
                 confidence_threshold: float = 0.7,
                 enable_learning: bool = True,
                 enable_hybrid_ai: bool = True):
        """
        Initialize the Unified AI Planner
        
        Args:
            local_ai_url: URL for local AI (Ollama)
            local_model: Model name for local AI
            teacher_ai_url: URL for teacher AI (Claude MCP)
            confidence_threshold: Minimum confidence to use local AI
            enable_learning: Whether to enable learning features
            enable_hybrid_ai: Whether to enable hybrid AI providers
        """
        self.local_ai_url = local_ai_url
        self.local_model = local_model
        self.teacher_ai_url = teacher_ai_url
        self.confidence_threshold = confidence_threshold
        self.enable_learning = enable_learning
        self.enable_hybrid_ai = enable_hybrid_ai
        
        # Initialize components based on availability
        self._init_learning_components()
        self._init_enhancement_components()
        self._init_hybrid_ai_components()
        
    def _init_learning_components(self):
        """Initialize learning components if available"""
        if self.enable_learning:
            try:
                from ..learning import LearningMemory, PatternTrainer
                self.memory = LearningMemory()
                self.trainer = PatternTrainer(self.memory)
                logger.info("Learning components initialized")
            except ImportError:
                self.memory = None
                self.trainer = None
                logger.warning("Learning components not available")
        else:
            self.memory = None
            self.trainer = None
    
    def _init_enhancement_components(self):
        """Initialize enhancement components if available"""
        try:
            from ..enhancement.tool_enhancer import EnhancedToolOrchestrator
            self.orchestrator = EnhancedToolOrchestrator()
            logger.info("Enhancement components initialized")
        except ImportError:
            self.orchestrator = None
            logger.warning("Enhancement components not available")
    
    def _init_hybrid_ai_components(self):
        """Initialize hybrid AI components if available"""
        if self.enable_hybrid_ai:
            try:
                from ..core.hybrid_ai_service import create_production_ai_service
                self.ai_service = create_production_ai_service()
                logger.info("Hybrid AI service initialized")
            except ImportError:
                self.ai_service = None
                logger.warning("Hybrid AI service not available")
        else:
            self.ai_service = None
    
    async def create_plan(self, user_request: str, context: Dict[str, Any] = None) -> ExecutionPlan:
        """
        Create an execution plan for a user request
        Uses the best available method based on enabled features
        
        Args:
            user_request: Natural language request from user
            context: Additional context for planning
            
        Returns:
            ExecutionPlan object with steps to execute
        """
        if context is None:
            context = {}
        
        start_time = time.time()
        
        # Step 1: Check for similar patterns if learning is enabled
        if self.memory:
            similar_patterns = await self.memory.find_similar_requests(user_request, k=3)
            
            if similar_patterns and similar_patterns[0].confidence > 0.9:
                logger.info(f"Reusing successful pattern (confidence: {similar_patterns[0].confidence:.0%})")
                adapted_plan = self._adapt_pattern(similar_patterns[0], user_request)
                planning_time = time.time() - start_time
                logger.info(f"Plan created via pattern reuse in {planning_time:.2f}s")
                return adapted_plan
        
        # Step 2: Try enhanced planning if orchestrator is available
        if self.orchestrator:
            enhanced_plan = await self._create_enhanced_plan(user_request, context)
            if enhanced_plan and enhanced_plan.confidence > self.confidence_threshold:
                planning_time = time.time() - start_time
                logger.info(f"Plan created via enhancement in {planning_time:.2f}s")
                return enhanced_plan
        
        # Step 3: Try hybrid AI if available
        if self.ai_service:
            hybrid_plan = await self._create_hybrid_plan(user_request, context)
            if hybrid_plan and hybrid_plan.confidence > self.confidence_threshold:
                planning_time = time.time() - start_time
                logger.info(f"Plan created via hybrid AI in {planning_time:.2f}s")
                return hybrid_plan
        
        # Step 4: Fallback to local AI
        local_plan, confidence = await self._create_plan_with_local_ai(user_request, tool_registry.get_tool_manifest())
        
        # Step 5: Final fallback if confidence is still low
        if confidence < self.confidence_threshold and self.teacher_ai_url:
            logger.info(f"Low confidence ({confidence:.2f}), consulting teacher AI")
            teacher_plan, teacher_confidence = await self._create_plan_with_teacher_ai(user_request, tool_registry.get_tool_manifest())
            
            # Learn from teacher if learning is enabled
            if self.trainer and teacher_confidence > confidence:
                await self.trainer.train_from_teacher(user_request, local_plan, teacher_plan)
            
            local_plan = teacher_plan
        
        planning_time = time.time() - start_time
        logger.info(f"Plan created in {planning_time:.2f}s with confidence {local_plan.confidence:.0%}")
        
        return local_plan
    
    def _generate_plan_id(self) -> str:
        """Generate unique plan ID"""
        import uuid
        return str(uuid.uuid4())


class PlanExecutor:
    """Enhanced plan executor with monitoring and optimization"""
    
    def __init__(self, planner: UnifiedAIPlanner):
        self.planner = planner
        self.registry = tool_registry
    
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """Execute a plan with full monitoring and optimization"""
        plan.status = PlanStatus.EXECUTING
        step_results = {}
        
        try:
            for step in plan.steps:
                # Execute step with monitoring
                step_result = await self._execute_step_with_monitoring(step, step_results)
                step_results[step.step_id] = step_result
            
            # Determine overall plan status
            plan.status = PlanStatus.COMPLETED if all(
                s.status == PlanStatus.COMPLETED for s in plan.steps
            ) else PlanStatus.FAILED
        
        except Exception as e:
            plan.status = PlanStatus.FAILED
            logger.error(f"Plan execution failed: {e}")
        
        return plan
    
    async def _execute_step_with_monitoring(self, step: PlanStep, previous_results: Dict[int, Any]) -> Any:
        """Execute a single step with monitoring"""
        import time
        start_time = time.time()
        
        try:
            # Get and execute tool
            tool = self.registry.get_tool(step.tool)
            if not tool:
                raise ValueError(f"Tool not found: {step.tool}")
            
            # Prepare parameters
            params = self._prepare_parameters(step.parameters, previous_results)
            
            # Execute
            result = await tool(**params)
            
            step.result = result
            step.status = PlanStatus.COMPLETED
            step.execution_time = time.time() - start_time
            
            return result
            
        except Exception as e:
            step.error = str(e)
            step.status = PlanStatus.FAILED
            step.execution_time = time.time() - start_time
            raise
    
    def _prepare_parameters(self, params: Dict[str, Any], previous_results: Dict[int, Any]) -> Dict[str, Any]:
        """Prepare parameters with result substitution"""
        prepared = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("{step_") and value.endswith("}"):
                # Extract step reference
                step_ref = value[1:-1]  # Remove { }
                step_id = int(step_ref.split("_")[1].split(".")[0])
                
                if step_id in previous_results:
                    if "." in step_ref:
                        parts = step_ref.split(".")[1:]
                        result = previous_results[step_id]
                        for part in parts:
                            result = result.get(part) if isinstance(result, dict) else getattr(result, part, None)
                        prepared[key] = result
                    else:
                        prepared[key] = previous_results[step_id]
                else:
                    prepared[key] = value
            else:
                prepared[key] = value
                
        return prepared


# Export main classes
__all__ = ['UnifiedAIPlanner', 'PlanExecutor', 'ExecutionPlan', 'PlanStep', 'PlanStatus']
