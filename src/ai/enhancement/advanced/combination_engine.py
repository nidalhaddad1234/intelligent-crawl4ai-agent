"""
Tool Combination Engine for Enhanced Tool Capabilities
Intelligently combines tools for complex workflows with parallel and sequential execution
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import networkx as nx
from collections import defaultdict
import time

logger = logging.getLogger(__name__)


class ExecutionStrategy(Enum):
    """Execution strategies for tool combinations"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    PIPELINE = "pipeline"


@dataclass
class ToolNode:
    """Represents a tool in the execution graph"""
    id: str
    tool_name: str
    parameters: Dict[str, Any]
    dependencies: Set[str] = field(default_factory=set)
    outputs_to: Set[str] = field(default_factory=set)
    condition: Optional[Callable] = None
    max_retries: int = 3
    timeout: Optional[float] = None


@dataclass
class ExecutionPipeline:
    """Represents a complete execution pipeline"""
    nodes: Dict[str, ToolNode]
    execution_order: List[List[str]]  # List of parallel groups
    strategy: ExecutionStrategy
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolCombinationEngine:
    """Intelligently combines tools for complex workflows"""
    
    def __init__(self, tool_registry=None, executor=None):
        self.tool_registry = tool_registry
        self.executor = executor
        self.combination_patterns = self._load_combination_patterns()
        self.optimization_rules = self._build_optimization_rules()
        
    def _load_combination_patterns(self) -> List[Dict]:
        """Load known successful tool combination patterns"""
        return [
            {
                'name': 'web_analysis',
                'pattern': ['crawl_web', 'analyze_content', 'export_*'],
                'description': 'Standard web scraping and analysis workflow'
            },
            {
                'name': 'multi_source_aggregation',
                'pattern': ['crawl_multiple', 'aggregate_data', 'detect_patterns'],
                'description': 'Aggregate data from multiple sources'
            },
            {
                'name': 'data_pipeline',
                'pattern': ['query_data', 'analyze_content', 'store_data'],
                'description': 'Data processing pipeline'
            },
            {
                'name': 'comparison_workflow',
                'pattern': ['crawl_multiple', 'compare_datasets', 'export_excel'],
                'description': 'Compare data from multiple sources'
            }
        ]
    
    def _build_optimization_rules(self) -> List[Dict]:
        """Build rules for optimizing tool combinations"""
        return [
            {
                'name': 'parallel_crawling',
                'condition': lambda nodes: self._can_parallelize_crawls(nodes),
                'optimizer': self._optimize_parallel_crawls
            },
            {
                'name': 'batch_processing',
                'condition': lambda nodes: self._can_batch_process(nodes),
                'optimizer': self._optimize_batch_processing
            },
            {
                'name': 'cache_reuse',
                'condition': lambda nodes: self._has_cacheable_results(nodes),
                'optimizer': self._optimize_with_cache
            }
        ]
    
    def suggest_combinations(
        self, 
        user_request: str,
        available_tools: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Suggest tool combinations for a user request
        
        Returns:
            List of suggested combinations with confidence scores
        """
        suggestions = []
        
        # Match against known patterns
        for pattern in self.combination_patterns:
            score = self._match_pattern_to_request(
                pattern, 
                user_request, 
                available_tools
            )
            if score > 0.5:
                suggestions.append({
                    'pattern_name': pattern['name'],
                    'tools': self._expand_pattern(pattern['pattern'], available_tools),
                    'description': pattern['description'],
                    'confidence': score
                })
        
        # Generate custom combinations
        custom_combos = self._generate_custom_combinations(
            user_request, 
            available_tools
        )
        suggestions.extend(custom_combos)
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x['confidence'], reverse=True)
        
        return suggestions[:5]  # Top 5 suggestions
    
    def create_pipeline(
        self,
        tools: List[Dict[str, Any]],
        strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL,
        optimize: bool = True
    ) -> ExecutionPipeline:
        """
        Create an execution pipeline from a list of tools
        
        Args:
            tools: List of {'tool_name': str, 'parameters': dict, 'depends_on': list}
            strategy: Execution strategy
            optimize: Whether to optimize the pipeline
            
        Returns:
            ExecutionPipeline object
        """
        # Create nodes
        nodes = {}
        for i, tool_spec in enumerate(tools):
            node_id = f"{tool_spec['tool_name']}_{i}"
            node = ToolNode(
                id=node_id,
                tool_name=tool_spec['tool_name'],
                parameters=tool_spec.get('parameters', {}),
                dependencies=set(tool_spec.get('depends_on', [])),
                timeout=tool_spec.get('timeout'),
                max_retries=tool_spec.get('max_retries', 3)
            )
            nodes[node_id] = node
        
        # Build dependency graph
        graph = self._build_dependency_graph(nodes)
        
        # Determine execution order
        if strategy == ExecutionStrategy.PARALLEL:
            execution_order = self._calculate_parallel_groups(graph, nodes)
        else:
            execution_order = self._calculate_sequential_order(graph, nodes)
        
        # Create pipeline
        pipeline = ExecutionPipeline(
            nodes=nodes,
            execution_order=execution_order,
            strategy=strategy
        )
        
        # Optimize if requested
        if optimize:
            pipeline = self._optimize_pipeline(pipeline)
        
        return pipeline
    
    async def execute_pipeline(
        self,
        pipeline: ExecutionPipeline,
        initial_context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute a pipeline asynchronously
        
        Returns:
            Results from all tool executions
        """
        if initial_context is None:
            initial_context = {}
            
        results = {}
        context = initial_context.copy()
        
        logger.info(f"Executing pipeline with strategy: {pipeline.strategy}")
        
        for group in pipeline.execution_order:
            if pipeline.strategy == ExecutionStrategy.PARALLEL:
                # Execute group in parallel
                group_results = await self._execute_parallel_group(
                    group, 
                    pipeline.nodes, 
                    context
                )
            else:
                # Execute group sequentially
                group_results = await self._execute_sequential_group(
                    group, 
                    pipeline.nodes, 
                    context
                )
            
            # Update results and context
            results.update(group_results)
            context.update(group_results)
        
        return results
    
    def _build_dependency_graph(
        self, 
        nodes: Dict[str, ToolNode]
    ) -> nx.DiGraph:
        """Build a directed graph of tool dependencies"""
        graph = nx.DiGraph()
        
        # Add nodes
        for node_id in nodes:
            graph.add_node(node_id)
        
        # Add edges based on dependencies
        for node_id, node in nodes.items():
            for dep in node.dependencies:
                if dep in nodes:
                    graph.add_edge(dep, node_id)
        
        # Detect cycles
        if not nx.is_directed_acyclic_graph(graph):
            cycles = list(nx.simple_cycles(graph))
            raise ValueError(f"Circular dependencies detected: {cycles}")
        
        return graph
    
    def _calculate_parallel_groups(
        self, 
        graph: nx.DiGraph, 
        nodes: Dict[str, ToolNode]
    ) -> List[List[str]]:
        """Calculate groups of tools that can run in parallel"""
        # Use topological generations (levels)
        generations = list(nx.topological_generations(graph))
        
        # Convert to list of node IDs
        parallel_groups = []
        for generation in generations:
            group = list(generation)
            parallel_groups.append(group)
        
        logger.info(f"Calculated {len(parallel_groups)} parallel groups")
        return parallel_groups
    
    def _calculate_sequential_order(
        self, 
        graph: nx.DiGraph, 
        nodes: Dict[str, ToolNode]
    ) -> List[List[str]]:
        """Calculate sequential execution order"""
        # Topological sort
        try:
            order = list(nx.topological_sort(graph))
        except nx.NetworkXUnfeasible:
            raise ValueError("Cannot create sequential order due to circular dependencies")
        
        # Each tool in its own group
        return [[node_id] for node_id in order]
    
    async def _execute_parallel_group(
        self,
        group: List[str],
        nodes: Dict[str, ToolNode],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a group of tools in parallel"""
        logger.info(f"Executing parallel group: {group}")
        
        tasks = []
        for node_id in group:
            node = nodes[node_id]
            task = self._execute_tool(node, context)
            tasks.append((node_id, task))
        
        # Execute all tasks in parallel
        results = {}
        task_results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )
        
        # Process results
        for i, (node_id, _) in enumerate(tasks):
            if isinstance(task_results[i], Exception):
                logger.error(f"Tool {node_id} failed: {task_results[i]}")
                results[node_id] = {
                    'status': 'error',
                    'error': str(task_results[i])
                }
            else:
                results[node_id] = task_results[i]
        
        return results
    
    async def _execute_sequential_group(
        self,
        group: List[str],
        nodes: Dict[str, ToolNode],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a group of tools sequentially"""
        results = {}
        
        for node_id in group:
            node = nodes[node_id]
            try:
                result = await self._execute_tool(node, context)
                results[node_id] = result
                context[node_id] = result  # Add to context for next tools
            except Exception as e:
                logger.error(f"Tool {node_id} failed: {e}")
                results[node_id] = {
                    'status': 'error',
                    'error': str(e)
                }
                # Decide whether to continue or stop
                if node.max_retries == 0:  # Critical tool
                    raise
        
        return results
    
    async def _execute_tool(
        self,
        node: ToolNode,
        context: Dict[str, Any]
    ) -> Any:
        """Execute a single tool with retries and timeout"""
        logger.info(f"Executing tool: {node.tool_name}")
        
        # Check condition if exists
        if node.condition and not node.condition(context):
            logger.info(f"Skipping {node.tool_name} - condition not met")
            return {'status': 'skipped'}
        
        # Prepare parameters with context
        params = self._prepare_parameters(node.parameters, context)
        
        # Execute with retries
        last_error = None
        for attempt in range(node.max_retries):
            try:
                if self.executor:
                    # Use provided executor
                    if node.timeout:
                        result = await asyncio.wait_for(
                            self.executor.execute_tool(node.tool_name, params),
                            timeout=node.timeout
                        )
                    else:
                        result = await self.executor.execute_tool(node.tool_name, params)
                else:
                    # Simulate execution
                    await asyncio.sleep(0.1)  # Simulate work
                    result = {
                        'status': 'success',
                        'data': f"Result from {node.tool_name}"
                    }
                
                return result
                
            except asyncio.TimeoutError:
                last_error = f"Timeout after {node.timeout}s"
                logger.warning(f"Tool {node.tool_name} timed out (attempt {attempt + 1})")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Tool {node.tool_name} failed (attempt {attempt + 1}): {e}")
            
            if attempt < node.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise Exception(f"Tool {node.tool_name} failed after {node.max_retries} attempts: {last_error}")
    
    def _prepare_parameters(
        self,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare parameters by resolving references to context"""
        resolved_params = {}
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                # Reference to context
                ref = value[2:-1]
                if '.' in ref:
                    # Nested reference like ${tool1.data}
                    parts = ref.split('.')
                    resolved_value = context
                    for part in parts:
                        if isinstance(resolved_value, dict) and part in resolved_value:
                            resolved_value = resolved_value[part]
                        else:
                            resolved_value = None
                            break
                    resolved_params[key] = resolved_value
                else:
                    resolved_params[key] = context.get(ref)
            else:
                resolved_params[key] = value
        
        return resolved_params
    
    def _optimize_pipeline(self, pipeline: ExecutionPipeline) -> ExecutionPipeline:
        """Apply optimization rules to the pipeline"""
        logger.info("Optimizing pipeline")
        
        for rule in self.optimization_rules:
            if rule['condition'](pipeline.nodes):
                pipeline = rule['optimizer'](pipeline)
                logger.info(f"Applied optimization: {rule['name']}")
        
        return pipeline
    
    def _can_parallelize_crawls(self, nodes: Dict[str, ToolNode]) -> bool:
        """Check if multiple crawl operations can be parallelized"""
        crawl_nodes = [
            node for node in nodes.values() 
            if 'crawl' in node.tool_name
        ]
        return len(crawl_nodes) > 1
    
    def _optimize_parallel_crawls(
        self, 
        pipeline: ExecutionPipeline
    ) -> ExecutionPipeline:
        """Optimize by parallelizing crawl operations"""
        # Identify crawl nodes
        crawl_nodes = []
        for group in pipeline.execution_order:
            for node_id in group:
                if 'crawl' in pipeline.nodes[node_id].tool_name:
                    crawl_nodes.append(node_id)
        
        if len(crawl_nodes) > 1:
            # Remove crawl nodes from their current positions
            new_order = []
            for group in pipeline.execution_order:
                new_group = [n for n in group if n not in crawl_nodes]
                if new_group:
                    new_order.append(new_group)
            
            # Add all crawl nodes as first parallel group
            new_order.insert(0, crawl_nodes)
            pipeline.execution_order = new_order
            pipeline.strategy = ExecutionStrategy.PIPELINE
        
        return pipeline
    
    def _can_batch_process(self, nodes: Dict[str, ToolNode]) -> bool:
        """Check if operations can be batched"""
        # Look for multiple operations on similar data
        analyze_nodes = [
            node for node in nodes.values() 
            if node.tool_name == 'analyze_content'
        ]
        return len(analyze_nodes) > 1
    
    def _optimize_batch_processing(
        self, 
        pipeline: ExecutionPipeline
    ) -> ExecutionPipeline:
        """Optimize by batching similar operations"""
        # Implementation would batch similar operations
        # This is a placeholder for the concept
        return pipeline
    
    def _has_cacheable_results(self, nodes: Dict[str, ToolNode]) -> bool:
        """Check if any results could be cached and reused"""
        # Look for repeated operations
        tool_counts = defaultdict(int)
        for node in nodes.values():
            tool_counts[node.tool_name] += 1
        
        return any(count > 1 for count in tool_counts.values())
    
    def _optimize_with_cache(
        self, 
        pipeline: ExecutionPipeline
    ) -> ExecutionPipeline:
        """Optimize by adding cache checks"""
        # Add cache metadata
        pipeline.metadata['use_cache'] = True
        return pipeline
    
    def _match_pattern_to_request(
        self,
        pattern: Dict,
        user_request: str,
        available_tools: List[str]
    ) -> float:
        """Calculate how well a pattern matches the user request"""
        score = 0.0
        request_lower = user_request.lower()
        
        # Check if pattern tools are available
        pattern_tools = self._expand_pattern(pattern['pattern'], available_tools)
        if not pattern_tools:
            return 0.0
        
        # Check for keywords
        keywords = {
            'web_analysis': ['analyze', 'website', 'scrape', 'extract'],
            'multi_source_aggregation': ['multiple', 'aggregate', 'combine', 'sources'],
            'data_pipeline': ['process', 'transform', 'pipeline'],
            'comparison_workflow': ['compare', 'difference', 'versus']
        }
        
        if pattern['name'] in keywords:
            matches = sum(
                1 for keyword in keywords[pattern['name']]
                if keyword in request_lower
            )
            score = matches / len(keywords[pattern['name']])
        
        return score
    
    def _expand_pattern(
        self,
        pattern: List[str],
        available_tools: List[str]
    ) -> List[str]:
        """Expand pattern wildcards to actual tools"""
        expanded = []
        
        for pattern_tool in pattern:
            if '*' in pattern_tool:
                # Wildcard pattern
                prefix = pattern_tool.replace('*', '')
                matches = [
                    tool for tool in available_tools 
                    if tool.startswith(prefix)
                ]
                expanded.extend(matches[:1])  # Take first match
            else:
                if pattern_tool in available_tools:
                    expanded.append(pattern_tool)
        
        return expanded
    
    def _generate_custom_combinations(
        self,
        user_request: str,
        available_tools: List[str]
    ) -> List[Dict[str, Any]]:
        """Generate custom tool combinations based on request analysis"""
        # This is a simplified version
        # A real implementation would use NLP to understand the request
        
        combinations = []
        
        # Simple heuristic-based generation
        if 'crawl' in user_request.lower() and 'analyze' in user_request.lower():
            tools = []
            for tool in available_tools:
                if 'crawl' in tool:
                    tools.append(tool)
                    break
            for tool in available_tools:
                if 'analyze' in tool:
                    tools.append(tool)
                    break
            
            if len(tools) == 2:
                combinations.append({
                    'pattern_name': 'custom_crawl_analyze',
                    'tools': tools,
                    'description': 'Custom crawl and analyze workflow',
                    'confidence': 0.7
                })
        
        return combinations


# Usage example:
if __name__ == "__main__":
    # Example usage
    engine = ToolCombinationEngine()
    
    # Suggest combinations
    suggestions = engine.suggest_combinations(
        "crawl multiple websites and compare their pricing data",
        ['crawl_web', 'crawl_multiple', 'analyze_content', 'compare_datasets', 'export_excel']
    )
    
    print("Suggestions:")
    for s in suggestions:
        print(f"- {s['pattern_name']}: {s['tools']} (confidence: {s['confidence']:.2f})")
    
    # Create pipeline
    tools = [
        {'tool_name': 'crawl_multiple', 'parameters': {'urls': ['url1', 'url2']}},
        {'tool_name': 'analyze_content', 'parameters': {'data': '${crawl_multiple_0}'}, 'depends_on': ['crawl_multiple_0']},
        {'tool_name': 'export_excel', 'parameters': {'data': '${analyze_content_1}'}, 'depends_on': ['analyze_content_1']}
    ]
    
    pipeline = engine.create_pipeline(tools, ExecutionStrategy.SEQUENTIAL)
    print(f"\nPipeline created with {len(pipeline.nodes)} nodes")
    print(f"Execution order: {pipeline.execution_order}")
