"""
Performance Profiler for Enhanced Tool Capabilities
Tracks and optimizes tool execution performance with detailed metrics
"""

import time
import psutil
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import tracemalloc
import threading

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a single tool execution"""
    tool_name: str
    start_time: float
    end_time: float
    execution_time: float
    memory_before: float
    memory_after: float
    memory_peak: float
    cpu_percent: float
    success: bool
    error: Optional[str] = None
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def memory_used(self) -> float:
        """Memory used during execution (MB)"""
        return self.memory_after - self.memory_before
    
    @property
    def throughput(self) -> Optional[float]:
        """Data throughput (bytes/second)"""
        if self.input_size and self.execution_time > 0:
            return self.input_size / self.execution_time
        return None


@dataclass
class ToolProfile:
    """Aggregated performance profile for a tool"""
    tool_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time: float = 0.0
    min_execution_time: float = float('inf')
    max_execution_time: float = 0.0
    avg_memory_used: float = 0.0
    avg_cpu_percent: float = 0.0
    success_rate: float = 0.0
    common_errors: Dict[str, int] = field(default_factory=dict)
    execution_history: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update(self, metrics: PerformanceMetrics):
        """Update profile with new metrics"""
        self.total_executions += 1
        
        if metrics.success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1
            if metrics.error:
                self.common_errors[metrics.error] = self.common_errors.get(metrics.error, 0) + 1
        
        # Update execution time stats
        self.min_execution_time = min(self.min_execution_time, metrics.execution_time)
        self.max_execution_time = max(self.max_execution_time, metrics.execution_time)
        
        # Add to history
        self.execution_history.append(metrics)
        
        # Recalculate averages from history
        if self.execution_history:
            self.avg_execution_time = statistics.mean(
                m.execution_time for m in self.execution_history
            )
            self.avg_memory_used = statistics.mean(
                m.memory_used for m in self.execution_history
            )
            self.avg_cpu_percent = statistics.mean(
                m.cpu_percent for m in self.execution_history
            )
        
        self.success_rate = self.successful_executions / self.total_executions if self.total_executions > 0 else 0


class ToolPerformanceProfiler:
    """Tracks and analyzes tool execution performance"""
    
    def __init__(self, enable_memory_tracking: bool = True):
        self.profiles: Dict[str, ToolProfile] = {}
        self.enable_memory_tracking = enable_memory_tracking
        self.current_executions: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        
        # Performance thresholds for alerts
        self.thresholds = {
            'execution_time': 30.0,  # seconds
            'memory_used': 500.0,    # MB
            'cpu_percent': 80.0,     # percentage
            'success_rate': 0.8      # ratio
        }
        
        # Optimization recommendations
        self.optimization_rules = self._build_optimization_rules()
        
        if self.enable_memory_tracking:
            tracemalloc.start()
    
    def _build_optimization_rules(self) -> List[Dict]:
        """Build rules for performance optimization recommendations"""
        return [
            {
                'name': 'slow_execution',
                'condition': lambda p: p.avg_execution_time > self.thresholds['execution_time'],
                'recommendation': 'Consider implementing caching or optimizing the algorithm'
            },
            {
                'name': 'high_memory',
                'condition': lambda p: p.avg_memory_used > self.thresholds['memory_used'],
                'recommendation': 'Implement streaming or batch processing to reduce memory usage'
            },
            {
                'name': 'low_success_rate',
                'condition': lambda p: p.success_rate < self.thresholds['success_rate'],
                'recommendation': 'Review error patterns and add retry logic or input validation'
            },
            {
                'name': 'high_variance',
                'condition': lambda p: (p.max_execution_time - p.min_execution_time) > p.avg_execution_time,
                'recommendation': 'Performance is inconsistent - investigate external dependencies'
            }
        ]
    
    async def profile_execution(
        self,
        tool_name: str,
        tool_func: Callable,
        parameters: Dict[str, Any]
    ) -> Tuple[Any, PerformanceMetrics]:
        """
        Profile the execution of a tool
        
        Returns:
            Tuple of (result, metrics)
        """
        # Initialize tracking
        execution_id = f"{tool_name}_{time.time()}"
        
        # Measure input size
        input_size = self._estimate_size(parameters)
        
        # Get initial measurements
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        cpu_before = process.cpu_percent(interval=0.1)
        
        if self.enable_memory_tracking:
            tracemalloc.reset_peak()
        
        # Record start
        start_time = time.time()
        
        # Track current execution
        with self._lock:
            self.current_executions[execution_id] = {
                'tool_name': tool_name,
                'start_time': start_time,
                'parameters': parameters
            }
        
        # Execute tool
        success = True
        error = None
        result = None
        
        try:
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**parameters)
            else:
                result = await asyncio.to_thread(tool_func, **parameters)
        except Exception as e:
            success = False
            error = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Tool {tool_name} failed: {error}")
            raise
        finally:
            # Record end
            end_time = time.time()
            
            # Get final measurements
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            cpu_after = process.cpu_percent(interval=0.1)
            
            memory_peak = memory_after
            if self.enable_memory_tracking:
                _, peak = tracemalloc.get_traced_memory()
                memory_peak = peak / 1024 / 1024  # MB
            
            # Estimate output size
            output_size = self._estimate_size(result) if result else 0
            
            # Create metrics
            metrics = PerformanceMetrics(
                tool_name=tool_name,
                start_time=start_time,
                end_time=end_time,
                execution_time=end_time - start_time,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_peak=memory_peak,
                cpu_percent=(cpu_before + cpu_after) / 2,
                success=success,
                error=error,
                input_size=input_size,
                output_size=output_size,
                parameters={k: type(v).__name__ for k, v in parameters.items()}
            )
            
            # Update profile
            self._update_profile(metrics)
            
            # Clean up tracking
            with self._lock:
                del self.current_executions[execution_id]
            
            # Check for performance issues
            self._check_performance_alerts(metrics)
        
        return result, metrics
    
    def _update_profile(self, metrics: PerformanceMetrics):
        """Update tool profile with new metrics"""
        with self._lock:
            if metrics.tool_name not in self.profiles:
                self.profiles[metrics.tool_name] = ToolProfile(tool_name=metrics.tool_name)
            
            self.profiles[metrics.tool_name].update(metrics)
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics):
        """Check for performance issues and log alerts"""
        alerts = []
        
        if metrics.execution_time > self.thresholds['execution_time']:
            alerts.append(f"Slow execution: {metrics.execution_time:.2f}s")
        
        if metrics.memory_used > self.thresholds['memory_used']:
            alerts.append(f"High memory usage: {metrics.memory_used:.2f}MB")
        
        if metrics.cpu_percent > self.thresholds['cpu_percent']:
            alerts.append(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        if alerts:
            logger.warning(f"Performance alerts for {metrics.tool_name}: {', '.join(alerts)}")
    
    def get_profile(self, tool_name: str) -> Optional[ToolProfile]:
        """Get performance profile for a specific tool"""
        return self.profiles.get(tool_name)
    
    def get_all_profiles(self) -> Dict[str, ToolProfile]:
        """Get all tool profiles"""
        return self.profiles.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.profiles:
            return {'message': 'No performance data available'}
        
        summary = {
            'total_tools': len(self.profiles),
            'total_executions': sum(p.total_executions for p in self.profiles.values()),
            'overall_success_rate': self._calculate_overall_success_rate(),
            'slowest_tools': self._get_slowest_tools(5),
            'most_memory_intensive': self._get_memory_intensive_tools(5),
            'most_error_prone': self._get_error_prone_tools(5),
            'recommendations': self._generate_recommendations()
        }
        
        return summary
    
    def get_tool_performance(self, tool_name: str) -> Dict[str, Any]:
        """Get detailed performance data for a specific tool"""
        profile = self.profiles.get(tool_name)
        if not profile:
            return {'error': f'No performance data for tool: {tool_name}'}
        
        # Calculate percentiles from history
        execution_times = [m.execution_time for m in profile.execution_history]
        
        performance_data = {
            'tool_name': tool_name,
            'statistics': {
                'total_executions': profile.total_executions,
                'success_rate': profile.success_rate,
                'avg_execution_time': profile.avg_execution_time,
                'min_execution_time': profile.min_execution_time,
                'max_execution_time': profile.max_execution_time,
                'p50_execution_time': statistics.median(execution_times) if execution_times else 0,
                'p95_execution_time': self._percentile(execution_times, 95) if execution_times else 0,
                'avg_memory_used': profile.avg_memory_used,
                'avg_cpu_percent': profile.avg_cpu_percent
            },
            'common_errors': profile.common_errors,
            'recent_executions': [
                {
                    'timestamp': datetime.fromtimestamp(m.start_time).isoformat(),
                    'execution_time': m.execution_time,
                    'memory_used': m.memory_used,
                    'success': m.success
                }
                for m in list(profile.execution_history)[-10:]
            ],
            'optimization_suggestions': self._get_tool_optimizations(profile)
        }
        
        return performance_data
    
    def _calculate_overall_success_rate(self) -> float:
        """Calculate overall success rate across all tools"""
        total_executions = sum(p.total_executions for p in self.profiles.values())
        total_successes = sum(p.successful_executions for p in self.profiles.values())
        
        return total_successes / total_executions if total_executions > 0 else 0
    
    def _get_slowest_tools(self, limit: int) -> List[Dict[str, Any]]:
        """Get the slowest performing tools"""
        sorted_tools = sorted(
            self.profiles.values(),
            key=lambda p: p.avg_execution_time,
            reverse=True
        )
        
        return [
            {
                'tool_name': p.tool_name,
                'avg_execution_time': p.avg_execution_time,
                'executions': p.total_executions
            }
            for p in sorted_tools[:limit]
        ]
    
    def _get_memory_intensive_tools(self, limit: int) -> List[Dict[str, Any]]:
        """Get the most memory-intensive tools"""
        sorted_tools = sorted(
            self.profiles.values(),
            key=lambda p: p.avg_memory_used,
            reverse=True
        )
        
        return [
            {
                'tool_name': p.tool_name,
                'avg_memory_used': p.avg_memory_used,
                'executions': p.total_executions
            }
            for p in sorted_tools[:limit]
        ]
    
    def _get_error_prone_tools(self, limit: int) -> List[Dict[str, Any]]:
        """Get tools with highest error rates"""
        tools_with_errors = [
            p for p in self.profiles.values() 
            if p.failed_executions > 0
        ]
        
        sorted_tools = sorted(
            tools_with_errors,
            key=lambda p: 1 - p.success_rate,
            reverse=True
        )
        
        return [
            {
                'tool_name': p.tool_name,
                'error_rate': 1 - p.success_rate,
                'failed_executions': p.failed_executions,
                'common_errors': list(p.common_errors.keys())[:3]
            }
            for p in sorted_tools[:limit]
        ]
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate optimization recommendations based on profiles"""
        recommendations = []
        
        for profile in self.profiles.values():
            for rule in self.optimization_rules:
                if rule['condition'](profile):
                    recommendations.append({
                        'tool': profile.tool_name,
                        'issue': rule['name'],
                        'recommendation': rule['recommendation']
                    })
        
        return recommendations
    
    def _get_tool_optimizations(self, profile: ToolProfile) -> List[str]:
        """Get optimization suggestions for a specific tool"""
        suggestions = []
        
        for rule in self.optimization_rules:
            if rule['condition'](profile):
                suggestions.append(rule['recommendation'])
        
        # Additional specific suggestions
        if profile.execution_history:
            recent_times = [m.execution_time for m in list(profile.execution_history)[-10:]]
            if len(recent_times) > 1:
                trend = statistics.mean(recent_times[-5:]) - statistics.mean(recent_times[:5])
                if trend > 0.1 * profile.avg_execution_time:
                    suggestions.append("Performance is degrading over time - check for memory leaks or data accumulation")
        
        return suggestions
    
    def _estimate_size(self, obj: Any) -> int:
        """Estimate the size of an object in bytes"""
        if obj is None:
            return 0
        
        if isinstance(obj, (str, bytes)):
            return len(obj)
        elif isinstance(obj, (list, tuple)):
            return sum(self._estimate_size(item) for item in obj)
        elif isinstance(obj, dict):
            return sum(
                self._estimate_size(k) + self._estimate_size(v) 
                for k, v in obj.items()
            )
        else:
            # Rough estimate for other types
            return len(str(obj))
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a dataset"""
        if not data:
            return 0
        
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def export_metrics(self, filepath: str):
        """Export all metrics to a JSON file"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self.get_performance_summary(),
            'profiles': {
                name: {
                    'tool_name': profile.tool_name,
                    'total_executions': profile.total_executions,
                    'success_rate': profile.success_rate,
                    'avg_execution_time': profile.avg_execution_time,
                    'avg_memory_used': profile.avg_memory_used,
                    'common_errors': profile.common_errors
                }
                for name, profile in self.profiles.items()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Exported performance metrics to {filepath}")
    
    def reset_metrics(self, tool_name: Optional[str] = None):
        """Reset metrics for a specific tool or all tools"""
        with self._lock:
            if tool_name:
                if tool_name in self.profiles:
                    del self.profiles[tool_name]
                    logger.info(f"Reset metrics for tool: {tool_name}")
            else:
                self.profiles.clear()
                logger.info("Reset all performance metrics")


# Usage example:
if __name__ == "__main__":
    import asyncio
    
    async def example_tool(data: str, count: int = 10):
        """Example tool that does some work"""
        await asyncio.sleep(0.1 * count)  # Simulate work
        return f"Processed {len(data)} chars, count={count}"
    
    async def main():
        profiler = ToolPerformanceProfiler()
        
        # Profile multiple executions
        for i in range(5):
            try:
                result, metrics = await profiler.profile_execution(
                    "example_tool",
                    example_tool,
                    {"data": "test data " * i, "count": i + 1}
                )
                print(f"Execution {i + 1}: {metrics.execution_time:.3f}s")
            except Exception as e:
                print(f"Execution {i + 1} failed: {e}")
        
        # Get performance summary
        summary = profiler.get_performance_summary()
        print("\nPerformance Summary:")
        print(json.dumps(summary, indent=2))
        
        # Get tool-specific performance
        tool_perf = profiler.get_tool_performance("example_tool")
        print("\nTool Performance:")
        print(json.dumps(tool_perf, indent=2))
    
    asyncio.run(main())
