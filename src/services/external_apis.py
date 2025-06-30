#!/usr/bin/env python3
"""
External API Service
Manages integrations with external APIs and services for enhanced functionality
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import aiohttp
import time
from urllib.parse import urlencode

logger = logging.getLogger("external_api_service")

@dataclass
class APIConfig:
    """Configuration for external API service"""
    timeout_seconds: int = 30
    max_retries: int = 3
    rate_limit_delay: float = 1.0
    user_agent: str = "Crawl4AI-ExternalAPI/1.0"
    
    # API Keys (loaded from environment or config)
    webhook_endpoints: Dict[str, str] = None
    elasticsearch_config: Dict[str, str] = None
    supabase_config: Dict[str, str] = None
    slack_config: Dict[str, str] = None

@dataclass
class APIResponse:
    """Structured API response"""
    success: bool
    data: Any
    status_code: Optional[int] = None
    error: Optional[str] = None
    response_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

class ExternalAPIService:
    """
    Production-ready external API service for integrations
    """
    
    def __init__(self, config: APIConfig = None):
        self.config = config or APIConfig()
        self.session = None
        self.request_count = 0
        self.error_count = 0
        self.rate_limiter = {}
        
    async def initialize(self) -> bool:
        """Initialize the external API service"""
        
        try:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout_seconds),
                headers={'User-Agent': self.config.user_agent}
            )
            
            logger.info("External API service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize external API service: {e}")
            return False
    
    async def send_webhook(self, webhook_url: str, data: Dict[str, Any],
                          headers: Dict[str, str] = None) -> APIResponse:
        """
        Send data to a webhook endpoint
        
        Args:
            webhook_url: Target webhook URL
            data: Data to send
            headers: Optional custom headers
            
        Returns:
            APIResponse with result
        """
        
        start_time = time.time()
        self.request_count += 1
        
        try:
            # Rate limiting
            await self._apply_rate_limit("webhook")
            
            request_headers = {"Content-Type": "application/json"}
            if headers:
                request_headers.update(headers)
            
            async with self.session.post(
                webhook_url,
                json=data,
                headers=request_headers
            ) as response:
                response_time = time.time() - start_time
                response_data = await response.text()
                
                if response.status < 400:
                    try:
                        parsed_data = json.loads(response_data)
                    except json.JSONDecodeError:
                        parsed_data = response_data
                    
                    return APIResponse(
                        success=True,
                        data=parsed_data,
                        status_code=response.status,
                        response_time=response_time,
                        metadata={"webhook_url": webhook_url}
                    )
                else:
                    return APIResponse(
                        success=False,
                        data=None,
                        status_code=response.status,
                        error=f"HTTP {response.status}: {response_data}",
                        response_time=response_time
                    )
                    
        except Exception as e:
            self.error_count += 1
            response_time = time.time() - start_time
            logger.error(f"Webhook request failed: {e}")
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time=response_time
            )
    
    async def send_to_elasticsearch(self, index: str, document: Dict[str, Any],
                                   doc_id: str = None) -> APIResponse:
        """
        Send document to Elasticsearch
        
        Args:
            index: Elasticsearch index name
            document: Document to index
            doc_id: Optional document ID
            
        Returns:
            APIResponse with result
        """
        
        if not self.config.elasticsearch_config:
            return APIResponse(
                success=False,
                data=None,
                error="Elasticsearch configuration not provided"
            )
        
        start_time = time.time()
        
        try:
            es_config = self.config.elasticsearch_config
            base_url = es_config.get("url", "http://localhost:9200")
            
            # Build URL
            if doc_id:
                url = f"{base_url}/{index}/_doc/{doc_id}"
            else:
                url = f"{base_url}/{index}/_doc"
            
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            
            # Add authentication if configured
            if "username" in es_config and "password" in es_config:
                import base64
                credentials = base64.b64encode(
                    f"{es_config['username']}:{es_config['password']}".encode()
                ).decode()
                headers["Authorization"] = f"Basic {credentials}"
            
            # Rate limiting
            await self._apply_rate_limit("elasticsearch")
            
            async with self.session.post(url, json=document, headers=headers) as response:
                response_time = time.time() - start_time
                response_data = await response.json()
                
                if response.status < 400:
                    return APIResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status,
                        response_time=response_time,
                        metadata={"index": index, "doc_id": doc_id}
                    )
                else:
                    return APIResponse(
                        success=False,
                        data=response_data,
                        status_code=response.status,
                        error=f"Elasticsearch error: {response_data.get('error', 'Unknown error')}",
                        response_time=response_time
                    )
                    
        except Exception as e:
            self.error_count += 1
            response_time = time.time() - start_time
            logger.error(f"Elasticsearch request failed: {e}")
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time=response_time
            )
    
    async def send_to_supabase(self, table: str, data: Dict[str, Any],
                              operation: str = "insert") -> APIResponse:
        """
        Send data to Supabase
        
        Args:
            table: Supabase table name
            data: Data to send
            operation: Operation type ('insert', 'update', 'upsert')
            
        Returns:
            APIResponse with result
        """
        
        if not self.config.supabase_config:
            return APIResponse(
                success=False,
                data=None,
                error="Supabase configuration not provided"
            )
        
        start_time = time.time()
        
        try:
            supabase_config = self.config.supabase_config
            base_url = supabase_config.get("url")
            api_key = supabase_config.get("api_key")
            
            if not base_url or not api_key:
                raise Exception("Missing Supabase URL or API key")
            
            # Build URL
            url = f"{base_url}/rest/v1/{table}"
            
            # Prepare headers
            headers = {
                "Content-Type": "application/json",
                "apikey": api_key,
                "Authorization": f"Bearer {api_key}",
                "Prefer": "return=representation"
            }
            
            # Handle different operations
            if operation == "upsert":
                headers["Prefer"] = "resolution=merge-duplicates"
            
            # Rate limiting
            await self._apply_rate_limit("supabase")
            
            async with self.session.post(url, json=data, headers=headers) as response:
                response_time = time.time() - start_time
                
                if response.status < 400:
                    response_data = await response.json()
                    return APIResponse(
                        success=True,
                        data=response_data,
                        status_code=response.status,
                        response_time=response_time,
                        metadata={"table": table, "operation": operation}
                    )
                else:
                    error_data = await response.text()
                    return APIResponse(
                        success=False,
                        data=None,
                        status_code=response.status,
                        error=f"Supabase error: {error_data}",
                        response_time=response_time
                    )
                    
        except Exception as e:
            self.error_count += 1
            response_time = time.time() - start_time
            logger.error(f"Supabase request failed: {e}")
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time=response_time
            )
    
    async def send_slack_notification(self, message: str, channel: str = None,
                                    attachments: List[Dict[str, Any]] = None) -> APIResponse:
        """
        Send notification to Slack
        
        Args:
            message: Message text
            channel: Slack channel (optional)
            attachments: Message attachments (optional)
            
        Returns:
            APIResponse with result
        """
        
        if not self.config.slack_config:
            return APIResponse(
                success=False,
                data=None,
                error="Slack configuration not provided"
            )
        
        start_time = time.time()
        
        try:
            slack_config = self.config.slack_config
            webhook_url = slack_config.get("webhook_url")
            
            if not webhook_url:
                raise Exception("Slack webhook URL not configured")
            
            # Prepare payload
            payload = {"text": message}
            
            if channel:
                payload["channel"] = channel
            
            if attachments:
                payload["attachments"] = attachments
            
            # Rate limiting
            await self._apply_rate_limit("slack")
            
            return await self.send_webhook(webhook_url, payload)
            
        except Exception as e:
            self.error_count += 1
            response_time = time.time() - start_time
            logger.error(f"Slack notification failed: {e}")
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time=response_time
            )
    
    async def send_extraction_results(self, results: Dict[str, Any],
                                    destinations: List[str] = None) -> Dict[str, APIResponse]:
        """
        Send extraction results to multiple destinations
        
        Args:
            results: Extraction results to send
            destinations: List of destination types ('webhook', 'elasticsearch', 'supabase')
            
        Returns:
            Dictionary of destination -> APIResponse
        """
        
        destinations = destinations or []
        responses = {}
        
        # Prepare standardized data format
        standardized_data = {
            "timestamp": time.time(),
            "url": results.get("url", "unknown"),
            "extraction_strategy": results.get("strategy", "unknown"),
            "success": results.get("success", False),
            "data": results.get("extracted_data", {}),
            "metadata": {
                "processing_time": results.get("processing_time", 0),
                "confidence": results.get("confidence", 0),
                "record_count": len(results.get("extracted_data", {}))
            }
        }
        
        # Send to each destination
        tasks = []
        
        if "webhook" in destinations and self.config.webhook_endpoints:
            for name, url in self.config.webhook_endpoints.items():
                task = self.send_webhook(url, standardized_data)
                tasks.append(("webhook_" + name, task))
        
        if "elasticsearch" in destinations:
            index_name = f"crawl4ai_results_{time.strftime('%Y_%m')}"
            task = self.send_to_elasticsearch(index_name, standardized_data)
            tasks.append(("elasticsearch", task))
        
        if "supabase" in destinations:
            task = self.send_to_supabase("extraction_results", standardized_data)
            tasks.append(("supabase", task))
        
        # Execute all tasks concurrently
        if tasks:
            task_names, task_coroutines = zip(*tasks)
            results_list = await asyncio.gather(*task_coroutines, return_exceptions=True)
            
            for name, result in zip(task_names, results_list):
                if isinstance(result, Exception):
                    responses[name] = APIResponse(
                        success=False,
                        data=None,
                        error=str(result)
                    )
                else:
                    responses[name] = result
        
        return responses
    
    async def get_api_status(self, service_name: str) -> APIResponse:
        """
        Check the status of an external API service
        
        Args:
            service_name: Name of the service to check
            
        Returns:
            APIResponse with status information
        """
        
        start_time = time.time()
        
        try:
            # Define health check endpoints
            health_endpoints = {
                "elasticsearch": "/_cluster/health",
                "supabase": "/rest/v1/",
            }
            
            if service_name not in health_endpoints:
                return APIResponse(
                    success=False,
                    data=None,
                    error=f"Unknown service: {service_name}"
                )
            
            # Get base URL from config
            base_url = None
            if service_name == "elasticsearch" and self.config.elasticsearch_config:
                base_url = self.config.elasticsearch_config.get("url")
            elif service_name == "supabase" and self.config.supabase_config:
                base_url = self.config.supabase_config.get("url")
            
            if not base_url:
                return APIResponse(
                    success=False,
                    data=None,
                    error=f"No configuration found for {service_name}"
                )
            
            # Make health check request
            url = base_url + health_endpoints[service_name]
            
            async with self.session.get(url) as response:
                response_time = time.time() - start_time
                
                if response.status < 400:
                    try:
                        data = await response.json()
                    except json.JSONDecodeError:
                        data = {"status": "healthy"}
                    
                    return APIResponse(
                        success=True,
                        data=data,
                        status_code=response.status,
                        response_time=response_time,
                        metadata={"service": service_name}
                    )
                else:
                    return APIResponse(
                        success=False,
                        data=None,
                        status_code=response.status,
                        error=f"Service {service_name} returned {response.status}",
                        response_time=response_time
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"API status check failed for {service_name}: {e}")
            
            return APIResponse(
                success=False,
                data=None,
                error=str(e),
                response_time=response_time
            )
    
    async def _apply_rate_limit(self, service: str):
        """Apply rate limiting for a service"""
        
        current_time = time.time()
        last_request_time = self.rate_limiter.get(service, 0)
        
        time_since_last = current_time - last_request_time
        if time_since_last < self.config.rate_limit_delay:
            sleep_time = self.config.rate_limit_delay - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.rate_limiter[service] = time.time()
    
    async def test_all_integrations(self) -> Dict[str, APIResponse]:
        """
        Test all configured integrations
        
        Returns:
            Dictionary of service -> test result
        """
        
        test_results = {}
        
        # Test Elasticsearch
        if self.config.elasticsearch_config:
            test_results["elasticsearch"] = await self.get_api_status("elasticsearch")
        
        # Test Supabase
        if self.config.supabase_config:
            test_results["supabase"] = await self.get_api_status("supabase")
        
        # Test Webhooks
        if self.config.webhook_endpoints:
            for name, url in self.config.webhook_endpoints.items():
                test_data = {"test": True, "timestamp": time.time()}
                test_results[f"webhook_{name}"] = await self.send_webhook(url, test_data)
        
        # Test Slack
        if self.config.slack_config:
            test_message = "Test notification from Crawl4AI External API Service"
            test_results["slack"] = await self.send_slack_notification(test_message)
        
        return test_results
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics"""
        
        success_rate = (self.request_count - self.error_count) / max(self.request_count, 1)
        
        return {
            "requests_processed": self.request_count,
            "errors_encountered": self.error_count,
            "success_rate": success_rate,
            "configured_services": {
                "elasticsearch": bool(self.config.elasticsearch_config),
                "supabase": bool(self.config.supabase_config),
                "webhooks": bool(self.config.webhook_endpoints),
                "slack": bool(self.config.slack_config)
            },
            "rate_limiter_status": self.rate_limiter,
            "service_initialized": self.session is not None
        }
    
    async def cleanup(self):
        """Clean up resources"""
        
        if self.session:
            await self.session.close()
            self.session = None
        
        # Clear rate limiter
        self.rate_limiter.clear()
        
        logger.info("External API service cleanup completed")
    
    async def __aenter__(self):
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()
