"""
Enhanced Tool Capabilities - Phase 6
Makes tools more intelligent with dynamic parameter discovery,
performance profiling, and capability matching.
"""

import time
import json
import statistics
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import numpy as np
from datetime import datetime, timedelta
import inspect
import re

from .registry import ToolRegistry, tool_registry


@dataclass
class ToolPerformanceMetrics:
    """Track performance metrics for tools"""
    tool_name: str
    function_name: str
    execution_times: List[float] = field(default_factory=list)
    memory_usage: List[float] = field(default_factory=list)
    success_count: int = 0
    failure_count: int = 0
    parameter_patterns: Dict[str, List[Any]] = field(default_factory=dict)
    error_patterns: List[Dict[str, Any]] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0
    
    @property
    def avg_execution_time(self) -> float:
        return statistics.mean(self.execution_times) if self.execution_times else 0.0
    
    @property
    def p95_execution_time(self) -> float:
        if not self.execution_times:
            return 0.0
        sorted_times = sorted(self.execution_times)
        idx = int(len(sorted_times) * 0.95)
        return sorted_times[idx] if idx < len(sorted_times) else sorted_times[-1]


class DynamicParameterDiscovery:
    """Discovers and suggests parameters based on context and history"""
    
    def __init__(self):
        self.parameter_history = defaultdict(lambda: defaultdict(list))
        self.successful_patterns = defaultdict(list)
        
    def record_parameters(self, tool_name: str, function_name: str, 
                         params: Dict[str, Any], success: bool):
        """Record parameter usage"""
        key = f"{tool_name}.{function_name}"
        
        # Store parameter values by name
        for param_name, param_value in params.items():
            self.parameter_history[key][param_name].append({
                'value': param_value,
                'success': success,
                'timestamp': datetime.now()
            })
        
        # Store successful parameter combinations
        if success:
            self.successful_patterns[key].append({
                'params': params.copy(),
                'timestamp': datetime.now()
            })
    
    def suggest_parameters(self, tool_name: str, function_name: str, 
                          context: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest parameters based on context and history"""
        key = f"{tool_name}.{function_name}"
        suggestions = {}
        
        # Get tool metadata
        tool_func = tool_registry.get_tool(tool_name)
        if not tool_func:
            return suggestions
        
        metadata = getattr(tool_func, '_tool_metadata', {})
        parameters = metadata.get('parameters', {})
        
        # Analyze successful patterns
        if key in self.successful_patterns:
            recent_patterns = sorted(
                self.successful_patterns[key],
                key=lambda x: x['timestamp'],
                reverse=True
            )[:10]  # Last 10 successful uses
            
            # Find most common parameter values
            param_frequencies = defaultdict(lambda: defaultdict(int))
            for pattern in recent_patterns:
                for param, value in pattern['params'].items():
                    if isinstance(value, (str, int, bool)):
                        param_frequencies[param][str(value)] += 1
            
            # Suggest most frequent values
            for param, frequencies in param_frequencies.items():
                if frequencies:
                    most_common = max(frequencies.items(), key=lambda x: x[1])
                    suggestions[param] = most_common[0]
        
        # Context-based suggestions
        if 'user_query' in context:
            query = context['user_query'].lower()
            
            # Extract patterns from query
            if 'csv' in query or 'comma' in query:
                suggestions['format'] = 'csv'
            elif 'excel' in query or 'xlsx' in query:
                suggestions['format'] = 'excel'
            elif 'json' in query:
                suggestions['format'] = 'json'
            
            # Extract numeric values
            numbers = re.findall(r'\b\d+\b', query)
            if numbers and 'limit' in parameters:
                suggestions['limit'] = int(numbers[0])
            
            # Extract date patterns
            if 'today' in query:
                suggestions['date'] = datetime.now().strftime('%Y-%m-%d')
            elif 'yesterday' in query:
                suggestions['date'] = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        
        return suggestions
    
    def validate_parameters(self, tool_name: str, function_name: str,
                           params: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate parameters against tool requirements"""
        errors = []
        tool_func = tool_registry.get_tool(tool_name)
        
        if not tool_func:
            return False, ["Tool not found"]
        
        metadata = getattr(tool_func, '_tool_metadata', {})
        parameters = metadata.get('parameters', {})
        required = metadata.get('required', [])
        
        # Check required parameters
        for req_param in required:
            if req_param not in params:
                errors.append(f"Missing required parameter: {req_param}")
        
        # Validate parameter types
        for param_name, param_value in params.items():
            if param_name in parameters:
                param_spec = parameters[param_name]
                expected_type = param_spec.get('type', 'any')
                
                # Type validation
                if expected_type == 'string' and not isinstance(param_value, str):
                    errors.append(f"{param_name} must be a string")
                elif expected_type == 'number' and not isinstance(param_value, (int, float)):
                    errors.append(f"{param_name} must be a number")
                elif expected_type == 'boolean' and not isinstance(param_value, bool):
                    errors.append(f"{param_name} must be a boolean")
                elif expected_type == 'array' and not isinstance(param_value, list):
                    errors.append(f"{param_name} must be an array")
                
                # Enum validation
                if 'enum' in param_spec and param_value not in param_spec['enum']:
                    errors.append(f"{param_name} must be one of: {param_spec['enum']}")
        
        return len(errors) == 0, errors


class ToolCombinationEngine:
    """Discovers and suggests tool combinations that work well together"""
    
    def __init__(self):
        self.combination_history = []
        self.successful_pipelines = []
        self.tool_adjacency = defaultdict(lambda: defaultdict(int))
        
    def record_combination(self, tools: List[Tuple[str, str]], success: bool,
                          execution_time: float, output_quality: float = 1.0):
        """Record a tool combination execution"""
        combination = {
            'tools': tools,
            'success': success,
            'execution_time': execution_time,
            'output_quality': output_quality,
            'timestamp': datetime.now()
        }
        
        self.combination_history.append(combination)
        
        if success:
            self.successful_pipelines.append(combination)
            
            # Update adjacency matrix
            for i in range(len(tools) - 1):
                tool1 = f"{tools[i][0]}.{tools[i][1]}"
                tool2 = f"{tools[i+1][0]}.{tools[i+1][1]}"
                self.tool_adjacency[tool1][tool2] += 1
    
    def suggest_next_tool(self, current_tool: Tuple[str, str],
                         context: Dict[str, Any]) -> List[Tuple[str, str, float]]:
        """Suggest next tools based on current tool and context"""
        current_key = f"{current_tool[0]}.{current_tool[1]}"
        suggestions = []
        
        if current_key in self.tool_adjacency:
            # Get tools that frequently follow the current tool
            for next_tool, count in self.tool_adjacency[current_key].items():
                tool_name, func_name = next_tool.split('.')
                confidence = count / sum(self.tool_adjacency[current_key].values())
                suggestions.append((tool_name, func_name, confidence))
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x[2], reverse=True)
        return suggestions[:5]  # Top 5 suggestions
    
    def find_similar_pipelines(self, planned_tools: List[Tuple[str, str]],
                               max_results: int = 5) -> List[Dict[str, Any]]:
        """Find similar successful pipelines"""
        similar_pipelines = []
        
        for pipeline in self.successful_pipelines:
            # Calculate similarity score
            pipeline_tools = pipeline['tools']
            common_tools = set(planned_tools) & set(pipeline_tools)
            
            if len(common_tools) > 0:
                similarity = len(common_tools) / max(len(planned_tools), len(pipeline_tools))
                similar_pipelines.append({
                    'pipeline': pipeline_tools,
                    'similarity': similarity,
                    'execution_time': pipeline['execution_time'],
                    'quality': pipeline['output_quality']
                })
        
        # Sort by similarity
        similar_pipelines.sort(key=lambda x: x['similarity'], reverse=True)
        return similar_pipelines[:max_results]
    
    def optimize_pipeline(self, tools: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Optimize tool execution order based on historical performance"""
        if len(tools) <= 1:
            return tools
        
        # Find if we have successful pipelines with these tools
        tool_set = set(tools)
        best_pipeline = None
        best_score = 0
        
        for pipeline in self.successful_pipelines:
            pipeline_set = set(pipeline['tools'])
            if tool_set == pipeline_set:
                # Score based on execution time and quality
                score = pipeline['output_quality'] / (1 + pipeline['execution_time'])
                if score > best_score:
                    best_score = score
                    best_pipeline = pipeline['tools']
        
        return best_pipeline if best_pipeline else tools


class PerformanceProfiler:
    """Profile tool performance and resource usage"""
    
    def __init__(self):
        self.metrics = defaultdict(lambda: ToolPerformanceMetrics("", ""))
        self.resource_limits = {
            'max_execution_time': 300,  # 5 minutes
            'max_memory_mb': 1024,      # 1GB
            'max_retries': 3
        }
    
    def start_profiling(self, tool_name: str, function_name: str) -> Dict[str, Any]:
        """Start profiling a tool execution"""
        return {
            'tool_name': tool_name,
            'function_name': function_name,
            'start_time': time.time(),
            'start_memory': self._get_memory_usage()
        }
    
    def end_profiling(self, profile_data: Dict[str, Any], success: bool,
                     params: Dict[str, Any], error: Optional[str] = None):
        """End profiling and record metrics"""
        tool_name = profile_data['tool_name']
        function_name = profile_data['function_name']
        key = f"{tool_name}.{function_name}"
        
        # Calculate metrics
        execution_time = time.time() - profile_data['start_time']
        memory_used = self._get_memory_usage() - profile_data['start_memory']
        
        # Update metrics
        metrics = self.metrics[key]
        metrics.tool_name = tool_name
        metrics.function_name = function_name
        metrics.execution_times.append(execution_time)
        metrics.memory_usage.append(memory_used)
        
        if success:
            metrics.success_count += 1
        else:
            metrics.failure_count += 1
            if error:
                metrics.error_patterns.append({
                    'error': error,
                    'params': params,
                    'timestamp': datetime.now()
                })
        
        # Record parameter patterns
        for param_name, param_value in params.items():
            if param_name not in metrics.parameter_patterns:
                metrics.parameter_patterns[param_name] = []
            metrics.parameter_patterns[param_name].append(param_value)
    
    def get_performance_report(self, tool_name: str = None,
                              function_name: str = None) -> Dict[str, Any]:
        """Get performance report for tools"""
        report = {}
        
        for key, metrics in self.metrics.items():
            if tool_name and not key.startswith(tool_name):
                continue
            if function_name and not key.endswith(function_name):
                continue
            
            report[key] = {
                'success_rate': metrics.success_rate,
                'avg_execution_time': metrics.avg_execution_time,
                'p95_execution_time': metrics.p95_execution_time,
                'total_executions': metrics.success_count + metrics.failure_count,
                'common_errors': self._analyze_error_patterns(metrics.error_patterns)
            }
        
        return report
    
    def recommend_optimizations(self, tool_name: str, function_name: str) -> List[str]:
        """Recommend optimizations based on performance data"""
        key = f"{tool_name}.{function_name}"
        recommendations = []
        
        if key not in self.metrics:
            return recommendations
        
        metrics = self.metrics[key]
        
        # Check success rate
        if metrics.success_rate < 0.8:
            recommendations.append(
                f"Low success rate ({metrics.success_rate:.1%}). "
                "Review error patterns and parameter validation."
            )
        
        # Check execution time
        if metrics.p95_execution_time > 30:
            recommendations.append(
                f"High execution time (P95: {metrics.p95_execution_time:.1f}s). "
                "Consider adding caching or optimizing the implementation."
            )
        
        # Check parameter patterns
        for param, values in metrics.parameter_patterns.items():
            if len(set(values)) == 1:
                recommendations.append(
                    f"Parameter '{param}' always has the same value. "
                    "Consider making it a default value."
                )
        
        return recommendations
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def _analyze_error_patterns(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Analyze common error patterns"""
        if not errors:
            return []
        
        error_counts = defaultdict(int)
        for error_info in errors:
            error_msg = error_info['error']
            # Simplify error message
            error_type = error_msg.split(':')[0] if ':' in error_msg else error_msg
            error_counts[error_type] += 1
        
        # Return top 3 most common errors
        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)
        return [f"{error}: {count} occurrences" for error, count in sorted_errors[:3]]


class CapabilityMatcher:
    """Match user intents to tool capabilities using semantic understanding"""
    
    def __init__(self):
        self.capability_index = {}
        self.semantic_mappings = {
            'extract': ['scrape', 'crawl', 'fetch', 'get', 'retrieve', 'pull'],
            'analyze': ['examine', 'inspect', 'study', 'investigate', 'evaluate'],
            'export': ['save', 'download', 'output', 'write', 'generate'],
            'compare': ['diff', 'contrast', 'match', 'correlate'],
            'search': ['find', 'locate', 'discover', 'query', 'lookup']
        }
        self._build_capability_index()
    
    def _build_capability_index(self):
        """Build index of tool capabilities"""
        # Use global tool_registry to get all tools
        all_tools = tool_registry.get_all_tools()
        
        for tool_name, tool_info in all_tools.items():
            # Get tool capabilities from info
            capabilities = tool_info.get('capabilities', [])
            description = tool_info.get('description', '')
            
            # Index by capability
            for capability in capabilities:
                if capability not in self.capability_index:
                    self.capability_index[capability] = []
                self.capability_index[capability].append({
                    'tool': tool_name,
                    'function': tool_name,  # Using tool_name as function for simplicity
                    'description': description
                })
    
    def find_tools_for_intent(self, user_intent: str) -> List[Dict[str, Any]]:
        """Find tools that match user intent"""
        intent_lower = user_intent.lower()
        matched_tools = []
        scores = defaultdict(float)
        
        # Direct capability matching
        for capability, tools in self.capability_index.items():
            if capability.lower() in intent_lower:
                for tool in tools:
                    key = f"{tool['tool']}.{tool['function']}"
                    scores[key] += 2.0  # Direct match weight
                    if key not in [t['key'] for t in matched_tools]:
                        matched_tools.append({
                            'key': key,
                            'tool': tool['tool'],
                            'function': tool['function'],
                            'description': tool['description'],
                            'match_type': 'capability'
                        })
        
        # Semantic matching
        for base_term, synonyms in self.semantic_mappings.items():
            if base_term in intent_lower or any(syn in intent_lower for syn in synonyms):
                # Find tools with related capabilities
                for capability, tools in self.capability_index.items():
                    if base_term in capability.lower() or any(syn in capability.lower() for syn in synonyms):
                        for tool in tools:
                            key = f"{tool['tool']}.{tool['function']}"
                            scores[key] += 1.0  # Semantic match weight
                            if key not in [t['key'] for t in matched_tools]:
                                matched_tools.append({
                                    'key': key,
                                    'tool': tool['tool'],
                                    'function': tool['function'],
                                    'description': tool['description'],
                                    'match_type': 'semantic'
                                })
        
        # Sort by score
        matched_tools.sort(key=lambda x: scores[x['key']], reverse=True)
        return matched_tools[:10]  # Top 10 matches
    
    def suggest_alternative_tools(self, tool_name: str, function_name: str) -> List[Dict[str, Any]]:
        """Suggest alternative tools with similar capabilities"""
        alternatives = []
        
        # Get current tool's capabilities
        tool_func = tool_registry.get_tool(tool_name)
        if not tool_func:
            return alternatives
        
        metadata = getattr(tool_func, '_tool_metadata', {})
        capabilities = set(metadata.get('capabilities', []))
        
        # Find tools with overlapping capabilities
        for cap in capabilities:
            if cap in self.capability_index:
                for tool in self.capability_index[cap]:
                    if tool['tool'] != tool_name or tool['function'] != function_name:
                        alternatives.append({
                            'tool': tool['tool'],
                            'function': tool['function'],
                            'shared_capability': cap,
                            'description': tool['description']
                        })
        
        # Remove duplicates and return
        seen = set()
        unique_alternatives = []
        for alt in alternatives:
            key = f"{alt['tool']}.{alt['function']}"
            if key not in seen:
                seen.add(key)
                unique_alternatives.append(alt)
        
        return unique_alternatives


class ToolRecommendationEngine:
    """Recommend new tools to create based on usage patterns and gaps"""
    
    def __init__(self, profiler: PerformanceProfiler, matcher: CapabilityMatcher):
        self.profiler = profiler
        self.matcher = matcher
        self.failed_intents = []
        self.capability_gaps = defaultdict(int)
    
    def record_failed_intent(self, user_intent: str, attempted_tools: List[Tuple[str, str]]):
        """Record when tools fail to satisfy user intent"""
        self.failed_intents.append({
            'intent': user_intent,
            'attempted_tools': attempted_tools,
            'timestamp': datetime.now()
        })
        
        # Analyze for capability gaps
        words = user_intent.lower().split()
        for word in words:
            if len(word) > 3:  # Skip short words
                self.capability_gaps[word] += 1
    
    def recommend_new_tools(self) -> List[Dict[str, Any]]:
        """Recommend new tools to implement based on gaps"""
        recommendations = []
        
        # Analyze capability gaps
        sorted_gaps = sorted(self.capability_gaps.items(), key=lambda x: x[1], reverse=True)
        
        for capability, count in sorted_gaps[:5]:  # Top 5 gaps
            if count >= 3:  # At least 3 failures
                # Check if we already have tools for this
                existing = self.matcher.find_tools_for_intent(capability)
                if not existing:
                    recommendations.append({
                        'capability': capability,
                        'frequency': count,
                        'suggested_tool': self._suggest_tool_implementation(capability),
                        'priority': 'high' if count >= 10 else 'medium'
                    })
        
        # Analyze performance bottlenecks
        perf_report = self.profiler.get_performance_report()
        for tool_key, metrics in perf_report.items():
            if metrics['avg_execution_time'] > 10 and metrics['total_executions'] > 10:
                tool_name, func_name = tool_key.split('.')
                recommendations.append({
                    'capability': f"optimized_{func_name}",
                    'frequency': metrics['total_executions'],
                    'suggested_tool': {
                        'name': f"{func_name}_fast",
                        'description': f"Optimized version of {func_name} with caching",
                        'type': 'performance_optimization'
                    },
                    'priority': 'medium'
                })
        
        return recommendations
    
    def identify_missing_combinations(self) -> List[Dict[str, Any]]:
        """Identify missing tool combinations that could be useful"""
        missing_combinations = []
        
        # Analyze failed intents that required multiple tools
        multi_tool_failures = [
            f for f in self.failed_intents 
            if len(f['attempted_tools']) > 1
        ]
        
        # Find patterns in multi-tool failures
        combination_patterns = defaultdict(int)
        for failure in multi_tool_failures:
            tools = failure['attempted_tools']
            for i in range(len(tools) - 1):
                pair = (tools[i], tools[i + 1])
                combination_patterns[pair] += 1
        
        # Recommend composite tools for common patterns
        for (tool1, tool2), count in combination_patterns.items():
            if count >= 2:
                missing_combinations.append({
                    'tools': [tool1, tool2],
                    'frequency': count,
                    'suggested_composite': {
                        'name': f"{tool1[1]}_{tool2[1]}_composite",
                        'description': f"Combines {tool1[1]} and {tool2[1]} in a single operation",
                        'benefits': "Reduces execution time and improves data flow"
                    }
                })
        
        return missing_combinations
    
    def _suggest_tool_implementation(self, capability: str) -> Dict[str, str]:
        """Suggest implementation details for a new tool"""
        # Basic heuristics for tool suggestions
        if any(word in capability for word in ['extract', 'scrape', 'fetch']):
            return {
                'name': f"{capability}_extractor",
                'description': f"Extract {capability} data from web pages",
                'type': 'data_extraction',
                'suggested_params': ['url', 'selector', 'format']
            }
        elif any(word in capability for word in ['analyze', 'detect', 'find']):
            return {
                'name': f"{capability}_analyzer",
                'description': f"Analyze data for {capability} patterns",
                'type': 'data_analysis',
                'suggested_params': ['data', 'threshold', 'output_format']
            }
        elif any(word in capability for word in ['export', 'save', 'convert']):
            return {
                'name': f"{capability}_exporter",
                'description': f"Export data in {capability} format",
                'type': 'data_export',
                'suggested_params': ['data', 'filename', 'options']
            }
        else:
            return {
                'name': f"{capability}_processor",
                'description': f"Process data for {capability}",
                'type': 'general_processing',
                'suggested_params': ['input', 'options', 'output_format']
            }


class EnhancedToolOrchestrator:
    """Main orchestrator for enhanced tool capabilities"""
    
    def __init__(self):
        self.param_discovery = DynamicParameterDiscovery()
        self.combination_engine = ToolCombinationEngine()
        self.profiler = PerformanceProfiler()
        self.capability_matcher = CapabilityMatcher()
        self.recommendation_engine = ToolRecommendationEngine(
            self.profiler, self.capability_matcher
        )
    
    def enhance_tool_execution(self, tool_name: str, function_name: str,
                              params: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance tool execution with intelligent features"""
        # Start profiling
        profile_data = self.profiler.start_profiling(tool_name, function_name)
        
        # Suggest parameters if missing
        if not params:
            params = self.param_discovery.suggest_parameters(tool_name, function_name, context)
        
        # Validate parameters
        valid, errors = self.param_discovery.validate_parameters(tool_name, function_name, params)
        if not valid:
            return {
                'success': False,
                'errors': errors,
                'suggestions': self.param_discovery.suggest_parameters(tool_name, function_name, context)
            }
        
        # Execute tool (placeholder - actual execution would happen here)
        try:
            # Tool execution would happen here
            result = {'success': True, 'data': 'Tool executed successfully'}
            
            # Record successful execution
            self.param_discovery.record_parameters(tool_name, function_name, params, True)
            self.profiler.end_profiling(profile_data, True, params)
            
            return result
            
        except Exception as e:
            # Record failure
            self.param_discovery.record_parameters(tool_name, function_name, params, False)
            self.profiler.end_profiling(profile_data, False, params, str(e))
            
            # Suggest alternatives
            alternatives = self.capability_matcher.suggest_alternative_tools(tool_name, function_name)
            
            return {
                'success': False,
                'error': str(e),
                'alternatives': alternatives
            }
    
    def optimize_tool_pipeline(self, planned_tools: List[Tuple[str, str]],
                              context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Optimize a pipeline of tools"""
        # Find similar successful pipelines
        similar = self.combination_engine.find_similar_pipelines(planned_tools)
        
        # Optimize order
        optimized_order = self.combination_engine.optimize_pipeline(planned_tools)
        
        # Enhance each step with parameter suggestions
        enhanced_pipeline = []
        for i, (tool_name, func_name) in enumerate(optimized_order):
            step_context = context.copy()
            if i > 0:
                # Add previous tool's output to context
                step_context['previous_tool'] = optimized_order[i-1]
            
            suggested_params = self.param_discovery.suggest_parameters(
                tool_name, func_name, step_context
            )
            
            # Get next tool suggestions
            next_suggestions = []
            if i < len(optimized_order) - 1:
                next_suggestions = self.combination_engine.suggest_next_tool(
                    (tool_name, func_name), step_context
                )
            
            enhanced_pipeline.append({
                'tool': tool_name,
                'function': func_name,
                'suggested_params': suggested_params,
                'next_tool_suggestions': next_suggestions,
                'performance_estimate': self._estimate_performance(tool_name, func_name)
            })
        
        return enhanced_pipeline
    
    def _estimate_performance(self, tool_name: str, function_name: str) -> Dict[str, float]:
        """Estimate performance metrics for a tool"""
        key = f"{tool_name}.{function_name}"
        if key in self.profiler.metrics:
            metrics = self.profiler.metrics[key]
            return {
                'avg_time': metrics.avg_execution_time,
                'p95_time': metrics.p95_execution_time,
                'success_rate': metrics.success_rate
            }
        return {
            'avg_time': 0.0,
            'p95_time': 0.0,
            'success_rate': 1.0
        }
    
    def get_insights_report(self) -> Dict[str, Any]:
        """Get comprehensive insights about tool usage"""
        return {
            'performance_report': self.profiler.get_performance_report(),
            'tool_recommendations': self.recommendation_engine.recommend_new_tools(),
            'missing_combinations': self.recommendation_engine.identify_missing_combinations(),
            'optimization_suggestions': self._get_optimization_suggestions()
        }
    
    def _get_optimization_suggestions(self) -> List[Dict[str, Any]]:
        """Get optimization suggestions across all tools"""
        suggestions = []
        
        for key, metrics in self.profiler.metrics.items():
            tool_name, func_name = key.split('.')
            optimizations = self.profiler.recommend_optimizations(tool_name, func_name)
            
            if optimizations:
                suggestions.append({
                    'tool': tool_name,
                    'function': func_name,
                    'suggestions': optimizations,
                    'impact': 'high' if metrics.success_rate < 0.7 else 'medium'
                })
        
        return suggestions


# Export main components
__all__ = [
    'EnhancedToolOrchestrator',
    'DynamicParameterDiscovery',
    'ToolCombinationEngine',
    'PerformanceProfiler',
    'CapabilityMatcher',
    'ToolRecommendationEngine'
]
