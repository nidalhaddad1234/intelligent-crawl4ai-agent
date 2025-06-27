"""
Adaptive Planner - Enhanced AI planner that learns from experience

This module extends the base AI planner with learning capabilities,
allowing it to improve over time by learning from past interactions.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple

from .planner import AIPlanner, ExecutionPlan, PlanStatus
from .learning import LearningMemory, PatternTrainer
from .registry import tool_registry


logger = logging.getLogger(__name__)


class AdaptivePlanner(AIPlanner):
    """
    Enhanced planner that learns from experience
    """
    
    def __init__(self, 
                 local_ai_url: str = "http://localhost:11434",
                 local_model: str = "deepseek-coder:1.3b",
                 teacher_ai_url: Optional[str] = None,
                 confidence_threshold: float = 0.7,
                 chromadb_host: str = "localhost",
                 chromadb_port: int = 8000,
                 enable_learning: bool = True):
        """
        Initialize Adaptive Planner with learning capabilities
        
        Args:
            local_ai_url: URL for local AI (Ollama)
            local_model: Model name for local AI
            teacher_ai_url: URL for teacher AI (Claude MCP)
            confidence_threshold: Minimum confidence to use local AI
            chromadb_host: ChromaDB host for learning memory
            chromadb_port: ChromaDB port
            enable_learning: Whether to enable learning features
        """
        super().__init__(local_ai_url, local_model, teacher_ai_url, confidence_threshold)
        
        self.enable_learning = enable_learning
        
        if enable_learning:
            # Initialize learning components
            self.memory = LearningMemory(
                chromadb_host=chromadb_host,
                chromadb_port=chromadb_port
            )
            self.trainer = PatternTrainer(self.memory)
            logger.info("Adaptive planning with learning enabled")
        else:
            self.memory = None
            self.trainer = None
            logger.info("Adaptive planning without learning (ChromaDB not available)")
    
    async def create_plan(self, user_request: str) -> ExecutionPlan:
        """
        Create an execution plan with learning capabilities
        
        Args:
            user_request: Natural language request from user
            
        Returns:
            ExecutionPlan object with steps to execute
        """
        start_time = time.time()
        
        # First, check for similar past requests if learning is enabled
        if self.enable_learning and self.memory:
            similar_patterns = await self.memory.find_similar_requests(user_request, k=3)
            
            if similar_patterns:
                best_pattern = similar_patterns[0]
                
                # If we have a very similar successful pattern, adapt and reuse it
                if best_pattern.confidence > 0.9:
                    logger.info(f"Reusing successful pattern (confidence: {best_pattern.confidence:.0%})")
                    
                    # Adapt the pattern to the new request
                    adapted_plan = self._adapt_pattern(best_pattern, user_request)
                    
                    # Log the adaptation
                    logger.info(f"Adapted plan with {len(adapted_plan.steps)} steps from past success")
                    
                    return adapted_plan
        
        # Otherwise, create new plan using base planner
        plan = await super().create_plan(user_request)
        
        # If confidence is low and we have a trainer, try to improve
        if self.enable_learning and self.trainer and plan.confidence < self.confidence_threshold:
            improved_plan = await self.trainer.suggest_plan_improvements(user_request, plan)
            
            if improved_plan:
                logger.info(f"Improved plan confidence from {plan.confidence:.0%} to {improved_plan.confidence:.0%}")
                plan = improved_plan
        
        # If still low confidence, consult teacher
        if plan.confidence < self.confidence_threshold and self.teacher_ai_url:
            logger.info(f"Low confidence ({plan.confidence:.0%}), consulting teacher AI")
            teacher_plan, teacher_confidence = await self._create_plan_with_teacher_ai(user_request, tool_registry.get_tool_manifest())
            
            # Learn from teacher
            if self.enable_learning and self.trainer and teacher_confidence > plan.confidence:
                await self.trainer.train_from_teacher(user_request, plan, teacher_plan)
            
            plan = teacher_plan
        
        planning_time = time.time() - start_time
        logger.info(f"Plan created in {planning_time:.2f}s with confidence {plan.confidence:.0%}")
        
        return plan
    
    async def record_outcome(self, 
                           request: str, 
                           plan: ExecutionPlan, 
                           success: bool,
                           execution_time: float,
                           error_details: Optional[str] = None) -> None:
        """
        Record the outcome of a plan execution for learning
        
        Args:
            request: Original user request
            plan: The plan that was executed
            success: Whether execution was successful
            execution_time: Time taken to execute
            error_details: Error details if failed
        """
        if not self.enable_learning or not self.memory:
            return
        
        outcome = "success" if success else "failure"
        
        # Store the interaction
        pattern_id = await self.memory.store_interaction(
            request=request,
            plan=plan,
            outcome=outcome,
            execution_time=execution_time,
            error_details=error_details
        )
        
        # Log tool performance
        for step in plan.steps:
            current_rate = await self.memory.get_success_rate(step.tool)
            logger.info(f"Tool '{step.tool}' success rate: {current_rate:.0%}")
        
        # If this was a failure, analyze it immediately
        if not success and self.trainer:
            logger.info("Analyzing failure for immediate learning...")
            failure_analysis = await self.trainer.analyze_failures(limit=1)
            
            if failure_analysis:
                logger.info(f"Failure type: {failure_analysis[0].get('failure_type', 'unknown')}")
                logger.info(f"Suggestion: {failure_analysis[0].get('suggestion', 'none')}")
    
    async def get_learning_stats(self) -> Dict[str, Any]:
        """
        Get current learning statistics
        
        Returns:
            Dictionary with learning metrics
        """
        if not self.enable_learning or not self.memory:
            return {
                "status": "Learning disabled",
                "total_patterns": 0,
                "success_rate": 0
            }
        
        return await self.memory.get_statistics()
    
    async def run_learning_routine(self) -> Dict[str, Any]:
        """
        Run the learning routine (can be scheduled daily)
        
        Returns:
            Learning report
        """
        if not self.enable_learning or not self.trainer:
            return {
                "status": "Learning disabled",
                "report": None
            }
        
        logger.info("Running learning routine...")
        report = await self.trainer.daily_learning_routine()
        
        # Log key insights
        logger.info(f"Learning routine complete - {report['statistics']['total_patterns']} patterns analyzed")
        
        return report
    
    def _adapt_pattern(self, pattern, new_request: str) -> ExecutionPlan:
        """
        Adapt a successful pattern to a new request
        
        Args:
            pattern: The successful pattern to adapt
            new_request: The new user request
            
        Returns:
            Adapted execution plan
        """
        import uuid
        from datetime import datetime
        
        # Extract plan structure from pattern
        plan_data = pattern.plan
        
        # Create new steps based on pattern
        steps = []
        for step_data in plan_data.get("steps", []):
            step = PlanStep(
                step_id=step_data["step_id"],
                tool=step_data["tool"],
                parameters=self._adapt_parameters(step_data["parameters"], new_request),
                description=step_data["description"],
                depends_on=step_data.get("depends_on", [])
            )
            steps.append(step)
        
        # Create adapted plan
        adapted_plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            request=new_request,
            description=f"Adapted: {plan_data.get('description', 'Based on successful pattern')}",
            steps=steps,
            created_at=datetime.now().isoformat(),
            confidence=pattern.confidence * 0.95  # Slightly lower for adapted plans
        )
        
        return adapted_plan
    
    def _adapt_parameters(self, 
                         original_params: Dict[str, Any], 
                         new_request: str) -> Dict[str, Any]:
        """
        Adapt parameters from a pattern to a new request
        
        This is a simplified version - in production would use
        more sophisticated parameter extraction and mapping
        """
        adapted = original_params.copy()
        
        # Extract URLs from new request if present
        import re
        url_pattern = r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&/=]*)'
        urls = re.findall(url_pattern, new_request)
        
        # Update URL parameters if found
        if urls:
            if "url" in adapted:
                adapted["url"] = urls[0]
            elif "urls" in adapted:
                adapted["urls"] = urls
        
        # Update any query/prompt parameters
        if "query" in adapted:
            adapted["query"] = new_request
        elif "prompt" in adapted:
            adapted["prompt"] = new_request
        elif "message" in adapted:
            adapted["message"] = new_request
        
        return adapted


# Import PlanStep at module level to avoid circular imports
from .planner import PlanStep
