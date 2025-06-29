"""
Proxy Management and Rotation
Enterprise proxy rotation strategies for scale and reliability
"""

import asyncio
import random
import time
import logging
from typing import Dict, Any, List, Optional, Iterator
from dataclasses import dataclass
from abc import ABC, abstractmethod
from collections import deque
import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class ProxyConfig:
    """Configuration for a single proxy"""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    protocol: str = "http"  # http, https, socks4, socks5
    max_concurrent: int = 5
    timeout: float = 30.0
    
    @property
    def url(self) -> str:
        """Get proxy URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def auth_dict(self) -> Optional[Dict[str, str]]:
        """Get authentication dictionary for aiohttp"""
        if self.username and self.password:
            return {"proxy_auth": aiohttp.BasicAuth(self.username, self.password)}
        return None


@dataclass  
class ProxyStats:
    """Statistics for proxy usage"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    last_used: float = 0.0
    consecutive_failures: int = 0
    is_healthy: bool = True
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        return 1.0 - self.success_rate


class ProxyRotationStrategy(ABC):
    """Base class for proxy rotation strategies"""
    
    @abstractmethod
    def select_proxy(self, proxies: List[ProxyConfig], stats: Dict[str, ProxyStats]) -> Optional[ProxyConfig]:
        """Select next proxy to use"""
        pass
    
    @abstractmethod
    def record_result(self, proxy: ProxyConfig, success: bool, response_time: float):
        """Record the result of using a proxy"""
        pass


class RoundRobinProxyStrategy(ProxyRotationStrategy):
    """Round-robin proxy selection"""
    
    def __init__(self):
        self.current_index = 0
        
    def select_proxy(self, proxies: List[ProxyConfig], stats: Dict[str, ProxyStats]) -> Optional[ProxyConfig]:
        """Select next proxy in round-robin fashion"""
        if not proxies:
            return None
        
        # Filter healthy proxies
        healthy_proxies = [
            proxy for proxy in proxies 
            if stats.get(proxy.url, ProxyStats()).is_healthy
        ]
        
        if not healthy_proxies:
            # All proxies unhealthy, use original list
            healthy_proxies = proxies
        
        if self.current_index >= len(healthy_proxies):
            self.current_index = 0
        
        selected = healthy_proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(healthy_proxies)
        
        return selected
    
    def record_result(self, proxy: ProxyConfig, success: bool, response_time: float):
        """Record result (round-robin doesn't need this)"""
        pass


class WeightedProxyStrategy(ProxyRotationStrategy):
    """Weighted proxy selection based on performance"""
    
    def __init__(self, health_threshold: float = 0.8):
        self.health_threshold = health_threshold
        
    def select_proxy(self, proxies: List[ProxyConfig], stats: Dict[str, ProxyStats]) -> Optional[ProxyConfig]:
        """Select proxy based on performance weights"""
        if not proxies:
            return None
        
        # Calculate weights based on success rate and response time
        proxy_weights = []
        
        for proxy in proxies:
            proxy_stats = stats.get(proxy.url, ProxyStats())
            
            # Skip unhealthy proxies unless all are unhealthy
            if not proxy_stats.is_healthy:
                continue
            
            # Weight based on success rate and response time
            success_weight = proxy_stats.success_rate
            speed_weight = 1.0 / max(proxy_stats.avg_response_time, 0.1)  # Faster is better
            
            total_weight = (success_weight * 0.7) + (speed_weight * 0.3)
            proxy_weights.append((proxy, total_weight))
        
        if not proxy_weights:
            # All proxies unhealthy, fallback to round-robin
            return random.choice(proxies)
        
        # Weighted random selection
        total_weight = sum(weight for _, weight in proxy_weights)
        if total_weight == 0:
            return random.choice(proxies)
        
        random_value = random.uniform(0, total_weight)
        cumulative_weight = 0
        
        for proxy, weight in proxy_weights:
            cumulative_weight += weight
            if random_value <= cumulative_weight:
                return proxy
        
        # Fallback
        return proxy_weights[0][0]
    
    def record_result(self, proxy: ProxyConfig, success: bool, response_time: float):
        """Record result for future weight calculation"""
        # This implementation doesn't need to store state
        # In a more complex version, you might maintain internal statistics
        pass


class FailoverProxyStrategy(ProxyRotationStrategy):
    """Failover strategy with primary/backup proxies"""
    
    def __init__(self, max_failures: int = 3, cooldown_seconds: float = 300.0):
        self.max_failures = max_failures
        self.cooldown_seconds = cooldown_seconds
        self.primary_index = 0
        
    def select_proxy(self, proxies: List[ProxyConfig], stats: Dict[str, ProxyStats]) -> Optional[ProxyConfig]:
        """Select primary proxy or failover to backup"""
        if not proxies:
            return None
        
        # Try primary proxy first
        for i in range(len(proxies)):
            proxy_index = (self.primary_index + i) % len(proxies)
            proxy = proxies[proxy_index]
            proxy_stats = stats.get(proxy.url, ProxyStats())
            
            # Check if proxy is healthy
            if self._is_proxy_available(proxy_stats):
                if i > 0:  # We failed over
                    logger.info(f"Failed over to proxy {proxy.url}")
                return proxy
        
        # All proxies failed, return least recently failed
        return min(proxies, key=lambda p: stats.get(p.url, ProxyStats()).last_used)
    
    def _is_proxy_available(self, proxy_stats: ProxyStats) -> bool:
        """Check if proxy is available for use"""
        # Check if proxy is healthy
        if proxy_stats.is_healthy:
            return True
        
        # Check if cooldown period has passed
        time_since_failure = time.time() - proxy_stats.last_used
        return time_since_failure > self.cooldown_seconds
    
    def record_result(self, proxy: ProxyConfig, success: bool, response_time: float):
        """Record result and update primary if needed"""
        if success:
            # Reset primary to this proxy if it's performing well
            pass  # Implementation would update primary_index


class ProxyManager:
    """Comprehensive proxy management with health monitoring"""
    
    def __init__(self, 
                 proxies: List[ProxyConfig],
                 strategy: ProxyRotationStrategy = None,
                 health_check_interval: float = 60.0,
                 max_failures: int = 5):
        self.proxies = proxies
        self.strategy = strategy or RoundRobinProxyStrategy()
        self.health_check_interval = health_check_interval
        self.max_failures = max_failures
        
        # Statistics tracking
        self.proxy_stats: Dict[str, ProxyStats] = {}
        for proxy in proxies:
            self.proxy_stats[proxy.url] = ProxyStats()
        
        # Health monitoring
        self._health_check_task: Optional[asyncio.Task] = None
        self._running = False
        
    async def start(self):
        """Start proxy manager and health monitoring"""
        self._running = True
        self._health_check_task = asyncio.create_task(self._health_monitor())
        logger.info(f"ProxyManager started with {len(self.proxies)} proxies")
    
    async def stop(self):
        """Stop proxy manager"""
        self._running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("ProxyManager stopped")
    
    def get_proxy(self) -> Optional[ProxyConfig]:
        """Get next proxy from rotation strategy"""
        return self.strategy.select_proxy(self.proxies, self.proxy_stats)
    
    def record_usage(self, proxy: ProxyConfig, success: bool, response_time: float):
        """Record proxy usage result"""
        if proxy.url not in self.proxy_stats:
            self.proxy_stats[proxy.url] = ProxyStats()
        
        stats = self.proxy_stats[proxy.url]
        stats.total_requests += 1
        stats.last_used = time.time()
        
        if success:
            stats.successful_requests += 1
            stats.consecutive_failures = 0
            
            # Update average response time
            if stats.avg_response_time == 0:
                stats.avg_response_time = response_time
            else:
                stats.avg_response_time = (stats.avg_response_time * 0.8) + (response_time * 0.2)
        else:
            stats.failed_requests += 1
            stats.consecutive_failures += 1
            
            # Mark as unhealthy if too many consecutive failures
            if stats.consecutive_failures >= self.max_failures:
                stats.is_healthy = False
                logger.warning(f"Proxy {proxy.url} marked as unhealthy after {stats.consecutive_failures} failures")
        
        # Record with strategy
        self.strategy.record_result(proxy, success, response_time)
    
    async def _health_monitor(self):
        """Monitor proxy health periodically"""
        while self._running:
            try:
                await self._check_proxy_health()
                await asyncio.sleep(self.health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(5.0)
    
    async def _check_proxy_health(self):
        """Check health of all proxies"""
        health_tasks = []
        
        for proxy in self.proxies:
            health_tasks.append(self._check_single_proxy_health(proxy))
        
        await asyncio.gather(*health_tasks, return_exceptions=True)
    
    async def _check_single_proxy_health(self, proxy: ProxyConfig):
        """Check health of a single proxy"""
        try:
            start_time = time.time()
            
            # Use a simple HTTP request to check connectivity
            timeout = aiohttp.ClientTimeout(total=proxy.timeout)
            proxy_url = proxy.url
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    "http://httpbin.org/ip",  # Simple health check endpoint
                    proxy=proxy_url
                ) as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        self.record_usage(proxy, True, response_time)
                        
                        # Mark as healthy if it was unhealthy
                        if not self.proxy_stats[proxy.url].is_healthy:
                            self.proxy_stats[proxy.url].is_healthy = True
                            logger.info(f"Proxy {proxy.url} recovered and marked healthy")
                    else:
                        self.record_usage(proxy, False, response_time)
        
        except Exception as e:
            logger.debug(f"Health check failed for {proxy.url}: {e}")
            self.record_usage(proxy, False, 0.0)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive proxy statistics"""
        total_requests = sum(stats.total_requests for stats in self.proxy_stats.values())
        healthy_proxies = sum(1 for stats in self.proxy_stats.values() if stats.is_healthy)
        
        proxy_details = {}
        for proxy in self.proxies:
            stats = self.proxy_stats[proxy.url]
            proxy_details[proxy.url] = {
                "healthy": stats.is_healthy,
                "success_rate": stats.success_rate,
                "avg_response_time": stats.avg_response_time,
                "total_requests": stats.total_requests,
                "consecutive_failures": stats.consecutive_failures
            }
        
        return {
            "total_proxies": len(self.proxies),
            "healthy_proxies": healthy_proxies,
            "total_requests": total_requests,
            "strategy": self.strategy.__class__.__name__,
            "proxy_details": proxy_details
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()


# Usage example
if __name__ == "__main__":
    async def test_proxy_manager():
        """Test proxy manager functionality"""
        
        # Create test proxies (these are example proxies - replace with real ones)
        proxies = [
            ProxyConfig(host="proxy1.example.com", port=8080),
            ProxyConfig(host="proxy2.example.com", port=8080),
            ProxyConfig(host="proxy3.example.com", port=8080, username="user", password="pass"),
        ]
        
        # Test with different strategies
        strategies = [
            RoundRobinProxyStrategy(),
            WeightedProxyStrategy(),
            FailoverProxyStrategy()
        ]
        
        for strategy in strategies:
            print(f"\nTesting {strategy.__class__.__name__}...")
            
            async with ProxyManager(proxies, strategy, health_check_interval=10.0) as manager:
                # Simulate usage
                for i in range(10):
                    proxy = manager.get_proxy()
                    if proxy:
                        # Simulate request result
                        success = random.random() > 0.2  # 80% success rate
                        response_time = random.uniform(0.1, 2.0)
                        
                        manager.record_usage(proxy, success, response_time)
                        print(f"Used proxy {proxy.host}:{proxy.port} - {'Success' if success else 'Failed'}")
                
                # Get statistics
                stats = manager.get_statistics()
                print(f"Statistics: {stats}")
    
    # Run test
    asyncio.run(test_proxy_manager())
