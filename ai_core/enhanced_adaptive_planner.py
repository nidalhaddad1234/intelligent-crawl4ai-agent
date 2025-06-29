"""
Enhanced Adaptive Planner - Phase 6
Integrates enhanced tool capabilities with learning system
"""

import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .adaptive_planner import AdaptivePlanner
from .tool_enhancer import (
    EnhancedToolOrchestrator,
    DynamicParameterDiscovery,
    ToolCombinationEngine,
    PerformanceProfiler,
    CapabilityMatcher,
    ToolRecommendationEngine
)
from .registry import tool_registry


class EnhancedAdaptivePlanner(AdaptivePlanner):
    """
    Enhanced version of AdaptivePlanner that includes:
    - Dynamic parameter discovery
    - Tool combination optimization
    - Performance-based planning
    - Capability matching
    """
    
    def __init__(self, model_name: str = "deepseek-coder:1.3b"):
        super().__init__(model_name)
        self.orchestrator = EnhancedToolOrchestrator()
        self.last_performance_report = None
    
    async def create_plan(self, user_query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create an enhanced execution plan with intelligent tool selection"""
        if context is None:
            context = {}
        
        # Add user query to context for parameter discovery
        context['user_query'] = user_query
        
        # Try to find similar patterns first (from parent class)
        similar_patterns = await self.memory.find_similar_requests(user_query)
        
        if similar_patterns and similar_patterns[0]['similarity'] > 0.9:
            # Reuse successful pattern but enhance it
            pattern = similar_patterns[0]
            base_plan = pattern['plan']
            
            # Enhance the reused plan with current optimizations
            enhanced_plan = self._enhance_existing_plan(base_plan, context)
            
            return {
                'plan_id': self._generate_plan_id(),
                'query': user_query,
                'steps': enhanced_plan['steps'],
                'confidence': pattern['similarity'],
                'reused_from': pattern['pattern_id'],
                'enhancements': enhanced_plan['enhancements']
            }
        
        # Find matching tools using capability matcher
        intent_matches = self.orchestrator.capability_matcher.find_tools_for_intent(user_query)
        
        if not intent_matches:
            # Fallback to base planner
            base_plan = super().create_plan(user_query, context)
            
            # Record failed intent for recommendations
            self.orchestrator.recommendation_engine.record_failed_intent(
                user_query, []
            )
            
            return base_plan
        
        # Build plan using matched tools
        steps = []
        selected_tools = []
        
        # Select best tools based on performance and capabilities
        for match in intent_matches[:3]:  # Consider top 3 matches
            tool_name = match['tool']
            func_name = match['function']
            
            # Get performance estimate
            perf = self.orchestrator._estimate_performance(tool_name, func_name)
            
            # Skip tools with poor performance
            if perf['success_rate'] < 0.5:
                alternatives = self.orchestrator.capability_matcher.suggest_alternative_tools(
                    tool_name, func_name
                )
                if alternatives:
                    # Use best alternative
                    alt = alternatives[0]
                    tool_name = alt['tool']
                    func_name = alt['function']
            
            selected_tools.append((tool_name, func_name))
        
        # Optimize tool pipeline
        optimized_pipeline = self.orchestrator.optimize_tool_pipeline(selected_tools, context)
        
        # Build steps from optimized pipeline
        for i, tool_info in enumerate(optimized_pipeline):
            step = {
                'step': i + 1,
                'tool': tool_info['tool'],
                'function': tool_info['function'],
                'parameters': tool_info['suggested_params'],
                'dependencies': [i] if i > 0 else [],
                'performance_estimate': tool_info['performance_estimate'],
                'alternatives': [
                    {'tool': alt[0], 'function': alt[1], 'confidence': alt[2]}
                    for alt in tool_info.get('next_tool_suggestions', [])[:2]
                ]
            }
            steps.append(step)
        
        plan = {
            'plan_id': self._generate_plan_id(),
            'query': user_query,
            'steps': steps,
            'confidence': 0.8,  # Base confidence for new plans
            'optimization_applied': True,
            'estimated_total_time': sum(
                s['performance_estimate']['avg_time'] for s in steps
            )
        }
        
        # Store the plan
        self.memory.store_pattern(user_query, plan, {'created_at': datetime.now()})
        
        return plan
    
    def _enhance_existing_plan(self, base_plan: Dict[str, Any], 
                              context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance an existing plan with current optimizations"""
        enhanced_steps = []
        enhancements = []
        
        # Extract tools from plan
        planned_tools = [
            (step['tool'], step['function']) 
            for step in base_plan.get('steps', [])
        ]
        
        # Get optimized pipeline
        optimized_pipeline = self.orchestrator.optimize_tool_pipeline(planned_tools, context)
        
        for i, (step, opt_info) in enumerate(zip(base_plan.get('steps', []), optimized_pipeline)):
            enhanced_step = step.copy()
            
            # Update parameters with suggestions
            if opt_info['suggested_params']:
                original_params = enhanced_step.get('parameters', {})
                enhanced_step['parameters'] = {**original_params, **opt_info['suggested_params']}
                enhancements.append(f"Enhanced parameters for step {i+1}")
            
            # Add performance estimates
            enhanced_step['performance_estimate'] = opt_info['performance_estimate']
            
            # Add alternatives
            if opt_info.get('next_tool_suggestions'):
                enhanced_step['alternatives'] = [
                    {'tool': alt[0], 'function': alt[1], 'confidence': alt[2]}
                    for alt in opt_info['next_tool_suggestions'][:2]
                ]
            
            enhanced_steps.append(enhanced_step)
        
        return {
            'steps': enhanced_steps,
            'enhancements': enhancements
        }
    
    def execute_with_monitoring(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plan with performance monitoring and optimization"""
        execution_start = datetime.now()
        executed_steps = []
        
        # Record the tool combination
        tool_sequence = [
            (step['tool'], step['function'])
            for step in plan['steps']
        ]
        
        for step in plan['steps']:
            step_start = datetime.now()
            
            # Execute with enhancement
            result = self.orchestrator.enhance_tool_execution(
                step['tool'],
                step['function'],
                step.get('parameters', {}),
                {'user_query': plan['query'], 'previous_results': executed_steps}
            )
            
            step_execution_time = (datetime.now() - step_start).total_seconds()
            
            executed_steps.append({
                'step': step['step'],
                'tool': step['tool'],
                'function': step['function'],
                'result': result,
                'execution_time': step_execution_time,
                'success': result.get('success', False)
            })
            
            # If step failed and alternatives exist, try them
            if not result.get('success') and 'alternatives' in result:
                for alt in result['alternatives'][:1]:  # Try first alternative
                    alt_result = self.orchestrator.enhance_tool_execution(
                        alt['tool'],
                        alt['function'],
                        step.get('parameters', {}),
                        {'user_query': plan['query'], 'previous_results': executed_steps}
                    )
                    
                    if alt_result.get('success'):
                        executed_steps[-1] = {
                            'step': step['step'],
                            'tool': alt['tool'],
                            'function': alt['function'],
                            'result': alt_result,
                            'execution_time': step_execution_time,
                            'success': True,
                            'used_alternative': True
                        }
                        break
        
        # Record execution results
        total_time = (datetime.now() - execution_start).total_seconds()
        success = all(step['success'] for step in executed_steps)
        
        # Record combination performance
        self.orchestrator.combination_engine.record_combination(
            tool_sequence,
            success,
            total_time,
            output_quality=1.0 if success else 0.5
        )
        
        # Record outcome in learning memory
        self.record_outcome(
            plan['plan_id'],
            success,
            executed_steps,
            total_time
        )
        
        return {
            'plan_id': plan['plan_id'],
            'executed_steps': executed_steps,
            'total_execution_time': total_time,
            'success': success,
            'optimization_impact': self._calculate_optimization_impact(plan, executed_steps)
        }
    
    def _calculate_optimization_impact(self, plan: Dict[str, Any], 
                                     executed_steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate the impact of optimizations"""
        estimated_time = plan.get('estimated_total_time', 0)
        actual_time = sum(step['execution_time'] for step in executed_steps)
        
        alternatives_used = sum(
            1 for step in executed_steps 
            if step.get('used_alternative', False)
        )
        
        return {
            'time_saved': max(0, estimated_time - actual_time),
            'time_accuracy': 1 - abs(estimated_time - actual_time) / max(estimated_time, actual_time, 1),
            'alternatives_used': alternatives_used,
            'success_rate_impact': 'positive' if all(s['success'] for s in executed_steps) else 'neutral'
        }
    
    def get_tool_insights(self) -> Dict[str, Any]:
        """Get insights about tool usage and recommendations"""
        insights = self.orchestrator.get_insights_report()
        
        # Add learning-based insights
        pattern_stats = self.memory.get_pattern_statistics()
        insights['learning_insights'] = {
            'total_patterns': pattern_stats['total_patterns'],
            'success_rate': pattern_stats['average_success_rate'],
            'most_successful_tools': self._get_most_successful_tools(),
            'optimization_opportunities': self._identify_optimization_opportunities()
        }
        
        return insights
    
    def _get_most_successful_tools(self) -> List[Dict[str, Any]]:
        """Identify most successful tools from patterns"""
        tool_success = {}
        patterns = self.memory.get_all_patterns()
        
        for pattern in patterns:
            if pattern.get('success_rate', 0) > 0:
                for step in pattern.get('plan', {}).get('steps', []):
                    key = f"{step['tool']}.{step['function']}"
                    if key not in tool_success:
                        tool_success[key] = {'count': 0, 'success_rate': 0}
                    tool_success[key]['count'] += 1
                    tool_success[key]['success_rate'] += pattern['success_rate']
        
        # Average success rates
        for key in tool_success:
            if tool_success[key]['count'] > 0:
                tool_success[key]['success_rate'] /= tool_success[key]['count']
        
        # Sort by success rate
        sorted_tools = sorted(
            tool_success.items(),
            key=lambda x: x[1]['success_rate'],
            reverse=True
        )
        
        return [
            {
                'tool': key.split('.')[0],
                'function': key.split('.')[1],
                'usage_count': data['count'],
                'success_rate': data['success_rate']
            }
            for key, data in sorted_tools[:5]
        ]
    
    def _identify_optimization_opportunities(self) -> List[Dict[str, Any]]:
        """Identify opportunities for optimization"""
        opportunities = []
        
        # Check for slow tools
        perf_report = self.orchestrator.profiler.get_performance_report()
        for tool_key, metrics in perf_report.items():
            if metrics['avg_execution_time'] > 5:  # Tools taking more than 5 seconds
                opportunities.append({
                    'type': 'performance',
                    'tool': tool_key,
                    'issue': f"Slow execution: {metrics['avg_execution_time']:.1f}s average",
                    'recommendation': "Consider caching or parallel execution"
                })
        
        # Check for frequently failing tools
        for tool_key, metrics in perf_report.items():
            if metrics['success_rate'] < 0.7 and metrics['total_executions'] > 5:
                opportunities.append({
                    'type': 'reliability',
                    'tool': tool_key,
                    'issue': f"Low success rate: {metrics['success_rate']:.1%}",
                    'recommendation': "Review error patterns and improve error handling"
                })
        
        return opportunities
    
    def suggest_new_capabilities(self) -> List[Dict[str, Any]]:
        """Suggest new capabilities based on usage patterns"""
        recommendations = self.orchestrator.recommendation_engine.recommend_new_tools()
        
        # Enhance recommendations with learning insights
        for rec in recommendations:
            # Find similar successful patterns
            similar_patterns = await self.memory.find_similar_requests(rec['capability'])
            if similar_patterns:
                rec['similar_patterns'] = len(similar_patterns)
                rec['potential_reuse'] = similar_patterns[0]['similarity']
        
        return recommendations


# Export enhanced planner
__all__ = ['EnhancedAdaptivePlanner']
