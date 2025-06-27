"""
AI Planner - The brain of the AI-first architecture

This module implements the AI planning engine that creates execution plans
based on user requests using available tools.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
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


class AIPlanner:
    """
    AI Planning Engine that creates execution plans from user requests
    """
    
    def __init__(self, 
                 local_ai_url: str = "http://localhost:11434",
                 local_model: str = "deepseek-coder:1.3b",
                 teacher_ai_url: Optional[str] = None,
                 confidence_threshold: float = 0.7):
        """
        Initialize the AI Planner
        
        Args:
            local_ai_url: URL for local AI (Ollama)
            local_model: Model name for local AI
            teacher_ai_url: URL for teacher AI (Claude MCP)
            confidence_threshold: Minimum confidence to use local AI
        """
        self.local_ai_url = local_ai_url
        self.local_model = local_model
        self.teacher_ai_url = teacher_ai_url
        self.confidence_threshold = confidence_threshold
        
    def create_plan(self, user_request: str) -> ExecutionPlan:
        """
        Create an execution plan for a user request
        
        Args:
            user_request: Natural language request from user
            
        Returns:
            ExecutionPlan object with steps to execute
        """
        # Get available tools
        tool_manifest = tool_registry.get_tool_manifest()
        
        # Try local AI first
        plan, confidence = self._create_plan_with_local_ai(user_request, tool_manifest)
        
        # If confidence is low, use teacher AI
        if confidence < self.confidence_threshold and self.teacher_ai_url:
            logger.info(f"Low confidence ({confidence:.2f}), consulting teacher AI")
            plan, confidence = self._create_plan_with_teacher_ai(user_request, tool_manifest)
        
        return plan
    
    def _create_plan_with_local_ai(self, 
                                   request: str, 
                                   tools: Dict[str, Any]) -> Tuple[ExecutionPlan, float]:
        """Create plan using local AI model"""
        prompt = self._build_planning_prompt(request, tools)
        
        try:
            # Call Ollama API
            response = requests.post(
                f"{self.local_ai_url}/api/generate",
                json={
                    "model": self.local_model,
                    "prompt": prompt,
                    "format": "json",
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                plan_data = json.loads(result.get("response", "{}"))
                
                # Parse the plan
                plan = self._parse_plan_response(plan_data, request)
                confidence = plan_data.get("confidence", 0.5)
                
                return plan, confidence
            else:
                logger.error(f"Local AI error: {response.status_code}")
                return self._create_fallback_plan(request), 0.0
                
        except Exception as e:
            logger.error(f"Error creating plan with local AI: {e}")
            return self._create_fallback_plan(request), 0.0
    
    def _create_plan_with_teacher_ai(self,
                                     request: str,
                                     tools: Dict[str, Any]) -> Tuple[ExecutionPlan, float]:
        """Create plan using teacher AI (Claude via MCP)"""
        # This would integrate with Claude Desktop MCP
        # For now, returning a placeholder
        logger.warning("Teacher AI integration not yet implemented")
        return self._create_fallback_plan(request), 0.5
    
    def _build_planning_prompt(self, request: str, tools: Dict[str, Any]) -> str:
        """Build the prompt for AI planning"""
        return f"""You are an AI planner that creates execution plans for web scraping and data extraction tasks.

User Request: {request}

Available Tools:
{json.dumps(tools, indent=2)}

Create a detailed execution plan that:
1. Breaks down the request into logical steps
2. Uses the appropriate tools for each step
3. Handles potential errors gracefully
4. Optimizes for efficiency and reliability

Return a JSON object with this structure:
{{
    "description": "Brief description of the plan",
    "confidence": 0.0-1.0,
    "steps": [
        {{
            "step_id": 1,
            "tool": "tool_name",
            "description": "What this step does",
            "parameters": {{}},
            "depends_on": [],
            "error_handling": "retry|fallback|fail"
        }}
    ]
}}

Important:
- Use exact tool names from the available tools
- Ensure parameters match the tool requirements
- Steps can depend on previous steps using depends_on
- Consider parallel execution where possible
"""
    
    def _parse_plan_response(self, plan_data: Dict[str, Any], request: str) -> ExecutionPlan:
        """Parse AI response into ExecutionPlan object"""
        import uuid
        from datetime import datetime
        
        steps = []
        for step_data in plan_data.get("steps", []):
            step = PlanStep(
                step_id=step_data["step_id"],
                tool=step_data["tool"],
                parameters=step_data.get("parameters", {}),
                description=step_data.get("description", ""),
                depends_on=step_data.get("depends_on", []),
                error_handling=step_data.get("error_handling", "fail")
            )
            steps.append(step)
        
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            request=request,
            description=plan_data.get("description", ""),
            steps=steps,
            created_at=datetime.now().isoformat(),
            confidence=plan_data.get("confidence", 0.5)
        )
    
    def _create_fallback_plan(self, request: str) -> ExecutionPlan:
        """Create a simple fallback plan when AI is unavailable"""
        import uuid
        from datetime import datetime
        
        # Simple heuristic: if URL mentioned, use crawler
        steps = []
        if "http" in request.lower() or "www" in request.lower():
            steps.append(PlanStep(
                step_id=1,
                tool="crawl_web",
                parameters={"strategy": "auto"},
                description="Extract data from web page"
            ))
        
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            request=request,
            description="Fallback plan - AI unavailable",
            steps=steps,
            created_at=datetime.now().isoformat(),
            confidence=0.1
        )


class PlanExecutor:
    """Executes plans created by the AI Planner"""
    
    def __init__(self):
        self.registry = tool_registry
        
    async def execute_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Execute a plan step by step
        
        Args:
            plan: The execution plan to run
            
        Returns:
            Updated plan with results
        """
        plan.status = PlanStatus.EXECUTING
        step_results = {}
        
        try:
            # Execute steps respecting dependencies
            for step in plan.steps:
                # Wait for dependencies
                if step.depends_on:
                    for dep_id in step.depends_on:
                        dep_step = next((s for s in plan.steps if s.step_id == dep_id), None)
                        if dep_step and dep_step.status != PlanStatus.COMPLETED:
                            step.status = PlanStatus.FAILED
                            step.error = "Dependency not completed"
                            continue
                
                # Execute the step
                step.status = PlanStatus.EXECUTING
                try:
                    result = await self._execute_step(step, step_results)
                    step.result = result
                    step.status = PlanStatus.COMPLETED
                    step_results[step.step_id] = result
                except Exception as e:
                    step.error = str(e)
                    step.status = PlanStatus.FAILED
                    
                    # Handle errors based on strategy
                    if step.error_handling == "retry" and step.retry_count < step.max_retries:
                        step.retry_count += 1
                        step.status = PlanStatus.RETRY
                        # Would retry here
                    elif step.error_handling == "fail":
                        plan.status = PlanStatus.FAILED
                        return plan
            
            # Plan completed successfully
            plan.status = PlanStatus.COMPLETED
            plan.result = self._aggregate_results(plan)
            
        except Exception as e:
            plan.status = PlanStatus.FAILED
            logger.error(f"Plan execution failed: {e}")
            
        return plan
    
    async def _execute_step(self, 
                           step: PlanStep, 
                           previous_results: Dict[int, Any]) -> Any:
        """Execute a single step"""
        # Get the tool
        tool = self.registry.get_tool(step.tool)
        if not tool:
            raise ValueError(f"Tool not found: {step.tool}")
        
        # Prepare parameters, substituting references to previous results
        params = self._prepare_parameters(step.parameters, previous_results)
        
        # Execute the tool
        return await tool(**params)
    
    def _prepare_parameters(self, 
                           params: Dict[str, Any], 
                           previous_results: Dict[int, Any]) -> Dict[str, Any]:
        """Prepare parameters, substituting references to previous results"""
        prepared = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("{step_") and value.endswith("}"):
                # Extract step reference
                step_ref = value[1:-1]  # Remove { }
                step_id = int(step_ref.split("_")[1].split(".")[0])
                
                if step_id in previous_results:
                    # Support nested access like {step_1.output.data}
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
    
    def _aggregate_results(self, plan: ExecutionPlan) -> Any:
        """Aggregate results from all steps"""
        # Simple aggregation - can be made smarter
        results = {}
        for step in plan.steps:
            if step.status == PlanStatus.COMPLETED:
                results[f"step_{step.step_id}"] = step.result
        
        return results
