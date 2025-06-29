"""
Advanced Rate Limiting
Token bucket, sliding window, and adaptive rate limiting
"""

import asyncio
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from collections import deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Configuration for rate limiters"""
    requests_per_second: float = 10.0
    burst_size: int = 20
    window_size_seconds: float = 60.0
    adaptive: bool = False
    backoff_factor: float = 1.5
    max_backoff_seconds: float = 300.0


class RateLimiter:
    """Base rate limiter interface"""
    
    def __init__(self, config: RateLimitConfig = None):
        self.config = config or RateLimitConfig()
        self.request_times = deque()
        self.total_requests = 0
        self.denied_requests = 0
        
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire permission for requests"""
        raise NotImplementedError
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get rate limiter statistics"""
        return {
            "total_requests": self.total_requests,
            "denied_requests": self.denied_requests,
            "success_rate": (self.total_requests - self.denied_requests) / max(self.total_requests, 1),
            "current_rate": self._calculate_current_rate(),
            "config": self.config.__dict__
        }
    
    def _calculate_current_rate(self) -> float:
        """Calculate current request rate"""
        now = time.time()
        minute_ago = now - 60
        
        # Count requests in last minute
        recent_requests = sum(1 for req_time in self.request_times if req_time > minute_ago)
        return recent_requests / 60.0


class TokenBucketLimiter(RateLimiter):
    """Token bucket rate limiter"""
    
    def __init__(self, config: RateLimitConfig = None):
        super().__init__(config)
        self.tokens = self.config.burst_size
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire tokens from bucket"""
        async with self._lock:
            self.total_requests += 1
            
            # Refill tokens
            now = time.time()
            time_passed = now - self.last_refill
            tokens_to_add = time_passed * self.config.requests_per_second
            
            self.tokens = min(self.config.burst_size, self.tokens + tokens_to_add)
            self.last_refill = now
            
            # Check if we have enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                self.request_times.append(now)
                
                # Cleanup old request times
                minute_ago = now - 60
                while self.request_times and self.request_times[0] < minute_ago:
                    self.request_times.popleft()
                
                return True
            else:
                self.denied_requests += 1
                return False
    
    async def wait_for_tokens(self, tokens: int = 1) -> None:
        """Wait until tokens are available"""
        while not await self.acquire(tokens):
            # Calculate wait time
            wait_time = tokens / self.config.requests_per_second
            await asyncio.sleep(min(wait_time, 1.0))
    
    def get_available_tokens(self) -> float:
        """Get current available tokens"""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.config.requests_per_second
        
        return min(self.config.burst_size, self.tokens + tokens_to_add)


class SlidingWindowLimiter(RateLimiter):
    """Sliding window rate limiter"""
    
    def __init__(self, config: RateLimitConfig = None):
        super().__init__(config)
        self.window_requests = deque()
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire permission using sliding window"""
        async with self._lock:
            self.total_requests += 1
            now = time.time()
            
            # Remove old requests outside window
            window_start = now - self.config.window_size_seconds
            while self.window_requests and self.window_requests[0] < window_start:
                self.window_requests.popleft()
            
            # Check if we can accept this request
            max_requests = self.config.requests_per_second * self.config.window_size_seconds
            
            if len(self.window_requests) < max_requests:
                self.window_requests.append(now)
                self.request_times.append(now)
                
                # Cleanup general request times
                minute_ago = now - 60
                while self.request_times and self.request_times[0] < minute_ago:
                    self.request_times.popleft()
                
                return True
            else:
                self.denied_requests += 1
                return False
    
    async def wait_for_availability(self) -> None:
        """Wait until a slot becomes available"""
        while not await self.acquire():
            # Wait for oldest request to expire
            if self.window_requests:
                oldest_request = self.window_requests[0]
                wait_time = (oldest_request + self.config.window_size_seconds) - time.time()
                if wait_time > 0:
                    await asyncio.sleep(min(wait_time + 0.1, 1.0))
            else:
                await asyncio.sleep(0.1)


class AdaptiveRateLimiter(RateLimiter):
    """Adaptive rate limiter that adjusts based on success/failure rates"""
    
    def __init__(self, config: RateLimitConfig = None):
        super().__init__(config)
        self.current_rate = self.config.requests_per_second
        self.success_history = deque(maxlen=100)
        self.last_adjustment = time.time()
        self.base_limiter = TokenBucketLimiter(self.config)
        self._lock = asyncio.Lock()
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire with adaptive rate adjustment"""
        # Update the base limiter's rate
        self.base_limiter.config.requests_per_second = self.current_rate
        
        result = await self.base_limiter.acquire(tokens)
        
        self.total_requests = self.base_limiter.total_requests
        self.denied_requests = self.base_limiter.denied_requests
        
        return result
    
    def record_success(self, success: bool):
        """Record the success/failure of a request"""
        self.success_history.append(success)
        self._maybe_adjust_rate()
    
    def _maybe_adjust_rate(self):
        """Adjust rate based on recent success history"""
        now = time.time()
        
        # Don't adjust too frequently
        if now - self.last_adjustment < 10.0:
            return
        
        if len(self.success_history) < 10:
            return
        
        # Calculate recent success rate
        recent_successes = sum(self.success_history)
        success_rate = recent_successes / len(self.success_history)
        
        old_rate = self.current_rate
        
        if success_rate > 0.95:
            # High success rate - can increase rate
            self.current_rate = min(
                self.config.requests_per_second * 2,
                self.current_rate * 1.1
            )
        elif success_rate < 0.8:
            # Low success rate - decrease rate
            self.current_rate = max(
                self.config.requests_per_second * 0.1,
                self.current_rate * 0.8
            )
        
        if old_rate != self.current_rate:
            logger.info(f"Adjusted rate from {old_rate:.2f} to {self.current_rate:.2f} rps (success rate: {success_rate:.2f})")
            self.last_adjustment = now
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get enhanced statistics"""
        base_stats = super().get_statistics()
        
        adaptive_stats = {
            "current_rate": self.current_rate,
            "base_rate": self.config.requests_per_second,
            "recent_success_rate": sum(self.success_history) / len(self.success_history) if self.success_history else 0,
            "rate_adjustments": len(self.success_history),
            "available_tokens": self.base_limiter.get_available_tokens()
        }
        
        return {**base_stats, **adaptive_stats}


class DistributedRateLimiter(RateLimiter):
    """Distributed rate limiter using Redis-like backend (simplified)"""
    
    def __init__(self, config: RateLimitConfig = None, instance_id: str = None):
        super().__init__(config)
        self.instance_id = instance_id or f"instance_{time.time()}"
        self.local_limiter = TokenBucketLimiter(config)
        
        # In a real implementation, this would connect to Redis/database
        self.shared_state = {}
    
    async def acquire(self, tokens: int = 1) -> bool:
        """Acquire with distributed coordination"""
        # For this simplified version, we'll just use local limiting
        # In production, this would coordinate with other instances via Redis
        
        result = await self.local_limiter.acquire(tokens)
        
        self.total_requests = self.local_limiter.total_requests
        self.denied_requests = self.local_limiter.denied_requests
        
        return result
    
    def _sync_with_distributed_state(self):
        """Sync with distributed rate limiting state"""
        # This would implement Redis Lua scripts for atomic operations
        pass


# Usage example and testing
if __name__ == "__main__":
    async def test_rate_limiters():
        """Test different rate limiters"""
        
        # Test TokenBucketLimiter
        print("Testing TokenBucketLimiter...")
        config = RateLimitConfig(requests_per_second=5.0, burst_size=10)
        limiter = TokenBucketLimiter(config)
        
        # Try to make 15 requests rapidly
        granted = 0
        denied = 0
        
        for i in range(15):
            if await limiter.acquire():
                granted += 1
            else:
                denied += 1
        
        print(f"Token Bucket: {granted} granted, {denied} denied")
        print(f"Statistics: {limiter.get_statistics()}")
        
        # Test SlidingWindowLimiter
        print("\nTesting SlidingWindowLimiter...")
        window_config = RateLimitConfig(requests_per_second=2.0, window_size_seconds=5.0)
        window_limiter = SlidingWindowLimiter(window_config)
        
        granted = 0
        denied = 0
        
        for i in range(12):
            if await window_limiter.acquire():
                granted += 1
            else:
                denied += 1
            await asyncio.sleep(0.1)
        
        print(f"Sliding Window: {granted} granted, {denied} denied")
        print(f"Statistics: {window_limiter.get_statistics()}")
        
        # Test AdaptiveRateLimiter
        print("\nTesting AdaptiveRateLimiter...")
        adaptive_config = RateLimitConfig(requests_per_second=3.0, adaptive=True)
        adaptive_limiter = AdaptiveRateLimiter(adaptive_config)
        
        # Simulate requests with varying success rates
        for i in range(50):
            if await adaptive_limiter.acquire():
                # Simulate success/failure
                success = i % 3 != 0  # 66% success rate
                adaptive_limiter.record_success(success)
            await asyncio.sleep(0.05)
        
        print(f"Adaptive Statistics: {adaptive_limiter.get_statistics()}")
    
    asyncio.run(test_rate_limiters())
