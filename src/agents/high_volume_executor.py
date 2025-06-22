#!/usr/bin/env python3
"""
High Volume Executor with SQL Database Integration
Handles massive concurrent scraping operations with intelligent distribution and SQL storage
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import aioredis

# Import database components
from ..database.sql_manager import DatabaseFactory
from ..models.extraction_models import ExtractionJob, ExtractedData, StrategyResult, create_extraction_job, create_extracted_data
from ..database.data_normalizer import DataNormalizer, normalize_extraction_result
from ..database.query_builder import QueryBuilder

# Import other agents for integration
from .intelligent_analyzer import IntelligentWebsiteAnalyzer
from .strategy_selector import StrategySelector
from ..utils.ollama_client import OllamaClient
from ..utils.chromadb_manager import ChromaDBManager

logger = logging.getLogger("high_volume_executor")

class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class HighVolumeJob:
    job_id: str
    urls: List[str]
    purpose: str
    priority: int = 1
    batch_size: int = 100
    max_workers: int = 50
    max_retries: int = 3
    status: JobStatus = JobStatus.PENDING
    created_at: float = None
    started_at: float = None
    completed_at: float = None
    progress: Dict[str, int] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.progress is None:
            self.progress = {
                "total": len(self.urls),
                "completed": 0,
                "failed": 0,
                "in_progress": 0
            }

@dataclass
class WorkerStats:
    worker_id: str
    urls_processed: int = 0
    successful_extractions: int = 0
    failed_extractions: int = 0
    current_job_id: str = None
    last_activity: float = None
    status: str = "idle"

class HighVolumeExecutor:
    """Manages high-volume concurrent scraping operations with SQL storage"""
    
    def __init__(self, database_type: str = "postgresql"):
        self.redis_client = None
        self.db_manager = None
        self.workers = []
        self.job_queue = "high_volume_jobs"
        self.result_queue = "scraping_results"
        self.max_workers = 50
        self.running = False
        self.database_type = database_type
        
        # Data processing components
        self.data_normalizer = DataNormalizer()
        self.query_builder = QueryBuilder(database_type)
        
        # AI Components for intelligent scraping
        self.ollama_client = None
        self.chromadb_manager = None
        self.website_analyzer = None
        self.strategy_selector = None
        
    async def initialize(self):
        """Initialize high-volume infrastructure with SQL database"""
        
        # Initialize database connection
        self.db_manager = DatabaseFactory.from_env()
        await self.db_manager.connect()
        
        # Create tables if they don't exist
        from ..models.extraction_models import Base
        await self.db_manager.create_tables(Base)
        
        logger.info(f"Database initialized: {type(self.db_manager).__name__}")
        
        # Redis for job queuing and real-time coordination
        redis_url = "redis://localhost:6379"
        self.redis_client = aioredis.from_url(redis_url, max_connections=100)
        
        # Initialize AI components
        self.ollama_client = OllamaClient()
        await self.ollama_client.initialize()
        
        self.chromadb_manager = ChromaDBManager(ollama_client=self.ollama_client)
        await self.chromadb_manager.initialize()
        
        self.website_analyzer = IntelligentWebsiteAnalyzer(self.ollama_client)
        self.strategy_selector = StrategySelector(self.ollama_client, self.chromadb_manager)
        
        # Start worker pool
        await self._start_worker_pool()
        
        logger.info(f"High-volume executor initialized with {self.max_workers} workers and AI components")
    
    async def _start_worker_pool(self):
        """Start the worker pool for processing jobs"""
        
        for i in range(self.max_workers):
            worker = HighVolumeWorker(f"worker_{i}", self)
            self.workers.append(worker)
            # Start worker as background task
            asyncio.create_task(worker.start_processing())
        
        logger.info(f"Started {len(self.workers)} high-volume workers")
    
    async def submit_job(self, urls: List[str], purpose: str, 
                        name: str = None, description: str = None,
                        priority: int = 1, batch_size: int = 100, 
                        max_workers: int = 50, credentials: Dict[str, str] = None) -> str:
        """Submit a high-volume scraping job with SQL storage"""
        
        # Create extraction job using SQLAlchemy model
        job = create_extraction_job(
            name=name or f"High-volume job {int(time.time())}",
            purpose=purpose,
            target_urls=urls,
            description=description or f"Scraping {len(urls)} URLs for {purpose}",
            primary_strategy="intelligent_hybrid",  # Will be determined per URL
            extraction_config={
                "batch_size": batch_size,
                "max_workers": min(max_workers, self.max_workers),
                "priority": priority,
                "credentials": credentials
            }
        )
        
        # Store job in database using SQL manager
        async with self.db_manager.session() as session:
            session.add(job)
            await session.flush()  # Get the job_id
            
            job_id = job.job_id
            logger.info(f"Created extraction job {job_id} in database")
        
        # Split URLs into batches and queue them in Redis
        batches = [urls[i:i + batch_size] for i in range(0, len(urls), batch_size)]
        
        for batch_idx, batch_urls in enumerate(batches):
            batch_data = {
                "job_id": job_id,
                "batch_id": f"{job_id}_batch_{batch_idx}",
                "urls": batch_urls,
                "purpose": purpose,
                "priority": priority,
                "credentials": credentials
            }
            
            # Add to Redis queue with priority
            await self.redis_client.zadd(
                self.job_queue,
                {json.dumps(batch_data): priority}
            )
        
        # Update job status to pending
        await self._update_job_status(job_id, JobStatus.PENDING.value)
        
        logger.info(f"Submitted high-volume job {job_id}: {len(urls)} URLs in {len(batches)} batches")
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get comprehensive job status using SQL queries"""
        
        try:
            # Use query builder for complex job status query
            query, params = self.query_builder.build_job_status_query(job_id=job_id)
            results = await self.db_manager.execute_query(query, params)
            
            if not results:
                return {"error": "Job not found"}
            
            job_data = results[0]
            
            # Get detailed URL processing stats using analytics query
            analytics_query, analytics_params = self.query_builder.build_analytics_query(
                table="extracted_data",
                metrics=["count", "success_rate", "avg_confidence", "avg_execution_time"],
                filters={"job_id": job_id}
            )
            
            analytics_results = await self.db_manager.execute_query(analytics_query, analytics_params)
            analytics = analytics_results[0] if analytics_results else {}
            
            # Calculate progress and estimates
            total_urls = len(job_data.get('target_urls', []))
            processed_urls = analytics.get('record_count', 0)
            remaining_urls = total_urls - processed_urls
            completion_percentage = (processed_urls / total_urls * 100) if total_urls > 0 else 0
            
            # Estimate completion time
            estimated_completion = None
            if analytics.get('avg_execution_time') and remaining_urls > 0:
                avg_time = float(analytics['avg_execution_time'])
                active_workers = await self._count_active_workers()
                estimated_seconds = (remaining_urls * avg_time) / max(1, active_workers)
                estimated_completion = time.time() + estimated_seconds
            
            return {
                "job_id": job_id,
                "name": job_data.get('name'),
                "description": job_data.get('description'),
                "status": job_data.get('status'),
                "purpose": job_data.get('purpose'),
                "created_at": job_data.get('created_at'),
                "started_at": job_data.get('started_at'),
                "completed_at": job_data.get('completed_at'),
                "progress": {
                    "total_urls": total_urls,
                    "processed_urls": processed_urls,
                    "successful_urls": int(processed_urls * analytics.get('success_rate', 0)) if analytics.get('success_rate') else 0,
                    "failed_urls": processed_urls - int(processed_urls * analytics.get('success_rate', 0)) if analytics.get('success_rate') else 0,
                    "remaining_urls": remaining_urls,
                    "completion_percentage": round(completion_percentage, 2)
                },
                "performance": {
                    "avg_processing_time": analytics.get('avg_execution_time', 0),
                    "avg_confidence": analytics.get('avg_confidence', 0),
                    "success_rate": analytics.get('success_rate', 0),
                    "estimated_completion": estimated_completion,
                    "processing_rate": self._calculate_processing_rate(job_data)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get job status for {job_id}: {e}")
            return {"error": str(e)}
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get real-time system performance statistics using SQL"""
        
        try:
            # Get recent performance metrics
            recent_query = """
            SELECT 
                COUNT(*) as urls_last_hour,
                AVG(extraction_time) as avg_time_last_hour,
                AVG(confidence_score) as avg_confidence_last_hour,
                SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_last_hour
            FROM extracted_data 
            WHERE extracted_at > datetime('now', '-1 hour')
            """ if self.database_type == "sqlite" else """
            SELECT 
                COUNT(*) as urls_last_hour,
                AVG(extraction_time) as avg_time_last_hour,
                AVG(confidence_score) as avg_confidence_last_hour,
                SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_last_hour
            FROM extracted_data 
            WHERE extracted_at > NOW() - INTERVAL '1 hour'
            """
            
            recent_stats = await self.db_manager.execute_query(recent_query)
            recent_data = recent_stats[0] if recent_stats else {}
            
            # Get active jobs count
            active_jobs_query = """
            SELECT COUNT(*) as active_jobs 
            FROM extraction_jobs 
            WHERE status IN ('pending', 'running')
            """
            
            active_jobs_result = await self.db_manager.execute_query(active_jobs_query)
            active_jobs = active_jobs_result[0]['active_jobs'] if active_jobs_result else 0
            
            # Queue statistics
            queue_depth = await self.redis_client.zcard(self.job_queue)
            
            # Worker statistics (simplified for now)
            total_active = await self._count_active_workers()
            
            urls_last_hour = recent_data.get('urls_last_hour', 0)
            throughput = f"{urls_last_hour / 60:.1f} URLs/minute" if urls_last_hour else "0 URLs/minute"
            
            return {
                "timestamp": time.time(),
                "workers": {
                    "total_workers": len(self.workers),
                    "active_workers": total_active,
                    "idle_workers": len(self.workers) - total_active
                },
                "jobs": {
                    "active_jobs": active_jobs,
                    "pending_batches": queue_depth
                },
                "performance": {
                    "urls_processed_last_hour": urls_last_hour,
                    "successful_last_hour": recent_data.get('successful_last_hour', 0),
                    "avg_processing_time": float(recent_data.get('avg_time_last_hour', 0)),
                    "avg_confidence": float(recent_data.get('avg_confidence_last_hour', 0)),
                    "current_throughput": throughput
                },
                "system": {
                    "database_type": type(self.db_manager).__name__,
                    "database_connected": self.db_manager.is_connected,
                    "redis_connected": await self._check_redis_health()
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}
    
    async def get_recent_extractions(self, limit: int = 100, purpose: str = None) -> List[Dict[str, Any]]:
        """Get recent extractions with optional filtering"""
        
        try:
            filters = {}
            if purpose:
                filters['purpose'] = purpose
            
            query, params = self.query_builder.build_search_query(
                table="extracted_data",
                filters=filters,
                limit=limit,
                order_by="extracted_at",
                order_desc=True
            )
            
            results = await self.db_manager.execute_query(query, params)
            return results
            
        except Exception as e:
            logger.error(f"Failed to get recent extractions: {e}")
            return []
    
    async def export_job_data(self, job_id: str, format: str = "json") -> Dict[str, Any]:
        """Export job data in specified format"""
        
        try:
            query, params = self.query_builder.build_data_export_query(
                table="extracted_data",
                filters={"job_id": job_id}
            )
            
            results = await self.db_manager.execute_query(query, params)
            
            if format.lower() == "json":
                return {
                    "job_id": job_id,
                    "total_records": len(results),
                    "exported_at": time.time(),
                    "data": results
                }
            else:
                # Could add CSV, Excel export here
                return {"error": f"Format {format} not supported yet"}
                
        except Exception as e:
            logger.error(f"Failed to export job data: {e}")
            return {"error": str(e)}
    
    async def _update_job_status(self, job_id: str, status: str, 
                               started_at: float = None, completed_at: float = None):
        """Update job status in database"""
        
        try:
            update_data = {"status": status}
            
            if started_at:
                update_data["started_at"] = started_at
            if completed_at:
                update_data["completed_at"] = completed_at
            
            query = """
            UPDATE extraction_jobs 
            SET status = :status
            """ + (", started_at = :started_at" if started_at else "") + \
                  (", completed_at = :completed_at" if completed_at else "") + \
            " WHERE job_id = :job_id"
            
            update_data["job_id"] = job_id
            await self.db_manager.execute_query(query, update_data)
            
        except Exception as e:
            logger.error(f"Failed to update job status: {e}")
    
    async def _count_active_workers(self) -> int:
        """Count currently active workers"""
        # For now, return approximate based on queue depth
        queue_depth = await self.redis_client.zcard(self.job_queue)
        return min(queue_depth, self.max_workers)
    
    def _calculate_processing_rate(self, job_data: Dict[str, Any]) -> str:
        """Calculate processing rate from job data"""
        if not job_data.get("started_at"):
            return "0 URLs/minute"
        
        # Basic calculation - would be enhanced with actual timing data
        return "~100 URLs/minute"  # Placeholder
    
    async def _check_redis_health(self) -> bool:
        """Check Redis connection health"""
        try:
            await self.redis_client.ping()
            return True
        except:
            return False

class HighVolumeWorker:
    """Individual worker for processing scraping batches with SQL storage"""
    
    def __init__(self, worker_id: str, executor: HighVolumeExecutor):
        self.worker_id = worker_id
        self.executor = executor
        self.stats = WorkerStats(worker_id=worker_id)
        self.running = False
    
    async def start_processing(self):
        """Main worker loop"""
        self.running = True
        logger.info(f"High-volume worker {self.worker_id} started")
        
        while self.running:
            try:
                # Get next batch from priority queue
                batch_data = await self.executor.redis_client.zpopmax(
                    self.executor.job_queue, 1
                )
                
                if batch_data:
                    batch_json, priority = batch_data[0]
                    batch = json.loads(batch_json)
                    
                    await self._process_batch(batch)
                else:
                    # No jobs available, brief pause
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                await asyncio.sleep(10)
    
    async def _process_batch(self, batch: Dict[str, Any]):
        """Process a batch of URLs with SQL storage"""
        
        job_id = batch["job_id"]
        batch_id = batch["batch_id"]
        urls = batch["urls"]
        purpose = batch["purpose"]
        credentials = batch.get("credentials")
        
        logger.info(f"Worker {self.worker_id} processing batch {batch_id}: {len(urls)} URLs")
        
        # Update job status to running if it's the first batch
        await self.executor._update_job_status(job_id, JobStatus.RUNNING.value, started_at=time.time())
        
        # Process URLs concurrently within the batch
        semaphore = asyncio.Semaphore(10)  # Limit concurrent URLs per worker
        
        async def process_single_url(url: str):
            async with semaphore:
                return await self._scrape_single_url(url, purpose, job_id)
        
        start_time = time.time()
        results = await asyncio.gather(
            *[process_single_url(url) for url in urls],
            return_exceptions=True
        )
        batch_time = time.time() - start_time
        
        # Store results in database using SQLAlchemy models
        successful = 0
        failed = 0
        
        extracted_records = []
        
        for i, result in enumerate(results):
            url = urls[i]
            
            if isinstance(result, Exception):
                # Handle exception
                extracted_record = create_extracted_data(
                    job_id=job_id,
                    url=url,
                    purpose=purpose,
                    strategy_used="error",
                    raw_data={},
                    success=False,
                    error_message=str(result),
                    extraction_time=batch_time / len(urls)
                )
                failed += 1
                
            elif result.get("success", False):
                # Successful extraction - normalize the data
                normalized_result = normalize_extraction_result(result, purpose, url)
                
                extracted_record = create_extracted_data(
                    job_id=job_id,
                    url=url,
                    purpose=purpose,
                    strategy_used=result.get("strategy_used", "unknown"),
                    raw_data=result.get("extracted_data", {}),
                    normalized_data=normalized_result.get("normalized_data", {}),
                    success=True,
                    confidence_score=result.get("confidence_score", 0.5),
                    data_quality_score=normalized_result.get("data_quality_score", 0.5),
                    extraction_time=result.get("processing_time", batch_time / len(urls)),
                    website_type=result.get("analysis_summary", {}).get("website_type"),
                    field_count=normalized_result.get("field_count", 0)
                )
                successful += 1
                
            else:
                # Failed extraction
                extracted_record = create_extracted_data(
                    job_id=job_id,
                    url=url,
                    purpose=purpose,
                    strategy_used=result.get("strategy_used", "unknown"),
                    raw_data=result.get("extracted_data", {}),
                    success=False,
                    error_message=result.get("error", "Unknown error"),
                    extraction_time=result.get("processing_time", batch_time / len(urls))
                )
                failed += 1
            
            extracted_records.append(extracted_record)
        
        # Bulk insert all records
        try:
            async with self.executor.db_manager.session() as session:
                session.add_all(extracted_records)
                
            logger.info(f"Stored {len(extracted_records)} extraction results in database")
            
        except Exception as e:
            logger.error(f"Failed to store extraction results: {e}")
        
        # Update worker statistics
        self.stats.urls_processed += len(urls)
        self.stats.successful_extractions += successful
        self.stats.failed_extractions += failed
        
        logger.info(f"Worker {self.worker_id} completed batch {batch_id}: {successful} successful, {failed} failed")
    
    async def _scrape_single_url(self, url: str, purpose: str, job_id: str) -> Dict[str, Any]:
        """Scrape a single URL using intelligent analysis and strategy selection"""
        
        start_time = time.time()
        
        try:
            # Step 1: Analyze website structure and content
            analysis = await self.executor.website_analyzer.analyze_website(url)
            
            # Step 2: Select optimal extraction strategy
            strategy = await self.executor.strategy_selector.select_strategy(
                analysis=analysis,
                purpose=purpose,
                additional_context=f"High-volume job {job_id}"
            )
            
            # Step 3: Execute extraction with selected strategy
            result = await self.executor.website_analyzer.execute_extraction(
                url=url,
                strategy=strategy
            )
            
            # Step 4: Learn from the result for future improvements
            await self.executor.strategy_selector.learn_from_extraction(
                url=url,
                strategy=strategy,
                result=result,
                analysis=analysis,
                purpose=purpose
            )
            
            # Add timing and analysis information
            processing_time = time.time() - start_time
            result["processing_time"] = processing_time
            result["analysis_summary"] = {
                "website_type": analysis.website_type.value,
                "complexity": analysis.estimated_complexity,
                "strategy_used": strategy.primary_strategy,
                "confidence": strategy.estimated_success_rate
            }
            
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Intelligent scraping failed for {url}: {e}")
            
            return {
                "success": False,
                "url": url,
                "error": str(e),
                "processing_time": processing_time,
                "job_id": job_id
            }

# Convenience functions for high-volume operations
async def submit_company_scraping_job(urls: List[str], executor: HighVolumeExecutor) -> str:
    """Submit a job for company information scraping"""
    
    return await executor.submit_job(
        urls=urls,
        purpose="company_info",
        name="Company Information Extraction",
        description=f"Extract company details from {len(urls)} business websites",
        batch_size=50,  # Smaller batches for company info
        max_workers=30
    )

async def submit_product_scraping_job(urls: List[str], executor: HighVolumeExecutor) -> str:
    """Submit a job for product data scraping"""
    
    return await executor.submit_job(
        urls=urls,
        purpose="product_data",
        name="Product Data Extraction",
        description=f"Extract product information from {len(urls)} e-commerce pages",
        batch_size=100,  # Larger batches for product data
        max_workers=50
    )

async def submit_contact_discovery_job(urls: List[str], executor: HighVolumeExecutor) -> str:
    """Submit a job for contact information discovery"""
    
    return await executor.submit_job(
        urls=urls,
        purpose="contact_discovery",
        name="Contact Information Discovery",
        description=f"Discover contact details from {len(urls)} websites",
        batch_size=75,
        max_workers=40
    )

if __name__ == "__main__":
    # Example usage
    async def test_high_volume_executor():
        executor = HighVolumeExecutor(database_type="sqlite")
        await executor.initialize()
        
        # Test with a small batch
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json"
        ]
        
        job_id = await executor.submit_job(
            urls=test_urls,
            purpose="company_info",
            name="Test Job",
            description="Testing high-volume executor with SQL"
        )
        
        print(f"Submitted job: {job_id}")
        
        # Wait a bit and check status
        await asyncio.sleep(5)
        status = await executor.get_job_status(job_id)
        print(f"Job status: {status}")
        
        # Get system stats
        stats = await executor.get_system_stats()
        print(f"System stats: {stats}")
    
    # Run test
    asyncio.run(test_high_volume_executor())
