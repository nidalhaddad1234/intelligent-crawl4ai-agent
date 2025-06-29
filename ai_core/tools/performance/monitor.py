"""
Crawler Monitoring and Performance Metrics
Real-time monitoring and resource tracking for enterprise crawling
"""

import asyncio
import psutil
import time
import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque
import statistics
import json

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """System performance metrics"""
    timestamp: float
    cpu_percent: float
    memory_used_mb: float
    memory_percent: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    load_average: Optional[float] = None


@dataclass
class CrawlerMetrics:
    """Crawler-specific metrics"""
    timestamp: float
    active_crawlers: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    requests_per_second: float
    bytes_downloaded: int
    pages_processed: int
    errors_per_minute: float


@dataclass
class AlertThreshold:
    """Alert threshold configuration"""
    metric_name: str
    threshold_value: float
    comparison: str = "greater"  # greater, less, equal
    duration_seconds: float = 60.0
    severity: str = "warning"  # info, warning, error, critical


class ResourceTracker:
    """Track system resource usage"""
    
    def __init__(self, collection_interval: float = 1.0, history_size: int = 3600):
        self.collection_interval = collection_interval
        self.history_size = history_size
        self.metrics_history: deque = deque(maxlen=history_size)
        self._running = False
        self._collection_task: Optional[asyncio.Task] = None
        
        # Baseline measurements
        self._baseline_disk_io = psutil.disk_io_counters()
        self._baseline_network = psutil.net_io_counters()
        self._last_measurement_time = time.time()
    
    async def start(self):
        """Start resource collection"""
        self._running = True
        self._collection_task = asyncio.create_task(self._collect_metrics())
        logger.info("Resource tracking started")
    
    async def stop(self):
        """Stop resource collection"""
        self._running = False
        if self._collection_task:
            self._collection_task.cancel()
            try:
                await self._collection_task
            except asyncio.CancelledError:
                pass
        logger.info("Resource tracking stopped")
    
    async def _collect_metrics(self):
        """Collect system metrics periodically"""
        while self._running:
            try:
                metrics = self._get_current_metrics()
                self.metrics_history.append(metrics)
                await asyncio.sleep(self.collection_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")
                await asyncio.sleep(1.0)
    
    def _get_current_metrics(self) -> PerformanceMetrics:
        """Get current system metrics"""
        current_time = time.time()
        
        # CPU and Memory
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        # Disk I/O
        current_disk_io = psutil.disk_io_counters()
        disk_read_mb = 0
        disk_write_mb = 0
        
        if self._baseline_disk_io and current_disk_io:
            disk_read_mb = (current_disk_io.read_bytes - self._baseline_disk_io.read_bytes) / 1024 / 1024
            disk_write_mb = (current_disk_io.write_bytes - self._baseline_disk_io.write_bytes) / 1024 / 1024
        
        # Network I/O
        current_network = psutil.net_io_counters()
        network_sent_mb = 0
        network_recv_mb = 0
        
        if self._baseline_network and current_network:
            network_sent_mb = (current_network.bytes_sent - self._baseline_network.bytes_sent) / 1024 / 1024
            network_recv_mb = (current_network.bytes_recv - self._baseline_network.bytes_recv) / 1024 / 1024
        
        # Network connections
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, OSError):
            connections = 0
        
        # Load average (Unix only)
        load_avg = None
        try:
            load_avg = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
        except (AttributeError, OSError):
            pass
        
        return PerformanceMetrics(
            timestamp=current_time,
            cpu_percent=cpu_percent,
            memory_used_mb=memory.used / 1024 / 1024,
            memory_percent=memory.percent,
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            active_connections=connections,
            load_average=load_avg
        )
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get most recent metrics"""
        return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """Get summary statistics for the specified time period"""
        if not self.metrics_history:
            return {}
        
        cutoff_time = time.time() - (minutes * 60)
        recent_metrics = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        return {
            "time_period_minutes": minutes,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg": statistics.mean(m.cpu_percent for m in recent_metrics),
                "max": max(m.cpu_percent for m in recent_metrics),
                "min": min(m.cpu_percent for m in recent_metrics)
            },
            "memory": {
                "avg_mb": statistics.mean(m.memory_used_mb for m in recent_metrics),
                "max_mb": max(m.memory_used_mb for m in recent_metrics),
                "avg_percent": statistics.mean(m.memory_percent for m in recent_metrics)
            },
            "disk_io": {
                "total_read_mb": sum(m.disk_io_read_mb for m in recent_metrics),
                "total_write_mb": sum(m.disk_io_write_mb for m in recent_metrics)
            },
            "network": {
                "total_sent_mb": sum(m.network_sent_mb for m in recent_metrics),
                "total_recv_mb": sum(m.network_recv_mb for m in recent_metrics)
            },
            "connections": {
                "avg": statistics.mean(m.active_connections for m in recent_metrics),
                "max": max(m.active_connections for m in recent_metrics)
            }
        }


class CrawlerMonitor:
    """Monitor crawler-specific metrics and performance"""
    
    def __init__(self, alert_thresholds: List[AlertThreshold] = None):
        self.crawler_metrics: deque = deque(maxlen=3600)  # 1 hour of data
        self.alert_thresholds = alert_thresholds or self._default_alert_thresholds()
        self.resource_tracker = ResourceTracker()
        
        # Crawler state tracking
        self.active_crawlers = 0
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times: deque = deque(maxlen=1000)
        self.bytes_downloaded = 0
        self.pages_processed = 0
        self.recent_errors: deque = deque(maxlen=100)
        
        # Alert state
        self.active_alerts: Dict[str, Dict] = {}
        self.alert_callbacks: List[Callable] = []
        
        self._monitoring_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _default_alert_thresholds(self) -> List[AlertThreshold]:
        """Default alert thresholds"""
        return [
            AlertThreshold("cpu_percent", 85.0, "greater", 120.0, "warning"),
            AlertThreshold("memory_percent", 90.0, "greater", 60.0, "error"),
            AlertThreshold("error_rate", 0.1, "greater", 300.0, "warning"),
            AlertThreshold("avg_response_time", 10.0, "greater", 180.0, "warning"),
            AlertThreshold("requests_per_second", 1.0, "less", 300.0, "warning")
        ]
    
    async def start(self):
        """Start monitoring"""
        self._running = True
        await self.resource_tracker.start()
        self._monitoring_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Crawler monitoring started")
    
    async def stop(self):
        """Stop monitoring"""
        self._running = False
        await self.resource_tracker.stop()
        
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Crawler monitoring stopped")
    
    def record_crawler_start(self):
        """Record a crawler starting"""
        self.active_crawlers += 1
    
    def record_crawler_stop(self):
        """Record a crawler stopping"""
        self.active_crawlers = max(0, self.active_crawlers - 1)
    
    def record_request(self, success: bool, response_time: float, bytes_downloaded: int = 0):
        """Record a request result"""
        self.total_requests += 1
        
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
            self.recent_errors.append(time.time())
        
        self.response_times.append(response_time)
        self.bytes_downloaded += bytes_downloaded
    
    def record_page_processed(self):
        """Record a page being processed"""
        self.pages_processed += 1
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                # Collect crawler metrics
                metrics = self._collect_crawler_metrics()
                self.crawler_metrics.append(metrics)
                
                # Check alerts
                await self._check_alerts(metrics)
                
                await asyncio.sleep(10.0)  # Check every 10 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(1.0)
    
    def _collect_crawler_metrics(self) -> CrawlerMetrics:
        """Collect current crawler metrics"""
        current_time = time.time()
        
        # Calculate requests per second (last minute)
        minute_ago = current_time - 60
        recent_requests = self.total_requests  # Simplified - would track per minute
        requests_per_second = recent_requests / 60.0
        
        # Calculate average response time
        avg_response_time = statistics.mean(self.response_times) if self.response_times else 0.0
        
        # Calculate errors per minute
        recent_error_times = [t for t in self.recent_errors if t > minute_ago]
        errors_per_minute = len(recent_error_times)
        
        return CrawlerMetrics(
            timestamp=current_time,
            active_crawlers=self.active_crawlers,
            total_requests=self.total_requests,
            successful_requests=self.successful_requests,
            failed_requests=self.failed_requests,
            avg_response_time=avg_response_time,
            requests_per_second=requests_per_second,
            bytes_downloaded=self.bytes_downloaded,
            pages_processed=self.pages_processed,
            errors_per_minute=errors_per_minute
        )
    
    async def _check_alerts(self, crawler_metrics: CrawlerMetrics):
        """Check for alert conditions"""
        current_system_metrics = self.resource_tracker.get_current_metrics()
        
        for threshold in self.alert_thresholds:
            value = self._get_metric_value(threshold.metric_name, crawler_metrics, current_system_metrics)
            
            if value is None:
                continue
            
            alert_condition = self._evaluate_threshold(value, threshold)
            alert_key = f"{threshold.metric_name}_{threshold.severity}"
            
            if alert_condition:
                if alert_key not in self.active_alerts:
                    # New alert
                    self.active_alerts[alert_key] = {
                        "threshold": threshold,
                        "first_triggered": time.time(),
                        "current_value": value
                    }
                else:
                    # Update existing alert
                    self.active_alerts[alert_key]["current_value"] = value
                    
                    # Check if alert duration exceeded
                    duration = time.time() - self.active_alerts[alert_key]["first_triggered"]
                    if duration >= threshold.duration_seconds:
                        await self._trigger_alert(threshold, value, duration)
            else:
                # Alert condition cleared
                if alert_key in self.active_alerts:
                    logger.info(f"Alert cleared: {threshold.metric_name} = {value}")
                    del self.active_alerts[alert_key]
    
    def _get_metric_value(self, metric_name: str, crawler_metrics: CrawlerMetrics, system_metrics: Optional[PerformanceMetrics]) -> Optional[float]:
        """Get value for a specific metric"""
        # Crawler metrics
        if hasattr(crawler_metrics, metric_name):
            return getattr(crawler_metrics, metric_name)
        
        # System metrics
        if system_metrics and hasattr(system_metrics, metric_name):
            return getattr(system_metrics, metric_name)
        
        # Calculated metrics
        if metric_name == "error_rate" and crawler_metrics.total_requests > 0:
            return crawler_metrics.failed_requests / crawler_metrics.total_requests
        
        return None
    
    def _evaluate_threshold(self, value: float, threshold: AlertThreshold) -> bool:
        """Evaluate if a threshold is exceeded"""
        if threshold.comparison == "greater":
            return value > threshold.threshold_value
        elif threshold.comparison == "less":
            return value < threshold.threshold_value
        elif threshold.comparison == "equal":
            return abs(value - threshold.threshold_value) < 0.001
        
        return False
    
    async def _trigger_alert(self, threshold: AlertThreshold, current_value: float, duration: float):
        """Trigger an alert"""
        alert_data = {
            "metric": threshold.metric_name,
            "severity": threshold.severity,
            "threshold": threshold.threshold_value,
            "current_value": current_value,
            "duration_seconds": duration,
            "timestamp": time.time()
        }
        
        logger.warning(f"ALERT [{threshold.severity.upper()}]: {threshold.metric_name} = {current_value} (threshold: {threshold.threshold_value})")
        
        # Call alert callbacks
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert_data)
                else:
                    callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
    
    def add_alert_callback(self, callback: Callable):
        """Add callback for alert notifications"""
        self.alert_callbacks.append(callback)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        current_metrics = self.crawler_metrics[-1] if self.crawler_metrics else None
        system_summary = self.resource_tracker.get_metrics_summary(60)  # Last hour
        
        return {
            "current_time": time.time(),
            "crawler_status": {
                "active_crawlers": self.active_crawlers,
                "total_requests": self.total_requests,
                "success_rate": self.successful_requests / max(self.total_requests, 1),
                "avg_response_time": statistics.mean(self.response_times) if self.response_times else 0,
                "pages_processed": self.pages_processed,
                "bytes_downloaded": self.bytes_downloaded
            },
            "system_performance": system_summary,
            "active_alerts": len(self.active_alerts),
            "alert_details": [
                {
                    "metric": alert["threshold"].metric_name,
                    "severity": alert["threshold"].severity,
                    "value": alert["current_value"],
                    "duration": time.time() - alert["first_triggered"]
                }
                for alert in self.active_alerts.values()
            ],
            "recent_metrics": [
                {
                    "timestamp": m.timestamp,
                    "requests_per_second": m.requests_per_second,
                    "avg_response_time": m.avg_response_time,
                    "active_crawlers": m.active_crawlers
                }
                for m in list(self.crawler_metrics)[-60:]  # Last 10 minutes
            ]
        }
    
    def export_metrics(self, filepath: str, hours: int = 24):
        """Export metrics to JSON file"""
        cutoff_time = time.time() - (hours * 3600)
        
        crawler_data = [
            {
                "timestamp": m.timestamp,
                "active_crawlers": m.active_crawlers,
                "total_requests": m.total_requests,
                "successful_requests": m.successful_requests,
                "failed_requests": m.failed_requests,
                "avg_response_time": m.avg_response_time,
                "requests_per_second": m.requests_per_second,
                "bytes_downloaded": m.bytes_downloaded,
                "pages_processed": m.pages_processed,
                "errors_per_minute": m.errors_per_minute
            }
            for m in self.crawler_metrics if m.timestamp > cutoff_time
        ]
        
        system_data = [
            {
                "timestamp": m.timestamp,
                "cpu_percent": m.cpu_percent,
                "memory_used_mb": m.memory_used_mb,
                "memory_percent": m.memory_percent,
                "disk_io_read_mb": m.disk_io_read_mb,
                "disk_io_write_mb": m.disk_io_write_mb,
                "network_sent_mb": m.network_sent_mb,
                "network_recv_mb": m.network_recv_mb,
                "active_connections": m.active_connections
            }
            for m in self.resource_tracker.metrics_history if m.timestamp > cutoff_time
        ]
        
        export_data = {
            "export_time": time.time(),
            "time_period_hours": hours,
            "crawler_metrics": crawler_data,
            "system_metrics": system_data
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"Metrics exported to {filepath}")
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.stop()


# Usage example
if __name__ == "__main__":
    async def test_monitoring():
        """Test monitoring functionality"""
        
        async def alert_callback(alert_data):
            print(f"ALERT RECEIVED: {alert_data}")
        
        # Create monitor with custom thresholds
        thresholds = [
            AlertThreshold("cpu_percent", 50.0, "greater", 5.0, "warning"),
            AlertThreshold("error_rate", 0.05, "greater", 10.0, "error")
        ]
        
        async with CrawlerMonitor(thresholds) as monitor:
            monitor.add_alert_callback(alert_callback)
            
            # Simulate crawler activity
            monitor.record_crawler_start()
            
            for i in range(100):
                # Simulate requests
                success = i % 10 != 0  # 90% success rate
                response_time = 0.5 + (i % 5) * 0.1  # Varying response times
                
                monitor.record_request(success, response_time, 1024 * (i % 10))
                
                if i % 10 == 0:
                    monitor.record_page_processed()
                
                await asyncio.sleep(0.1)
            
            # Get dashboard data
            dashboard = monitor.get_dashboard_data()
            print("Dashboard Data:")
            print(json.dumps(dashboard, indent=2))
            
            # Export metrics
            monitor.export_metrics("test_metrics.json", 1)
            
            monitor.record_crawler_stop()
    
    asyncio.run(test_monitoring())
