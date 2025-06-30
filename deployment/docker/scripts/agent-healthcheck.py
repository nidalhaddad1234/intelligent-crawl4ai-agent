#!/usr/bin/env python3
"""
Intelligent Crawl4AI Agent - Docker Health Check
Comprehensive health check for the containerized agent
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import psutil


class HealthChecker:
    """Comprehensive health checker for the intelligent agent"""
    
    def __init__(self):
        self.checks = []
        self.start_time = time.time()
        self.timeout = int(os.environ.get('HEALTH_CHECK_TIMEOUT', '10'))
        
        # Configuration
        self.mcp_host = os.environ.get('MCP_SERVER_HOST', '0.0.0.0')
        self.mcp_port = int(os.environ.get('MCP_SERVER_PORT', '8811'))
        self.metrics_port = int(os.environ.get('METRICS_PORT', '8812'))
        self.ollama_url = os.environ.get('OLLAMA_URL', '')
        self.chromadb_url = os.environ.get('CHROMADB_URL', '')
        self.redis_url = os.environ.get('REDIS_URL', '')
        
    async def check_mcp_server(self) -> Dict[str, any]:
        """Check if MCP server is responding"""
        try:
            url = f"http://{self.mcp_host}:{self.mcp_port}/health"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'status': 'healthy',
                            'response_time': time.time() - self.start_time,
                            'server_info': data
                        }
                    else:
                        return {
                            'status': 'unhealthy',
                            'error': f'HTTP {response.status}',
                            'response_time': time.time() - self.start_time
                        }
                        
        except asyncio.TimeoutError:
            return {
                'status': 'unhealthy',
                'error': 'Connection timeout',
                'response_time': time.time() - self.start_time
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': time.time() - self.start_time
            }
    
    async def check_ai_services(self) -> Dict[str, any]:
        """Check connectivity to AI services"""
        services = {}
        
        # Check Ollama
        if self.ollama_url:
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                    async with session.get(f"{self.ollama_url}/api/tags") as response:
                        if response.status == 200:
                            services['ollama'] = {'status': 'healthy', 'url': self.ollama_url}
                        else:
                            services['ollama'] = {'status': 'unhealthy', 'error': f'HTTP {response.status}'}
            except Exception as e:
                services['ollama'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Check ChromaDB
        if self.chromadb_url:
            try:
                headers = {}
                chromadb_token = os.environ.get('CHROMADB_TOKEN')
                if chromadb_token:
                    headers['X-Chroma-Token'] = chromadb_token
                
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=3)) as session:
                    async with session.get(f"{self.chromadb_url}/api/v1/heartbeat", headers=headers) as response:
                        if response.status == 200:
                            services['chromadb'] = {'status': 'healthy', 'url': self.chromadb_url}
                        else:
                            services['chromadb'] = {'status': 'unhealthy', 'error': f'HTTP {response.status}'}
            except Exception as e:
                services['chromadb'] = {'status': 'unhealthy', 'error': str(e)}
        
        # Check Redis
        if self.redis_url:
            try:
                import redis
                from urllib.parse import urlparse
                
                parsed = urlparse(self.redis_url)
                r = redis.Redis(
                    host=parsed.hostname,
                    port=parsed.port or 6379,
                    password=parsed.password,
                    socket_timeout=3,
                    socket_connect_timeout=3
                )
                
                r.ping()
                services['redis'] = {'status': 'healthy', 'url': self.redis_url}
                
            except Exception as e:
                services['redis'] = {'status': 'unhealthy', 'error': str(e)}
        
        return services
    
    def check_system_resources(self) -> Dict[str, any]:
        """Check system resource usage"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_gb = memory.available / (1024**3)
            
            # Disk usage
            disk = psutil.disk_usage('/app')
            disk_percent = disk.percent
            disk_free_gb = disk.free / (1024**3)
            
            # Process count
            process_count = len(psutil.pids())
            
            # Determine overall health
            resource_issues = []
            if cpu_percent > 90:
                resource_issues.append(f"High CPU usage: {cpu_percent}%")
            if memory_percent > 90:
                resource_issues.append(f"High memory usage: {memory_percent}%")
            if disk_percent > 90:
                resource_issues.append(f"High disk usage: {disk_percent}%")
            if memory_available_gb < 0.5:
                resource_issues.append(f"Low available memory: {memory_available_gb:.2f}GB")
            
            status = 'unhealthy' if resource_issues else 'healthy'
            
            return {
                'status': status,
                'cpu_percent': round(cpu_percent, 2),
                'memory_percent': round(memory_percent, 2),
                'memory_available_gb': round(memory_available_gb, 2),
                'disk_percent': round(disk_percent, 2),
                'disk_free_gb': round(disk_free_gb, 2),
                'process_count': process_count,
                'issues': resource_issues
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_file_system(self) -> Dict[str, any]:
        """Check file system health and required directories"""
        try:
            required_dirs = [
                '/app/src',
                '/app/config',
                '/app/data',
                '/app/logs'
            ]
            
            missing_dirs = []
            readable_dirs = []
            writable_dirs = []
            
            for dir_path in required_dirs:
                path = Path(dir_path)
                
                if not path.exists():
                    missing_dirs.append(dir_path)
                    continue
                
                if path.is_readable():
                    readable_dirs.append(dir_path)
                
                if os.access(dir_path, os.W_OK):
                    writable_dirs.append(dir_path)
            
            # Check log files (if any)
            log_files = list(Path('/app/logs').glob('*.log')) if Path('/app/logs').exists() else []
            
            # Check data directory size
            data_size_mb = 0
            if Path('/app/data').exists():
                try:
                    data_size_mb = sum(f.stat().st_size for f in Path('/app/data').rglob('*') if f.is_file()) / (1024**2)
                except:
                    data_size_mb = 0
            
            status = 'unhealthy' if missing_dirs else 'healthy'
            
            return {
                'status': status,
                'required_dirs': len(required_dirs),
                'missing_dirs': missing_dirs,
                'readable_dirs': len(readable_dirs),
                'writable_dirs': len(writable_dirs),
                'log_files': len(log_files),
                'data_size_mb': round(data_size_mb, 2)
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_environment(self) -> Dict[str, any]:
        """Check environment configuration"""
        try:
            critical_env_vars = [
                'MCP_SERVER_HOST',
                'MCP_SERVER_PORT',
                'APP_ENV'
            ]
            
            optional_env_vars = [
                'OLLAMA_URL',
                'CHROMADB_URL',
                'REDIS_URL',
                'POSTGRES_URL',
                'LOG_LEVEL',
                'MAX_WORKERS'
            ]
            
            missing_critical = []
            missing_optional = []
            
            for var in critical_env_vars:
                if not os.environ.get(var):
                    missing_critical.append(var)
            
            for var in optional_env_vars:
                if not os.environ.get(var):
                    missing_optional.append(var)
            
            status = 'unhealthy' if missing_critical else 'healthy'
            
            return {
                'status': status,
                'missing_critical': missing_critical,
                'missing_optional': missing_optional,
                'app_env': os.environ.get('APP_ENV', 'unknown'),
                'log_level': os.environ.get('LOG_LEVEL', 'unknown'),
                'python_version': sys.version.split()[0]
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    async def run_health_check(self) -> Dict[str, any]:
        """Run comprehensive health check"""
        health_report = {
            'timestamp': time.time(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        try:
            # Run all health checks
            checks = [
                ('mcp_server', self.check_mcp_server()),
                ('ai_services', self.check_ai_services()),
                ('system_resources', self.check_system_resources()),
                ('file_system', self.check_file_system()),
                ('environment', self.check_environment())
            ]
            
            # Execute async checks
            for check_name, check_coro in checks:
                if asyncio.iscoroutine(check_coro):
                    health_report['checks'][check_name] = await check_coro
                else:
                    health_report['checks'][check_name] = check_coro
            
            # Determine overall status
            unhealthy_checks = [
                name for name, result in health_report['checks'].items()
                if result.get('status') == 'unhealthy'
            ]
            
            if unhealthy_checks:
                health_report['overall_status'] = 'unhealthy'
                health_report['unhealthy_checks'] = unhealthy_checks
            
            health_report['execution_time'] = time.time() - self.start_time
            
        except Exception as e:
            health_report['overall_status'] = 'unhealthy'
            health_report['error'] = str(e)
            health_report['execution_time'] = time.time() - self.start_time
        
        return health_report


async def main():
    """Main health check execution"""
    try:
        checker = HealthChecker()
        health_report = await checker.run_health_check()
        
        # Output format based on environment
        output_format = os.environ.get('HEALTH_CHECK_FORMAT', 'exit_code')
        
        if output_format == 'json':
            print(json.dumps(health_report, indent=2))
        elif output_format == 'simple':
            print(f"Status: {health_report['overall_status']}")
            if health_report['overall_status'] == 'unhealthy':
                unhealthy = health_report.get('unhealthy_checks', [])
                print(f"Issues: {', '.join(unhealthy)}")
        
        # Exit with appropriate code
        if health_report['overall_status'] == 'healthy':
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"Health check failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    # Run the health check
    asyncio.run(main())
