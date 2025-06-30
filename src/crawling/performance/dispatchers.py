"""
Advanced Dispatchers for Enterprise-Scale Processing
Memory-adaptive and intelligent request dispatching
"""

import asyncio
import psutil
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable, Awaitable
from dataclasses import dataclass
from collections import deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class DispatcherConfig:
    """Configuration for dispatchers"""
    max_concurrent: int = 10
    memory_threshold_mb: int = 1000
    cpu_threshold_percent: float = 80.0
    adaptive_scaling: bool = True
    min_concurrent: int = 1
    max_adaptive_concurrent: int = 50
    monitoring_interval: float = 1.0


class BaseDispatcher(ABC):
    """Base class for request dispatchers"""
    
    def __init__(self, config: DispatcherConfig = None):
        self.config = config or DispatcherConfig()
        self.active_tasks = 0
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.start_time = time.time()
        
    @abstractmethod
    async def dispatch(self, tasks: List[Callable[[], Awaitable]], **kwargs) -> List[Any]:
        """Dispatch tasks for execution"""
        pass
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get dispatcher statistics"""
        runtime = time.time() - self.start_time
        
        return {
            "active_tasks": self.active_tasks,
            "completed_tasks": self.completed_tasks,
            "failed_tasks": self.failed_tasks,
            "total_tasks": self.completed_tasks + self.failed_tasks,
            "success_rate": self.completed_tasks / max(self.completed_tasks + self.failed_tasks, 1),
            "runtime_seconds": runtime,
            "tasks_per_second": (self.completed_tasks + self.failed_tasks) / max(runtime, 1)
        }


class SemaphoreDispatcher(BaseDispatcher):
    """Simple semaphore-based dispatcher"""
    
    def __init__(self, config: DispatcherConfig = None):
        super().__init__(config)
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent)
    
    async def dispatch(self, tasks: List[Callable[[], Awaitable]], **kwargs) -> List[Any]:
        """Dispatch tasks using semaphore limiting"""
        async def execute_with_semaphore(task_func):
            async with self.semaphore:
                self.active_tasks += 1
                try:
                    result = await task_func()
                    self.completed_tasks += 1
                    return result
                except Exception as e:
                    self.failed_tasks += 1
                    logger.error(f"Task failed: {e}")
                    raise
                finally:
                    self.active_tasks -= 1
        
        # Execute all tasks
        results = await asyncio.gather(
            *[execute_with_semaphore(task) for task in tasks],
            return_exceptions=True
        )
        
        return results


class MemoryAdaptiveDispatcher(BaseDispatcher):
    """Memory-adaptive dispatcher that scales concurrency based on resource usage"""
    
    def __init__(self, config: DispatcherConfig = None):
        super().__init__(config)
        self.current_concurrent = self.config.max_concurrent
        self.memory_history = deque(maxlen=10)
        self.cpu_history = deque(maxlen=10)
        self.adjustment_history = deque(maxlen=20)
        self.last_adjustment = time.time()
        
    async def dispatch(self, tasks: List[Callable[[], Awaitable]], **kwargs) -> List[Any]:
        """Dispatch tasks with adaptive concurrency"""
        if not tasks:
            return []
        
        # Start monitoring task
        monitor_task = asyncio.create_task(self._monitor_resources())
        
        try:
            # Process tasks in batches
            results = []
            task_queue = deque(tasks)
            
            while task_queue:
                # Determine current batch size
                batch_size = min(len(task_queue), self.current_concurrent)
                current_batch = [task_queue.popleft() for _ in range(batch_size)]
                
                # Execute batch
                batch_results = await self._execute_batch(current_batch)
                results.extend(batch_results)
                
                # Brief pause to allow monitoring
                if task_queue:
                    await asyncio.sleep(0.1)
            
            return results
            
        finally:
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _execute_batch(self, tasks: List[Callable[[], Awaitable]]) -> List[Any]:
        """Execute a batch of tasks"""
        semaphore = asyncio.Semaphore(len(tasks))
        
        async def execute_with_tracking(task_func):
            async with semaphore:
                self.active_tasks += 1
                try:
                    result = await task_func()
                    self.completed_tasks += 1
                    return result
                except Exception as e:
                    self.failed_tasks += 1
                    logger.error(f"Task failed: {e}")
                    return e
                finally:
                    self.active_tasks -= 1
        
        results = await asyncio.gather(
            *[execute_with_tracking(task) for task in tasks],
            return_exceptions=True
        )
        
        return results
    
    async def _monitor_resources(self):
        """Monitor system resources and adjust concurrency"""
        while True:
            try:
                # Get current resource usage
                memory_usage = psutil.virtual_memory().used / 1024 / 1024  # MB
                cpu_percent = psutil.cpu_percent(interval=0.1)
                
                self.memory_history.append(memory_usage)
                self.cpu_history.append(cpu_percent)
                
                # Adjust concurrency if needed
                await self._adjust_concurrency(memory_usage, cpu_percent)
                
                await asyncio.sleep(self.config.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(1.0)
    
    async def _adjust_concurrency(self, memory_usage: float, cpu_percent: float):
        """Adjust concurrency based on resource usage"""
        current_time = time.time()
        
        # Don't adjust too frequently
        if current_time - self.last_adjustment < 2.0:
            return
        
        old_concurrent = self.current_concurrent
        
        # Check if we should reduce concurrency
        should_reduce = (
            memory_usage > self.config.memory_threshold_mb or
            cpu_percent > self.config.cpu_threshold_percent
        )
        
        # Check if we can increase concurrency
        avg_memory = statistics.mean(self.memory_history) if self.memory_history else 0
        avg_cpu = statistics.mean(self.cpu_history) if self.cpu_history else 0
        
        can_increase = (
            avg_memory < self.config.memory_threshold_mb * 0.7 and
            avg_cpu < self.config.cpu_threshold_percent * 0.7 and
            self.current_concurrent < self.config.max_adaptive_concurrent
        )
        
        if should_reduce:
            # Reduce concurrency
            self.current_concurrent = max(
                self.config.min_concurrent,
                int(self.current_concurrent * 0.8)
            )
            logger.info(f"Reduced concurrency to {self.current_concurrent} due to resource pressure")
            
        elif can_increase and len(self.adjustment_history) > 5:
            # Increase concurrency if recent adjustments were successful
            recent_adjustments = list(self.adjustment_history)[-5:]
            if all(adj >= 0 for adj in recent_adjustments):  # No recent reductions
                self.current_concurrent = min(
                    self.config.max_adaptive_concurrent,
                    int(self.current_concurrent * 1.2)
                )
                logger.info(f"Increased concurrency to {self.current_concurrent}")
        
        # Track adjustment
        if old_concurrent != self.current_concurrent:
            adjustment = self.current_concurrent - old_concurrent
            self.adjustment_history.append(adjustment)
            self.last_adjustment = current_time
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics for adaptive dispatcher"""
        base_stats = super().get_statistics()
        
        adaptive_stats = {
            "current_concurrency": self.current_concurrent,
            "max_concurrency": self.config.max_adaptive_concurrent,
            "avg_memory_mb": statistics.mean(self.memory_history) if self.memory_history else 0,
            "avg_cpu_percent": statistics.mean(self.cpu_history) if self.cpu_history else 0,
            "recent_adjustments": list(self.adjustment_history)[-5:],
            "total_adjustments": len(self.adjustment_history)
        }
        
        return {**base_stats, **adaptive_stats}


class PriorityDispatcher(BaseDispatcher):
    """Priority-based dispatcher for task prioritization"""
    
    def __init__(self, config: DispatcherConfig = None):
        super().__init__(config)
        self.priority_queues = {
            "high": deque(),
            "medium": deque(), 
            "low": deque()
        }
    
    async def dispatch(self, tasks: List[Callable[[], Awaitable]], priorities: List[str] = None, **kwargs) -> List[Any]:
        """Dispatch tasks based on priority"""
        if not tasks:
            return []
        
        if not priorities:
            priorities = ["medium"] * len(tasks)
        
        # Sort tasks by priority
        prioritized_tasks = []
        for task, priority in zip(tasks, priorities):
            prioritized_tasks.append((task, priority))
        
        # Sort by priority (high > medium > low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        prioritized_tasks.sort(key=lambda x: priority_order.get(x[1], 1))
        
        # Execute in priority order with concurrency control
        semaphore = asyncio.Semaphore(self.config.max_concurrent)
        
        async def execute_with_priority(task_func, priority):
            async with semaphore:
                self.active_tasks += 1
                try:
                    result = await task_func()
                    self.completed_tasks += 1
                    return result
                except Exception as e:
                    self.failed_tasks += 1
                    logger.error(f"Priority {priority} task failed: {e}")
                    return e
                finally:
                    self.active_tasks -= 1
        
        results = await asyncio.gather(
            *[execute_with_priority(task, priority) for task, priority in prioritized_tasks],
            return_exceptions=True
        )
        
        return results


# Usage example
if __name__ == "__main__":
    async def sample_task(task_id: int, duration: float = 0.1):
        """Sample task for testing"""
        await asyncio.sleep(duration)
        return f"Task {task_id} completed"
    
    async def test_dispatchers():
        """Test different dispatchers"""
        
        # Create test tasks
        tasks = [lambda tid=i: sample_task(tid, 0.1) for i in range(20)]
        
        # Test SemaphoreDispatcher
        print("Testing SemaphoreDispatcher...")
        config = DispatcherConfig(max_concurrent=5)
        dispatcher = SemaphoreDispatcher(config)
        
        start_time = time.time()
        results = await dispatcher.dispatch(tasks)
        end_time = time.time()
        
        print(f"SemaphoreDispatcher: {len(results)} tasks in {end_time - start_time:.2f}s")
        print(f"Statistics: {dispatcher.get_statistics()}")
        
        # Test MemoryAdaptiveDispatcher
        print("\nTesting MemoryAdaptiveDispatcher...")
        adaptive_dispatcher = MemoryAdaptiveDispatcher(config)
        
        start_time = time.time()
        results = await adaptive_dispatcher.dispatch(tasks)
        end_time = time.time()
        
        print(f"MemoryAdaptiveDispatcher: {len(results)} tasks in {end_time - start_time:.2f}s")
        print(f"Statistics: {adaptive_dispatcher.get_statistics()}")
    
    # Run tests
    asyncio.run(test_dispatchers())
