"""
Tool Recommendation Engine for Enhanced Tool Capabilities
Suggests better tools and optimizations based on usage patterns
"""

import json
import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


@dataclass
class UsagePattern:
    """Represents a tool usage pattern"""
    pattern_id: str
    tool_sequence: List[str]
    frequency: int
    avg_execution_time: float
    success_rate: float
    common_parameters: Dict[str, Any]
    user_requests: List[str]
    last_used: datetime
    
    @property
    def efficiency_score(self) -> float:
        """Calculate efficiency score based on time and success"""
        if self.avg_execution_time == 0:
            return 0
        return self.success_rate / (self.avg_execution_time / 60)  # Success per minute


@dataclass
class ToolRecommendation:
    """A recommendation for tool improvement"""
    recommendation_type: str  # 'alternative', 'parameter', 'combination', 'workflow'
    current_tool: Optional[str]
    recommended_tool: Optional[str]
    reason: str
    expected_improvement: Dict[str, float]  # e.g., {'execution_time': -30, 'success_rate': 10}
    confidence: float  # 0-1
    examples: List[str] = field(default_factory=list)


class ToolRecommendationEngine:
    """Analyzes usage patterns and recommends improvements"""
    
    def __init__(
        self,
        learning_memory=None,
        performance_profiler=None,
        capability_matcher=None
    ):
        self.learning_memory = learning_memory
        self.performance_profiler = performance_profiler
        self.capability_matcher = capability_matcher
        
        self.usage_patterns: Dict[str, UsagePattern] = {}
        self.tool_substitutions: Dict[str, List[str]] = self._load_tool_substitutions()
        self.optimization_rules = self._build_optimization_rules()
        
        # Pattern clustering
        self.pattern_clusters = None
        self.scaler = StandardScaler()
    
    def _load_tool_substitutions(self) -> Dict[str, List[str]]:
        """Load known tool substitutions"""
        return {
            'crawl_web': ['crawl_multiple'],  # Can use multiple for single URL
            'export_json': ['export_csv', 'export_excel'],  # Alternative formats
            'analyze_content': ['detect_patterns'],  # More specific analysis
            'store_data': ['export_csv', 'export_json'],  # Alternative to storing
        }
    
    def _build_optimization_rules(self) -> List[Dict]:
        """Build rules for optimization recommendations"""
        return [
            {
                'name': 'parallel_opportunity',
                'condition': self._check_parallel_opportunity,
                'recommender': self._recommend_parallelization
            },
            {
                'name': 'redundant_operations',
                'condition': self._check_redundant_operations,
                'recommender': self._recommend_deduplication
            },
            {
                'name': 'inefficient_sequence',
                'condition': self._check_inefficient_sequence,
                'recommender': self._recommend_better_sequence
            },
            {
                'name': 'parameter_optimization',
                'condition': self._check_parameter_patterns,
                'recommender': self._recommend_parameter_optimization
            }
        ]
    
    def analyze_usage_patterns(
        self,
        time_window: Optional[timedelta] = None
    ) -> Dict[str, Any]:
        """
        Analyze tool usage patterns
        
        Returns:
            Analysis results with patterns and insights
        """
        if not self.learning_memory:
            return {'error': 'Learning memory not available'}
        
        # Get execution history
        executions = self._get_execution_history(time_window)
        
        # Extract patterns
        self.usage_patterns = self._extract_usage_patterns(executions)
        
        # Cluster similar patterns
        if len(self.usage_patterns) > 5:
            self._cluster_patterns()
        
        # Analyze patterns
        analysis = {
            'total_patterns': len(self.usage_patterns),
            'most_common_patterns': self._get_most_common_patterns(5),
            'most_efficient_patterns': self._get_most_efficient_patterns(5),
            'problematic_patterns': self._get_problematic_patterns(),
            'tool_usage_stats': self._get_tool_usage_stats(executions),
            'pattern_clusters': self._describe_pattern_clusters() if self.pattern_clusters else None
        }
        
        return analysis
    
    def recommend_improvements(
        self,
        current_plan: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> List[ToolRecommendation]:
        """
        Recommend improvements for a given plan
        
        Args:
            current_plan: Current execution plan
            context: Additional context
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Apply optimization rules
        for rule in self.optimization_rules:
            if rule['condition'](current_plan):
                rule_recommendations = rule['recommender'](current_plan, context)
                recommendations.extend(rule_recommendations)
        
        # Check for better tool alternatives
        alt_recommendations = self._recommend_tool_alternatives(current_plan)
        recommendations.extend(alt_recommendations)
        
        # Check for similar successful patterns
        pattern_recommendations = self._recommend_from_patterns(current_plan)
        recommendations.extend(pattern_recommendations)
        
        # Sort by confidence
        recommendations.sort(key=lambda r: r.confidence, reverse=True)
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _get_execution_history(
        self,
        time_window: Optional[timedelta]
    ) -> List[Dict[str, Any]]:
        """Get execution history from learning memory"""
        if not self.learning_memory:
            return []
        
        # This would interface with the actual learning memory
        # For now, return mock data
        return []
    
    def _extract_usage_patterns(
        self,
        executions: List[Dict[str, Any]]
    ) -> Dict[str, UsagePattern]:
        """Extract usage patterns from executions"""
        pattern_data = defaultdict(lambda: {
            'tool_sequences': [],
            'execution_times': [],
            'success_count': 0,
            'total_count': 0,
            'parameters': [],
            'requests': []
        })
        
        # Group executions by tool sequence
        for execution in executions:
            if 'plan' in execution and 'steps' in execution['plan']:
                # Extract tool sequence
                tool_sequence = [
                    step['tool'] for step in execution['plan']['steps']
                ]
                pattern_key = '->'.join(tool_sequence)
                
                # Update pattern data
                data = pattern_data[pattern_key]
                data['tool_sequences'].append(tool_sequence)
                data['execution_times'].append(execution.get('execution_time', 0))
                data['total_count'] += 1
                if execution.get('success', False):
                    data['success_count'] += 1
                data['parameters'].extend(execution.get('parameters', []))
                data['requests'].append(execution.get('user_request', ''))
        
        # Convert to UsagePattern objects
        patterns = {}
        for pattern_key, data in pattern_data.items():
            if data['tool_sequences']:
                pattern = UsagePattern(
                    pattern_id=pattern_key,
                    tool_sequence=data['tool_sequences'][0],
                    frequency=data['total_count'],
                    avg_execution_time=np.mean(data['execution_times']) if data['execution_times'] else 0,
                    success_rate=data['success_count'] / data['total_count'] if data['total_count'] > 0 else 0,
                    common_parameters=self._extract_common_parameters(data['parameters']),
                    user_requests=list(set(data['requests']))[:5],  # Keep top 5 unique requests
                    last_used=datetime.now()  # Would be from actual data
                )
                patterns[pattern_key] = pattern
        
        return patterns
    
    def _extract_common_parameters(
        self,
        parameters_list: List[Dict]
    ) -> Dict[str, Any]:
        """Extract most common parameters from a list"""
        if not parameters_list:
            return {}
        
        # Count parameter values
        param_counts = defaultdict(Counter)
        for params in parameters_list:
            for key, value in params.items():
                if isinstance(value, (str, int, bool)):
                    param_counts[key][value] += 1
        
        # Get most common values
        common_params = {}
        for key, counter in param_counts.items():
            most_common = counter.most_common(1)[0]
            common_params[key] = most_common[0]
        
        return common_params
    
    def _cluster_patterns(self):
        """Cluster similar usage patterns"""
        if not self.usage_patterns:
            return
        
        # Create feature vectors
        features = []
        pattern_ids = []
        
        for pattern_id, pattern in self.usage_patterns.items():
            feature_vector = [
                len(pattern.tool_sequence),
                pattern.frequency,
                pattern.avg_execution_time,
                pattern.success_rate,
                pattern.efficiency_score
            ]
            features.append(feature_vector)
            pattern_ids.append(pattern_id)
        
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Cluster
        n_clusters = min(5, len(features) // 3)
        if n_clusters > 1:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            self.pattern_clusters = kmeans.fit_predict(features_scaled)
    
    def _get_most_common_patterns(self, limit: int) -> List[Dict[str, Any]]:
        """Get most frequently used patterns"""
        sorted_patterns = sorted(
            self.usage_patterns.values(),
            key=lambda p: p.frequency,
            reverse=True
        )
        
        return [
            {
                'pattern': p.pattern_id,
                'tools': p.tool_sequence,
                'frequency': p.frequency,
                'success_rate': p.success_rate,
                'avg_time': p.avg_execution_time
            }
            for p in sorted_patterns[:limit]
        ]
    
    def _get_most_efficient_patterns(self, limit: int) -> List[Dict[str, Any]]:
        """Get most efficient patterns"""
        sorted_patterns = sorted(
            self.usage_patterns.values(),
            key=lambda p: p.efficiency_score,
            reverse=True
        )
        
        return [
            {
                'pattern': p.pattern_id,
                'tools': p.tool_sequence,
                'efficiency_score': p.efficiency_score,
                'success_rate': p.success_rate,
                'avg_time': p.avg_execution_time
            }
            for p in sorted_patterns[:limit]
        ]
    
    def _get_problematic_patterns(self) -> List[Dict[str, Any]]:
        """Identify patterns with issues"""
        problematic = []
        
        for pattern in self.usage_patterns.values():
            issues = []
            
            if pattern.success_rate < 0.7:
                issues.append(f"Low success rate: {pattern.success_rate:.1%}")
            
            if pattern.avg_execution_time > 60:
                issues.append(f"Slow execution: {pattern.avg_execution_time:.1f}s")
            
            if pattern.efficiency_score < 0.5:
                issues.append(f"Low efficiency: {pattern.efficiency_score:.2f}")
            
            if issues:
                problematic.append({
                    'pattern': pattern.pattern_id,
                    'tools': pattern.tool_sequence,
                    'issues': issues,
                    'frequency': pattern.frequency
                })
        
        return problematic
    
    def _get_tool_usage_stats(
        self,
        executions: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """Get usage statistics per tool"""
        tool_stats = defaultdict(lambda: {
            'usage_count': 0,
            'success_count': 0,
            'total_time': 0,
            'common_next_tools': Counter(),
            'common_prev_tools': Counter()
        })
        
        # Aggregate stats
        for execution in executions:
            if 'plan' in execution and 'steps' in execution['plan']:
                steps = execution['plan']['steps']
                success = execution.get('success', False)
                
                for i, step in enumerate(steps):
                    tool = step['tool']
                    stats = tool_stats[tool]
                    
                    stats['usage_count'] += 1
                    if success:
                        stats['success_count'] += 1
                    stats['total_time'] += step.get('execution_time', 0)
                    
                    # Track tool sequences
                    if i > 0:
                        stats['common_prev_tools'][steps[i-1]['tool']] += 1
                    if i < len(steps) - 1:
                        stats['common_next_tools'][steps[i+1]['tool']] += 1
        
        # Format results
        formatted_stats = {}
        for tool, stats in tool_stats.items():
            formatted_stats[tool] = {
                'usage_count': stats['usage_count'],
                'success_rate': stats['success_count'] / stats['usage_count'] if stats['usage_count'] > 0 else 0,
                'avg_execution_time': stats['total_time'] / stats['usage_count'] if stats['usage_count'] > 0 else 0,
                'common_next_tools': dict(stats['common_next_tools'].most_common(3)),
                'common_prev_tools': dict(stats['common_prev_tools'].most_common(3))
            }
        
        return formatted_stats
    
    def _describe_pattern_clusters(self) -> List[Dict[str, Any]]:
        """Describe pattern clusters"""
        if self.pattern_clusters is None:
            return []
        
        clusters = defaultdict(list)
        pattern_list = list(self.usage_patterns.values())
        
        for i, cluster_id in enumerate(self.pattern_clusters):
            clusters[cluster_id].append(pattern_list[i])
        
        descriptions = []
        for cluster_id, patterns in clusters.items():
            # Calculate cluster characteristics
            avg_length = np.mean([len(p.tool_sequence) for p in patterns])
            avg_efficiency = np.mean([p.efficiency_score for p in patterns])
            common_tools = Counter()
            
            for pattern in patterns:
                common_tools.update(pattern.tool_sequence)
            
            descriptions.append({
                'cluster_id': int(cluster_id),
                'pattern_count': len(patterns),
                'avg_sequence_length': avg_length,
                'avg_efficiency_score': avg_efficiency,
                'common_tools': dict(common_tools.most_common(5)),
                'example_patterns': [p.pattern_id for p in patterns[:3]]
            })
        
        return descriptions
    
    def _check_parallel_opportunity(self, plan: Dict[str, Any]) -> bool:
        """Check if plan has parallelization opportunities"""
        if 'steps' not in plan:
            return False
        
        # Look for multiple similar operations
        tool_counts = Counter(step['tool'] for step in plan['steps'])
        return any(count > 1 for count in tool_counts.values())
    
    def _recommend_parallelization(
        self,
        plan: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[ToolRecommendation]:
        """Recommend parallelization opportunities"""
        recommendations = []
        
        # Find tools that appear multiple times
        tool_counts = Counter(step['tool'] for step in plan['steps'])
        
        for tool, count in tool_counts.items():
            if count > 1 and 'crawl' in tool:  # Example: crawling can be parallelized
                recommendations.append(ToolRecommendation(
                    recommendation_type='workflow',
                    current_tool=tool,
                    recommended_tool='crawl_multiple',
                    reason=f"Detected {count} sequential {tool} operations that could run in parallel",
                    expected_improvement={
                        'execution_time': -60,  # 60% reduction
                        'efficiency': 50  # 50% improvement
                    },
                    confidence=0.8,
                    examples=["Use crawl_multiple with all URLs at once instead of multiple crawl_web calls"]
                ))
        
        return recommendations
    
    def _check_redundant_operations(self, plan: Dict[str, Any]) -> bool:
        """Check for redundant operations in plan"""
        if 'steps' not in plan:
            return False
        
        # Check for repeated tool sequences
        tool_sequence = [step['tool'] for step in plan['steps']]
        return len(tool_sequence) != len(set(tool_sequence))
    
    def _recommend_deduplication(
        self,
        plan: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[ToolRecommendation]:
        """Recommend removing redundant operations"""
        recommendations = []
        
        tool_sequence = [step['tool'] for step in plan['steps']]
        seen = set()
        
        for i, tool in enumerate(tool_sequence):
            if tool in seen and tool not in ['export_csv', 'export_json']:  # Some tools can legitimately repeat
                recommendations.append(ToolRecommendation(
                    recommendation_type='workflow',
                    current_tool=tool,
                    recommended_tool=None,
                    reason=f"Tool '{tool}' appears multiple times - consider consolidating",
                    expected_improvement={
                        'execution_time': -30,
                        'complexity': -20
                    },
                    confidence=0.7,
                    examples=["Combine multiple operations into a single call"]
                ))
            seen.add(tool)
        
        return recommendations
    
    def _check_inefficient_sequence(self, plan: Dict[str, Any]) -> bool:
        """Check for inefficient tool sequences"""
        if 'steps' not in plan or len(plan['steps']) < 2:
            return False
        
        # Check known inefficient patterns
        tool_sequence = [step['tool'] for step in plan['steps']]
        inefficient_patterns = [
            ['store_data', 'query_data'],  # Storing then immediately querying
            ['export_json', 'export_csv'],  # Multiple exports of same data
        ]
        
        for pattern in inefficient_patterns:
            if all(tool in tool_sequence for tool in pattern):
                return True
        
        return False
    
    def _recommend_better_sequence(
        self,
        plan: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[ToolRecommendation]:
        """Recommend more efficient sequences"""
        recommendations = []
        tool_sequence = [step['tool'] for step in plan['steps']]
        
        # Check for store->query pattern
        for i in range(len(tool_sequence) - 1):
            if tool_sequence[i] == 'store_data' and tool_sequence[i+1] == 'query_data':
                recommendations.append(ToolRecommendation(
                    recommendation_type='workflow',
                    current_tool=None,
                    recommended_tool=None,
                    reason="Detected store followed by immediate query - consider processing data directly",
                    expected_improvement={
                        'execution_time': -40,
                        'complexity': -30
                    },
                    confidence=0.8,
                    examples=["Process data in memory instead of storing and retrieving"]
                ))
        
        return recommendations
    
    def _check_parameter_patterns(self, plan: Dict[str, Any]) -> bool:
        """Check if parameters could be optimized"""
        # This would analyze parameter patterns
        # For now, always return True to check parameters
        return True
    
    def _recommend_parameter_optimization(
        self,
        plan: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> List[ToolRecommendation]:
        """Recommend parameter optimizations"""
        recommendations = []
        
        # Example: Check for missing batch sizes
        for step in plan.get('steps', []):
            if 'parameters' in step:
                params = step['parameters']
                
                # Check for missing optimization parameters
                if step['tool'] in ['crawl_multiple', 'query_data'] and 'batch_size' not in params:
                    recommendations.append(ToolRecommendation(
                        recommendation_type='parameter',
                        current_tool=step['tool'],
                        recommended_tool=None,
                        reason="Consider adding batch_size parameter for better performance",
                        expected_improvement={
                            'execution_time': -20,
                            'memory_usage': -30
                        },
                        confidence=0.6,
                        examples=["Add 'batch_size': 10 to process in chunks"]
                    ))
        
        return recommendations
    
    def _recommend_tool_alternatives(
        self,
        plan: Dict[str, Any]
    ) -> List[ToolRecommendation]:
        """Recommend alternative tools"""
        recommendations = []
        
        for step in plan.get('steps', []):
            tool = step['tool']
            
            # Check if there are known better alternatives
            if tool in self.tool_substitutions:
                alternatives = self.tool_substitutions[tool]
                
                # Get performance data if available
                if self.performance_profiler:
                    current_profile = self.performance_profiler.get_profile(tool)
                    
                    for alt_tool in alternatives:
                        alt_profile = self.performance_profiler.get_profile(alt_tool)
                        
                        if alt_profile and current_profile:
                            # Compare performance
                            if alt_profile.avg_execution_time < current_profile.avg_execution_time * 0.7:
                                recommendations.append(ToolRecommendation(
                                    recommendation_type='alternative',
                                    current_tool=tool,
                                    recommended_tool=alt_tool,
                                    reason=f"{alt_tool} is {(1 - alt_profile.avg_execution_time/current_profile.avg_execution_time)*100:.0f}% faster",
                                    expected_improvement={
                                        'execution_time': -(1 - alt_profile.avg_execution_time/current_profile.avg_execution_time)*100
                                    },
                                    confidence=0.9,
                                    examples=[f"Replace {tool} with {alt_tool}"]
                                ))
        
        return recommendations
    
    def _recommend_from_patterns(
        self,
        plan: Dict[str, Any]
    ) -> List[ToolRecommendation]:
        """Recommend based on successful patterns"""
        recommendations = []
        
        # Extract current tool sequence
        current_sequence = [step['tool'] for step in plan.get('steps', [])]
        current_key = '->'.join(current_sequence)
        
        # Find similar successful patterns
        for pattern in self.usage_patterns.values():
            if pattern.success_rate > 0.9 and pattern.efficiency_score > 1.0:
                # Check if pattern is similar but more efficient
                if len(pattern.tool_sequence) == len(current_sequence):
                    differences = sum(
                        1 for a, b in zip(pattern.tool_sequence, current_sequence) 
                        if a != b
                    )
                    
                    if 0 < differences <= 2:  # Similar but not identical
                        recommendations.append(ToolRecommendation(
                            recommendation_type='combination',
                            current_tool=None,
                            recommended_tool=None,
                            reason=f"Similar pattern '{pattern.pattern_id}' has {pattern.success_rate:.0%} success rate",
                            expected_improvement={
                                'success_rate': (pattern.success_rate - 0.7) * 100
                            },
                            confidence=0.7,
                            examples=[f"Use sequence: {' -> '.join(pattern.tool_sequence)}"]
                        ))
        
        return recommendations[:2]  # Limit pattern recommendations
    
    def learn_from_execution(
        self,
        plan: Dict[str, Any],
        execution_result: Dict[str, Any]
    ):
        """Learn from an execution to improve recommendations"""
        # Extract tool sequence
        tool_sequence = [step['tool'] for step in plan.get('steps', [])]
        pattern_key = '->'.join(tool_sequence)
        
        # Update or create pattern
        if pattern_key in self.usage_patterns:
            pattern = self.usage_patterns[pattern_key]
            # Update pattern statistics
            pattern.frequency += 1
            pattern.last_used = datetime.now()
            # Update success rate and execution time
            # This would be more sophisticated in real implementation
        else:
            # Create new pattern
            self.usage_patterns[pattern_key] = UsagePattern(
                pattern_id=pattern_key,
                tool_sequence=tool_sequence,
                frequency=1,
                avg_execution_time=execution_result.get('execution_time', 0),
                success_rate=1.0 if execution_result.get('success', False) else 0.0,
                common_parameters={},
                user_requests=[plan.get('user_request', '')],
                last_used=datetime.now()
            )
    
    def export_recommendations(
        self,
        filepath: str,
        include_patterns: bool = True
    ):
        """Export recommendations and patterns to file"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'usage_analysis': self.analyze_usage_patterns(),
            'optimization_rules': [
                {
                    'name': rule['name'],
                    'description': rule['recommender'].__doc__.strip()
                }
                for rule in self.optimization_rules
            ]
        }
        
        if include_patterns:
            export_data['patterns'] = {
                pattern_id: {
                    'tools': pattern.tool_sequence,
                    'frequency': pattern.frequency,
                    'efficiency_score': pattern.efficiency_score,
                    'success_rate': pattern.success_rate
                }
                for pattern_id, pattern in self.usage_patterns.items()
            }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported recommendations to {filepath}")


# Usage example:
if __name__ == "__main__":
    # Create recommendation engine
    engine = ToolRecommendationEngine()
    
    # Example plan
    test_plan = {
        'steps': [
            {'tool': 'crawl_web', 'parameters': {'url': 'example1.com'}},
            {'tool': 'crawl_web', 'parameters': {'url': 'example2.com'}},
            {'tool': 'analyze_content', 'parameters': {'data': '${crawl_web}'}},
            {'tool': 'store_data', 'parameters': {'table': 'results'}},
            {'tool': 'query_data', 'parameters': {'table': 'results'}},
            {'tool': 'export_csv', 'parameters': {'filename': 'output.csv'}}
        ]
    }
    
    # Get recommendations
    recommendations = engine.recommend_improvements(test_plan)
    
    print("Recommendations:")
    for rec in recommendations:
        print(f"\nType: {rec.recommendation_type}")
        print(f"Reason: {rec.reason}")
        print(f"Expected improvement: {rec.expected_improvement}")
        print(f"Confidence: {rec.confidence:.1%}")
        if rec.examples:
            print(f"Examples: {', '.join(rec.examples)}")
    
    # Analyze patterns
    analysis = engine.analyze_usage_patterns()
    print(f"\n\nUsage Analysis:")
    print(json.dumps(analysis, indent=2))
