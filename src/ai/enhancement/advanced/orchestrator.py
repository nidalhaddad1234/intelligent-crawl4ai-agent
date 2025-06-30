"""
Enhanced Tool Orchestrator
Integrates all enhanced tool capabilities for intelligent execution
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .parameter_discovery import ParameterInferenceEngine, ParameterContext
from .combination_engine import ToolCombinationEngine, ExecutionStrategy, ExecutionPipeline
from .performance_profiler import ToolPerformanceProfiler
from .capability_matcher import CapabilityMatcher
from .recommendation_engine import ToolRecommendationEngine

logger = logging.getLogger(__name__)


@dataclass
class EnhancedExecutionResult:
    """Result of enhanced tool execution"""
    success: bool
    results: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    execution_time: float


class EnhancedToolOrchestrator:
    """
    Orchestrates enhanced tool execution with all advanced capabilities
    """
    
    def __init__(self, tool_registry=None, learning_memory=None):
        self.tool_registry = tool_registry
        self.learning_memory = learning_memory
        
        # Initialize all components
        self.parameter_engine = ParameterInferenceEngine(tool_registry)
        self.combination_engine = ToolCombinationEngine(tool_registry, self)
        self.performance_profiler = ToolPerformanceProfiler()
        self.capability_matcher = CapabilityMatcher(tool_registry, self.performance_profiler)
        self.recommendation_engine = ToolRecommendationEngine(
            learning_memory, 
            self.performance_profiler, 
            self.capability_matcher
        )
    
    async def process_request(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> EnhancedExecutionResult:
        """
        Process a user request with all enhanced capabilities
        """
        logger.info(f"Processing request: {user_request}")
        start_time = asyncio.get_event_loop().time()
        
        # 1. Match request to tools
        matched_tools = self.capability_matcher.match_request_to_tools(
            user_request, 
            context,
            top_k=10
        )
        
        if not matched_tools:
            return EnhancedExecutionResult(
                success=False,
                results={'error': 'No matching tools found'},
                performance_metrics={},
                recommendations=[],
                execution_time=0
            )
        
        # 2. Suggest tool combinations
        combinations = self.capability_matcher.suggest_tool_combinations(
            user_request, 
            matched_tools
        )
        
        # 3. Create execution plan
        if combinations:
            # Use the first suggested combination
            tool_sequence = combinations[0]
            plan = self._create_plan_from_sequence(tool_sequence, user_request, context)
        else:
            # Use single best tool
            plan = self._create_single_tool_plan(matched_tools[0]['tool_name'], user_request, context)
        
        # 4. Get recommendations for plan optimization
        recommendations = self.recommendation_engine.recommend_improvements(plan, context)
        
        # 5. Apply recommendations if any high-confidence ones exist
        if recommendations and recommendations[0].confidence > 0.8:
            plan = self._apply_recommendations(plan, recommendations[:2])
        
        # 6. Create pipeline
        pipeline = self.combination_engine.create_pipeline(
            plan['steps'],
            strategy=ExecutionStrategy.PIPELINE,
            optimize=True
        )
        
        # 7. Execute with performance profiling
        results = {}
        performance_metrics = {}
        
        try:
            # Execute pipeline
            execution_results = await self.combination_engine.execute_pipeline(
                pipeline,
                initial_context=context or {}
            )
            
            results = execution_results
            success = all(
                r.get('status') != 'error' 
                for r in execution_results.values() 
                if isinstance(r, dict)
            )
            
            # Collect performance metrics
            for node_id, node in pipeline.nodes.items():
                if node.tool_name in self.performance_profiler.profiles:
                    profile = self.performance_profiler.get_profile(node.tool_name)
                    performance_metrics[node.tool_name] = {
                        'avg_execution_time': profile.avg_execution_time,
                        'success_rate': profile.success_rate,
                        'memory_used': profile.avg_memory_used
                    }
            
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            success = False
            results = {'error': str(e)}
        
        # 8. Learn from execution
        execution_time = asyncio.get_event_loop().time() - start_time
        execution_result = {
            'success': success,
            'execution_time': execution_time,
            'plan': plan,
            'user_request': user_request
        }
        self.recommendation_engine.learn_from_execution(plan, execution_result)
        
        # 9. Format recommendations for output
        formatted_recommendations = [
            {
                'type': rec.recommendation_type,
                'description': rec.reason,
                'confidence': rec.confidence,
                'expected_improvement': rec.expected_improvement
            }
            for rec in recommendations[:3]
        ]
        
        return EnhancedExecutionResult(
            success=success,
            results=results,
            performance_metrics=performance_metrics,
            recommendations=formatted_recommendations,
            execution_time=execution_time
        )
    
    def _create_plan_from_sequence(
        self,
        tool_sequence: List[str],
        user_request: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create execution plan from tool sequence"""
        steps = []
        previous_output = None
        
        for i, tool_name in enumerate(tool_sequence):
            # Prepare context for parameter inference
            param_context = ParameterContext(
                previous_results=previous_output or {},
                user_request=user_request,
                execution_history=[],
                similar_patterns=[]
            )
            
            # Get required parameters for tool
            tool_info = self._get_tool_info(tool_name)
            required_params = tool_info.get('required_params', [])
            
            # Infer parameters
            inferred_params, confidence = self.parameter_engine.infer_missing_params(
                tool_name,
                {},  # Start with empty params
                param_context,
                required_params
            )
            
            # Create step
            step = {
                'tool_name': tool_name,
                'parameters': inferred_params,
                'depends_on': [f"{tool_sequence[i-1]}_{i-1}"] if i > 0 else []
            }
            steps.append(step)
            
            # Update previous output reference
            previous_output = f"${{{tool_name}_{i}}}"
        
        return {
            'user_request': user_request,
            'steps': steps
        }
    
    def _create_single_tool_plan(
        self,
        tool_name: str,
        user_request: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create plan for single tool execution"""
        # Prepare context for parameter inference
        param_context = ParameterContext(
            previous_results={},
            user_request=user_request,
            execution_history=[],
            similar_patterns=[]
        )
        
        # Get required parameters
        tool_info = self._get_tool_info(tool_name)
        required_params = tool_info.get('required_params', [])
        
        # Infer parameters
        inferred_params, confidence = self.parameter_engine.infer_missing_params(
            tool_name,
            {},
            param_context,
            required_params
        )
        
        return {
            'user_request': user_request,
            'steps': [{
                'tool_name': tool_name,
                'parameters': inferred_params,
                'depends_on': []
            }]
        }
    
    def _apply_recommendations(
        self,
        plan: Dict[str, Any],
        recommendations: List[Any]
    ) -> Dict[str, Any]:
        """Apply recommendations to improve plan"""
        modified_plan = plan.copy()
        
        for rec in recommendations:
            if rec.recommendation_type == 'alternative':
                # Replace tool with recommended alternative
                for step in modified_plan['steps']:
                    if step['tool_name'] == rec.current_tool:
                        step['tool_name'] = rec.recommended_tool
                        logger.info(f"Replaced {rec.current_tool} with {rec.recommended_tool}")
            
            elif rec.recommendation_type == 'workflow':
                # Apply workflow optimizations
                if 'crawl_multiple' in rec.reason:
                    # Consolidate multiple crawl operations
                    crawl_steps = [
                        s for s in modified_plan['steps'] 
                        if 'crawl' in s['tool_name']
                    ]
                    if len(crawl_steps) > 1:
                        # Replace with single crawl_multiple
                        urls = [s['parameters'].get('url') for s in crawl_steps]
                        new_step = {
                            'tool_name': 'crawl_multiple',
                            'parameters': {'urls': urls},
                            'depends_on': []
                        }
                        # Remove individual crawl steps and add new one
                        modified_plan['steps'] = [
                            s for s in modified_plan['steps'] 
                            if 'crawl' not in s['tool_name']
                        ]
                        modified_plan['steps'].insert(0, new_step)
        
        return modified_plan
    
    def _get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get tool information from registry"""
        if self.tool_registry:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                return {
                    'required_params': getattr(tool, 'required_params', []),
                    'optional_params': getattr(tool, 'optional_params', [])
                }
        
        # Default tool info
        default_info = {
            'crawl_web': {'required_params': ['url'], 'optional_params': ['wait_for', 'screenshot']},
            'analyze_content': {'required_params': ['data'], 'optional_params': ['analysis_type']},
            'export_csv': {'required_params': ['data', 'filename'], 'optional_params': ['headers']},
            'store_data': {'required_params': ['data'], 'optional_params': ['table_name']}
        }
        
        return default_info.get(tool_name, {'required_params': [], 'optional_params': []})
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a single tool with performance profiling"""
        if self.tool_registry:
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                # Profile execution
                result, metrics = await self.performance_profiler.profile_execution(
                    tool_name,
                    tool.execute,
                    parameters
                )
                return result
        
        # Simulate tool execution
        await asyncio.sleep(0.1)
        return {
            'status': 'success',
            'data': f"Simulated result from {tool_name}"
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        return self.performance_profiler.get_performance_summary()
    
    def get_usage_analysis(self) -> Dict[str, Any]:
        """Get usage pattern analysis"""
        return self.recommendation_engine.analyze_usage_patterns()


# Usage example:
async def main():
    # Create orchestrator
    orchestrator = EnhancedToolOrchestrator()
    
    # Example requests
    test_requests = [
        "crawl https://example.com and https://test.com then compare the data and export to Excel",
        "analyze the website content for pricing information and save to database",
        "find patterns in the data and export as CSV file named analysis_results.csv"
    ]
    
    for request in test_requests:
        print(f"\n{'='*60}")
        print(f"Request: {request}")
        print('='*60)
        
        # Process request
        result = await orchestrator.process_request(request)
        
        print(f"\nSuccess: {result.success}")
        print(f"Execution time: {result.execution_time:.2f}s")
        
        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"- {rec['description']} (confidence: {rec['confidence']:.1%})")
        
        if result.performance_metrics:
            print("\nPerformance metrics:")
            for tool, metrics in result.performance_metrics.items():
                print(f"- {tool}: {metrics['avg_execution_time']:.2f}s avg, "
                      f"{metrics['success_rate']:.1%} success rate")


if __name__ == "__main__":
    asyncio.run(main())
