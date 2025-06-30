"""
Pattern Trainer - Analyzes patterns and improves AI planning

This module analyzes success and failure patterns to continuously
improve the AI's planning capabilities.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import asyncio

from .memory import LearningMemory, LearningPattern
from ..planner import ExecutionPlan, PlanStep


logger = logging.getLogger(__name__)


class PatternTrainer:
    """
    Analyzes patterns and improves planning through learning
    """
    
    def __init__(self, memory: LearningMemory):
        """
        Initialize Pattern Trainer
        
        Args:
            memory: Learning memory instance
        """
        self.memory = memory
        self.improvement_suggestions = []
        self.learning_insights = []
    
    async def analyze_failures(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Analyze failed plans to identify patterns and suggest improvements
        
        Args:
            limit: Maximum number of failures to analyze
            
        Returns:
            List of failure analysis with improvement suggestions
        """
        # Get failure patterns
        failures = await self.memory.get_failure_patterns(limit)
        
        # Group failures by type
        failure_groups = defaultdict(list)
        
        for failure in failures:
            # Categorize by error type
            error = failure.get("error_details", "Unknown error")
            
            if "timeout" in error.lower():
                failure_groups["timeout"].append(failure)
            elif "not found" in error.lower() or "404" in error.lower():
                failure_groups["not_found"].append(failure)
            elif "permission" in error.lower() or "forbidden" in error.lower():
                failure_groups["permission"].append(failure)
            elif "parse" in error.lower() or "extract" in error.lower():
                failure_groups["extraction"].append(failure)
            else:
                failure_groups["other"].append(failure)
        
        # Analyze each group
        analysis = []
        
        for failure_type, patterns in failure_groups.items():
            if patterns:
                suggestion = self._generate_improvement_suggestion(failure_type, patterns)
                analysis.append({
                    "failure_type": failure_type,
                    "count": len(patterns),
                    "examples": patterns[:3],  # First 3 examples
                    "suggestion": suggestion,
                    "affected_tools": self._extract_affected_tools(patterns)
                })
        
        logger.info(f"Analyzed {len(failures)} failures across {len(failure_groups)} categories")
        return analysis
    
    async def train_from_teacher(self, 
                               request: str, 
                               student_plan: ExecutionPlan,
                               teacher_plan: ExecutionPlan) -> Dict[str, Any]:
        """
        Learn from Claude's better plan
        
        Args:
            request: The original user request
            student_plan: The plan created by local AI
            teacher_plan: The better plan from Claude
            
        Returns:
            Training insights
        """
        # Compare plans
        comparison = self._compare_plans(student_plan, teacher_plan)
        
        # Store teacher's plan as high-quality example
        await self.memory.store_interaction(
            request=request,
            plan=teacher_plan,
            outcome="success",  # Assume teacher plans are good
            execution_time=0.0,  # Not executed yet
            error_details=None
        )
        
        # Generate insights
        insights = {
            "request": request,
            "student_confidence": student_plan.confidence,
            "teacher_confidence": teacher_plan.confidence,
            "differences": comparison,
            "learning_points": self._extract_learning_points(comparison),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        self.learning_insights.append(insights)
        
        logger.info(f"Learned from teacher - {len(comparison['tool_differences'])} tool differences found")
        return insights
    
    async def daily_learning_routine(self) -> Dict[str, Any]:
        """
        Run daily to consolidate learning and generate reports
        
        Returns:
            Learning report with statistics and recommendations
        """
        logger.info("Starting daily learning routine...")
        
        # Get statistics
        stats = await self.memory.get_statistics()
        
        # Analyze failures
        failure_analysis = await self.analyze_failures()
        
        # Get tool performance
        tool_performance = await self.memory.get_tool_performance()
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            stats, failure_analysis, tool_performance
        )
        
        # Create learning report
        report = {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "statistics": stats,
            "failure_analysis": failure_analysis,
            "tool_performance": tool_performance,
            "recommendations": recommendations,
            "insights_count": len(self.learning_insights),
            "improvement_areas": self._identify_improvement_areas(tool_performance)
        }
        
        # Log summary
        logger.info(f"Daily learning complete - Success rate: {stats.get('success_rate', 0):.0%}")
        logger.info(f"Top recommendation: {recommendations[0] if recommendations else 'None'}")
        
        return report
    
    async def suggest_plan_improvements(self, 
                                      request: str,
                                      current_plan: ExecutionPlan) -> Optional[ExecutionPlan]:
        """
        Suggest improvements to a plan based on past patterns
        
        Args:
            request: User request
            current_plan: Current execution plan
            
        Returns:
            Improved plan if applicable
        """
        # Find similar successful patterns
        similar_patterns = await self.memory.find_similar_requests(request, k=3)
        
        if not similar_patterns:
            return None
        
        # Check if any similar pattern has significantly higher success rate
        best_pattern = max(similar_patterns, key=lambda p: p.confidence)
        
        if best_pattern.confidence > current_plan.confidence + 0.2:
            # Adapt the successful pattern
            logger.info(f"Found better pattern with {best_pattern.confidence:.0%} confidence")
            return self._adapt_pattern_to_plan(best_pattern, request)
        
        return None
    
    def _generate_improvement_suggestion(self, 
                                       failure_type: str, 
                                       patterns: List[Dict]) -> str:
        """Generate improvement suggestion for failure type"""
        suggestions = {
            "timeout": "Consider increasing timeout limits or breaking down large requests into smaller chunks",
            "not_found": "Verify URLs are valid before processing and add retry logic with backoff",
            "permission": "Check authentication requirements and handle 403 errors gracefully",
            "extraction": "Review extraction strategies and add fallback methods for difficult sites",
            "other": "Analyze error patterns and add specific error handling"
        }
        
        return suggestions.get(failure_type, "Review and add better error handling")
    
    def _extract_affected_tools(self, patterns: List[Dict]) -> List[str]:
        """Extract tools that appear in failed patterns"""
        tools = set()
        for pattern in patterns:
            for tool in pattern.get("failed_tools", []):
                if tool:
                    tools.add(tool)
        return list(tools)
    
    def _compare_plans(self, plan1: ExecutionPlan, plan2: ExecutionPlan) -> Dict[str, Any]:
        """Compare two plans to find differences"""
        comparison = {
            "confidence_diff": plan2.confidence - plan1.confidence,
            "step_count_diff": len(plan2.steps) - len(plan1.steps),
            "tool_differences": [],
            "parameter_differences": []
        }
        
        # Compare tools used
        tools1 = {step.tool for step in plan1.steps}
        tools2 = {step.tool for step in plan2.steps}
        
        comparison["tool_differences"] = {
            "added": list(tools2 - tools1),
            "removed": list(tools1 - tools2)
        }
        
        # Compare parameters for common tools
        for step1 in plan1.steps:
            for step2 in plan2.steps:
                if step1.tool == step2.tool:
                    param_diff = self._compare_parameters(step1.parameters, step2.parameters)
                    if param_diff:
                        comparison["parameter_differences"].append({
                            "tool": step1.tool,
                            "differences": param_diff
                        })
        
        return comparison
    
    def _compare_parameters(self, params1: Dict, params2: Dict) -> Dict[str, Any]:
        """Compare parameters between two steps"""
        differences = {}
        
        all_keys = set(params1.keys()) | set(params2.keys())
        
        for key in all_keys:
            val1 = params1.get(key)
            val2 = params2.get(key)
            
            if val1 != val2:
                differences[key] = {
                    "old": val1,
                    "new": val2
                }
        
        return differences
    
    def _extract_learning_points(self, comparison: Dict[str, Any]) -> List[str]:
        """Extract specific learning points from plan comparison"""
        points = []
        
        if comparison["confidence_diff"] > 0.1:
            points.append(f"Teacher plan has {comparison['confidence_diff']:.0%} higher confidence")
        
        if comparison["tool_differences"]["added"]:
            points.append(f"Consider using tools: {', '.join(comparison['tool_differences']['added'])}")
        
        if comparison["tool_differences"]["removed"]:
            points.append(f"Avoid unnecessary tools: {', '.join(comparison['tool_differences']['removed'])}")
        
        if comparison["step_count_diff"] < 0:
            points.append("Teacher uses fewer steps - consider simplifying")
        elif comparison["step_count_diff"] > 0:
            points.append("Teacher uses more steps - consider breaking down complex tasks")
        
        return points
    
    def _generate_recommendations(self, 
                                stats: Dict[str, Any],
                                failure_analysis: List[Dict],
                                tool_performance: Dict[str, Dict]) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Overall success rate recommendation
        success_rate = stats.get("success_rate", 0)
        if success_rate < 0.7:
            recommendations.append(f"Success rate is {success_rate:.0%} - consider consulting teacher AI more often")
        
        # Tool-specific recommendations
        for tool, metrics in tool_performance.items():
            if metrics["success_rate"] < 0.6:
                recommendations.append(f"Tool '{tool}' has low success rate ({metrics['success_rate']:.0%}) - review usage patterns")
            
            if metrics["avg_time"] > 30:
                recommendations.append(f"Tool '{tool}' is slow (avg {metrics['avg_time']:.1f}s) - consider optimization")
        
        # Failure pattern recommendations
        for analysis in failure_analysis:
            if analysis["count"] > 5:
                recommendations.append(f"{analysis['failure_type']} failures are common - {analysis['suggestion']}")
        
        # Learning insights recommendation
        if len(self.learning_insights) > 10:
            recommendations.append(f"Review {len(self.learning_insights)} teacher insights for pattern improvements")
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _identify_improvement_areas(self, tool_performance: Dict[str, Dict]) -> List[str]:
        """Identify specific areas for improvement"""
        areas = []
        
        # Find worst performing tools
        worst_tools = sorted(
            tool_performance.items(),
            key=lambda x: x[1]["success_rate"]
        )[:3]
        
        for tool, metrics in worst_tools:
            if metrics["success_rate"] < 0.8:
                areas.append(f"Improve {tool} (currently {metrics['success_rate']:.0%} success)")
        
        return areas
    
    def _adapt_pattern_to_plan(self, pattern: LearningPattern, new_request: str) -> ExecutionPlan:
        """Adapt a successful pattern to create a new plan"""
        # This is a simplified adaptation - in reality would be more sophisticated
        import uuid
        from ..planner import ExecutionPlan, PlanStep, PlanStatus
        
        # Extract plan data from pattern
        plan_data = pattern.plan
        
        # Create new steps based on pattern
        new_steps = []
        for i, step_data in enumerate(plan_data.get("steps", [])):
            new_step = PlanStep(
                step_id=i + 1,
                tool=step_data["tool"],
                parameters=step_data["parameters"].copy(),  # Copy to avoid mutations
                description=step_data["description"]
            )
            new_steps.append(new_step)
        
        # Create new plan
        new_plan = ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            request=new_request,
            description=f"Adapted from successful pattern: {plan_data.get('description', '')}",
            steps=new_steps,
            created_at=datetime.now(timezone.utc).isoformat(),
            confidence=pattern.confidence * 0.9  # Slightly lower confidence for adapted plan
        )
        
        return new_plan
