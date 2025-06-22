#!/usr/bin/env python3
"""
High Volume Executor
Handles massive concurrent scraping operations with intelligent distribution
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
import asyncpg

logger = logging.getLogger("high_volume_executor")

class JobStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
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
    """Manages high-volume concurrent scraping operations"""
    
    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.workers = []
        self.job_queue = "high_volume_jobs"
        self.result_queue = "scraping_results"
        self.max_workers = 50
        self.running = False
        
    async def initialize(self):
        """Initialize high-volume infrastructure"""
        
        # Redis for job queuing and real-time coordination
        redis_url = "redis://localhost:6379"
        self.redis_client = aioredis.from_url(redis_url, max_connections=100)
        
        # PostgreSQL for persistent job storage
        postgres_url = "postgresql://scraper_user:secure_password_123@localhost:5432/high_volume_scraping"
        self.db_pool = await asyncpg.create_pool(
            postgres_url,
            min_size=10,
            max_size=50
        )
        
        # Initialize database schema
        await self._initialize_database()
        
        # Start worker pool
        await self._start_worker_pool()
        
        logger.info(f"High-volume executor initialized with {self.max_workers} workers")
    
    async def _initialize_database(self):
        """Initialize database tables for job management"""
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS high_volume_jobs (
                    job_id VARCHAR PRIMARY KEY,
                    urls_count INTEGER NOT NULL,
                    purpose VARCHAR NOT NULL,
                    priority INTEGER DEFAULT 1,
                    batch_size INTEGER DEFAULT 100,
                    max_workers INTEGER DEFAULT 50,
                    status VARCHAR DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT NOW(),
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    progress JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}'
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS url_results (
                    id SERIAL PRIMARY KEY,
                    job_id VARCHAR NOT NULL,
                    url VARCHAR NOT NULL,
                    success BOOLEAN NOT NULL,
                    extracted_data JSONB,
                    error_message TEXT,
                    processing_time FLOAT,
                    strategy_used VARCHAR,
                    worker_id VARCHAR,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS worker_stats (
                    worker_id VARCHAR PRIMARY KEY,
                    urls_processed INTEGER DEFAULT 0,
                    successful_extractions INTEGER DEFAULT 0,
                    failed_extractions INTEGER DEFAULT 0,
                    current_job_id VARCHAR,
                    last_activity TIMESTAMP DEFAULT NOW(),
                    status VARCHAR DEFAULT 'idle'
                )
            """)
    
    async def _start_worker_pool(self):
        """Start the worker pool for processing jobs"""
        
        for i in range(self.max_workers):
            worker = HighVolumeWorker(f"worker_{i}", self)
            self.workers.append(worker)
            # Start worker as background task
            asyncio.create_task(worker.start_processing())
        
        logger.info(f"Started {len(self.workers)} high-volume workers")
    
    async def submit_job(self, urls: List[str], purpose: str, priority: int = 1,
                        batch_size: int = 100, max_workers: int = 50,
                        credentials: Dict[str, str] = None) -> str:
        """Submit a high-volume scraping job"""
        
        job_id = f"hvol_{int(time.time())}_{str(uuid.uuid4())[:8]}"
        
        job = HighVolumeJob(
            job_id=job_id,
            urls=urls,
            purpose=purpose,
            priority=priority,
            batch_size=batch_size,
            max_workers=min(max_workers, self.max_workers)
        )
        
        # Store job in database
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO high_volume_jobs (job_id, urls_count, purpose, priority, 
                                            batch_size, max_workers, status, progress, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, job.job_id, len(urls), purpose, priority, batch_size, max_workers,
                 job.status.value, json.dumps(job.progress), 
                 json.dumps({"credentials": credentials} if credentials else {}))
        
        # Split URLs into batches and queue them
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
        
        logger.info(f"Submitted high-volume job {job_id}: {len(urls)} URLs in {len(batches)} batches")
        
        return job_id
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get comprehensive job status and progress"""
        
        async with self.db_pool.acquire() as conn:
            # Get job info
            job_row = await conn.fetchrow("""
                SELECT * FROM high_volume_jobs WHERE job_id = $1
            """, job_id)
            
            if not job_row:
                return {"error": "Job not found"}
            
            # Get URL processing stats
            url_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_processed,
                    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successful,
                    SUM(CASE WHEN NOT success THEN 1 ELSE 0 END) as failed,
                    AVG(processing_time) as avg_processing_time,
                    MIN(created_at) as first_processed,
                    MAX(created_at) as last_processed
                FROM url_results 
                WHERE job_id = $1
            """, job_id)
            
            # Calculate progress
            total_urls = job_row["urls_count"]
            processed_urls = url_stats["total_processed"] or 0
            remaining_urls = total_urls - processed_urls
            completion_percentage = (processed_urls / total_urls * 100) if total_urls > 0 else 0
            
            # Estimate completion time
            estimated_completion = None
            if url_stats["avg_processing_time"] and remaining_urls > 0:
                avg_time = float(url_stats["avg_processing_time"])
                # Estimate based on current worker capacity
                active_workers = await self._count_active_workers()
                estimated_seconds = (remaining_urls * avg_time) / max(1, active_workers)
                estimated_completion = time.time() + estimated_seconds
            
            return {
                "job_id": job_id,
                "status": job_row["status"],
                "created_at": job_row["created_at"].isoformat(),
                "started_at": job_row["started_at"].isoformat() if job_row["started_at"] else None,
                "completed_at": job_row["completed_at"].isoformat() if job_row["completed_at"] else None,
                "progress": {
                    "total_urls": total_urls,
                    "processed_urls": processed_urls,
                    "successful_urls": url_stats["successful"] or 0,
                    "failed_urls": url_stats["failed"] or 0,
                    "remaining_urls": remaining_urls,
                    "completion_percentage": round(completion_percentage, 2)
                },
                "performance": {
                    "avg_processing_time": float(url_stats["avg_processing_time"] or 0),
                    "estimated_completion": estimated_completion,
                    "processing_rate": self._calculate_processing_rate(url_stats)
                },
                "metadata": {
                    "purpose": job_row["purpose"],
                    "priority": job_row["priority"],
                    "batch_size": job_row["batch_size"],
                    "max_workers": job_row["max_workers"]
                }
            }
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get real-time system performance statistics"""
        
        # Worker statistics
        worker_stats = []
        total_active = 0
        total_processing_rate = 0
        
        async with self.db_pool.acquire() as conn:
            worker_rows = await conn.fetch("SELECT * FROM worker_stats")
            
            for row in worker_rows:
                stats = {
                    "worker_id": row["worker_id"],
                    "status": row["status"],
                    "urls_processed": row["urls_processed"],
                    "successful_extractions": row["successful_extractions"],
                    "failed_extractions": row["failed_extractions"],
                    "success_rate": (row["successful_extractions"] / max(1, row["urls_processed"])) * 100,
                    "current_job": row["current_job_id"],
                    "last_activity": row["last_activity"].isoformat() if row["last_activity"] else None
                }
                
                worker_stats.append(stats)
                
                if row["status"] == "active":
                    total_active += 1
        
        # Queue statistics
        queue_depth = await self.redis_client.zcard(self.job_queue)
        
        # Recent performance
        async with self.db_pool.acquire() as conn:
            recent_stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as urls_last_hour,
                    AVG(processing_time) as avg_time_last_hour
                FROM url_results 
                WHERE created_at > NOW() - INTERVAL '1 hour'
            """)
        
        return {
            "timestamp": time.time(),
            "workers": {
                "total_workers": len(self.workers),
                "active_workers": total_active,
                "idle_workers": len(self.workers) - total_active,
                "worker_details": worker_stats
            },
            "queue": {
                "pending_batches": queue_depth,
                "estimated_urls": queue_depth * 100  # Approximate
            },
            "performance": {
                "urls_processed_last_hour": recent_stats["urls_last_hour"] or 0,
                "avg_processing_time": float(recent_stats["avg_time_last_hour"] or 0),
                "current_throughput": f"{(recent_stats['urls_last_hour'] or 0) / 60:.1f} URLs/minute"
            },
            "system": {
                "redis_connected": await self._check_redis_health(),
                "database_connected": await self._check_database_health()
            }
        }
    
    async def _count_active_workers(self) -> int:
        """Count currently active workers"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COUNT(*) FROM worker_stats WHERE status = 'active'
            """)
            return result or 0
    
    def _calculate_processing_rate(self, stats) -> str:
        """Calculate processing rate from statistics"""
        if not stats["first_processed"] or not stats["last_processed"]:
            return "0 URLs/minute"
        
        time_diff = (stats["last_processed"] - stats["first_processed"]).total_seconds()
        if time_diff <= 0:
            return "0 URLs/minute"
        
        urls_per_second = (stats["total_processed"] or 0) / time_diff
        urls_per_minute = urls_per_second * 60
        
        return f"{urls_per_minute:.1f} URLs/minute"
    
    async def _check_redis_health(self) -> bool:
        """Check Redis connection health"""
        try:
            await self.redis_client.ping()
            return True
        except:
            return False
    
    async def _check_database_health(self) -> bool:
        """Check database connection health"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except:
            return False

class HighVolumeWorker:
    """Individual worker for processing scraping batches"""
    
    def __init__(self, worker_id: str, executor: HighVolumeExecutor):
        self.worker_id = worker_id
        self.executor = executor
        self.stats = WorkerStats(worker_id=worker_id)
        self.running = False
    
    async def start_processing(self):
        """Main worker loop"""
        self.running = True
        logger.info(f"High-volume worker {self.worker_id} started")
        
        # Initialize worker stats in database
        await self._update_worker_stats("idle")
        
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
                    await self._update_worker_stats("idle")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error: {e}")
                await asyncio.sleep(10)
    
    async def _process_batch(self, batch: Dict[str, Any]):
        """Process a batch of URLs"""
        
        job_id = batch["job_id"]
        batch_id = batch["batch_id"]
        urls = batch["urls"]
        purpose = batch["purpose"]
        credentials = batch.get("credentials")
        
        await self._update_worker_stats("active", job_id)
        
        logger.info(f"Worker {self.worker_id} processing batch {batch_id}: {len(urls)} URLs")
        
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
        
        # Store results in database
        successful = 0
        failed = 0
        
        async with self.executor.db_pool.acquire() as conn:
            for i, result in enumerate(results):
                url = urls[i]
                
                if isinstance(result, Exception):
                    # Handle exception
                    await conn.execute("""
                        INSERT INTO url_results (job_id, url, success, error_message, 
                                               processing_time, worker_id)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, job_id, url, False, str(result), batch_time / len(urls), self.worker_id)
                    failed += 1
                    
                elif result.get("success", False):
                    # Successful extraction
                    await conn.execute("""
                        INSERT INTO url_results (job_id, url, success, extracted_data,
                                               processing_time, strategy_used, worker_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, job_id, url, True, json.dumps(result.get("extracted_data", {})),
                         batch_time / len(urls), result.get("strategy_used"), self.worker_id)
                    successful += 1
                    
                else:
                    # Failed extraction
                    await conn.execute("""
                        INSERT INTO url_results (job_id, url, success, error_message,
                                               processing_time, worker_id)
                        VALUES ($1, $2, $3, $4, $5, $6)
                    """, job_id, url, False, result.get("error", "Unknown error"),
                         batch_time / len(urls), self.worker_id)
                    failed += 1
        
        # Update worker statistics
        self.stats.urls_processed += len(urls)
        self.stats.successful_extractions += successful
        self.stats.failed_extractions += failed
        
        await self._update_worker_stats("idle")
        
        logger.info(f"Worker {self.worker_id} completed batch {batch_id}: {successful} successful, {failed} failed")
    
    async def _scrape_single_url(self, url: str, purpose: str, job_id: str) -> Dict[str, Any]:
        """Scrape a single URL (placeholder implementation)"""
        
        # TODO: Integrate with the intelligent analyzer and strategy selector
        # For now, return a mock result
        
        try:
            # Simulate processing time
            await asyncio.sleep(0.5)
            
            # Mock successful extraction
            return {
                "success": True,
                "url": url,
                "extracted_data": {
                    "title": f"Mock data for {url}",
                    "purpose": purpose
                },
                "strategy_used": "mock_strategy"
            }
            
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }
    
    async def _update_worker_stats(self, status: str, current_job: str = None):
        """Update worker statistics in database"""
        
        self.stats.status = status
        self.stats.current_job_id = current_job
        self.stats.last_activity = time.time()
        
        async with self.executor.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO worker_stats (worker_id, urls_processed, successful_extractions,
                                        failed_extractions, current_job_id, status, last_activity)
                VALUES ($1, $2, $3, $4, $5, $6, NOW())
                ON CONFLICT (worker_id) DO UPDATE SET
                    urls_processed = EXCLUDED.urls_processed,
                    successful_extractions = EXCLUDED.successful_extractions,
                    failed_extractions = EXCLUDED.failed_extractions,
                    current_job_id = EXCLUDED.current_job_id,
                    status = EXCLUDED.status,
                    last_activity = EXCLUDED.last_activity
            """, self.worker_id, self.stats.urls_processed, self.stats.successful_extractions,
                 self.stats.failed_extractions, current_job, status)
