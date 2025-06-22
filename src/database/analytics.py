#!/usr/bin/env python3
"""
Analytics Engine
Built-in analytics and reporting for intelligent web scraping
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import json

logger = logging.getLogger("analytics")

class AnalyticsEngine:
    """Provides built-in analytics and reporting for scraping operations"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
    
    async def get_success_rates_by_strategy(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get success rates for each extraction strategy"""
        
        date_threshold = datetime.now() - timedelta(days=days_back)
        
        query = """
        SELECT 
            strategy_used,
            COUNT(*) as total_attempts,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_attempts,
            ROUND(AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate,
            ROUND(AVG(confidence_score), 3) as avg_confidence,
            ROUND(AVG(extraction_time), 3) as avg_execution_time
        FROM extracted_data 
        WHERE extracted_at >= :date_threshold
        GROUP BY strategy_used
        ORDER BY success_rate DESC
        """
        
        results = await self.db_manager.execute_query(query, {"date_threshold": date_threshold})
        return results
    
    async def get_performance_by_website_type(self, days_back: int = 30) -> List[Dict[str, Any]]:
        """Get performance metrics by website type"""
        
        date_threshold = datetime.now() - timedelta(days=days_back)
        
        query = """
        SELECT 
            website_type,
            COUNT(*) as total_extractions,
            ROUND(AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate,
            ROUND(AVG(confidence_score), 3) as avg_confidence,
            ROUND(AVG(data_quality_score), 3) as avg_data_quality,
            ROUND(AVG(field_count), 1) as avg_fields_extracted,
            COUNT(DISTINCT domain) as unique_domains
        FROM extracted_data 
        WHERE extracted_at >= :date_threshold AND website_type IS NOT NULL
        GROUP BY website_type
        ORDER BY total_extractions DESC
        """
        
        results = await self.db_manager.execute_query(query, {"date_threshold": date_threshold})
        return results
    
    async def get_extraction_performance_metrics(self, job_id: str = None) -> Dict[str, Any]:
        """Get comprehensive performance metrics"""
        
        filters = {}
        where_clause = ""
        
        if job_id:
            filters["job_id"] = job_id
            where_clause = "WHERE job_id = :job_id"
        
        query = f"""
        SELECT 
            COUNT(*) as total_extractions,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_extractions,
            SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failed_extractions,
            ROUND(AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) * 100, 2) as overall_success_rate,
            ROUND(AVG(confidence_score), 3) as avg_confidence,
            ROUND(AVG(data_quality_score), 3) as avg_data_quality,
            ROUND(AVG(extraction_time), 3) as avg_extraction_time,
            ROUND(AVG(field_count), 1) as avg_fields_per_extraction,
            COUNT(DISTINCT domain) as unique_domains,
            COUNT(DISTINCT purpose) as unique_purposes,
            MIN(extracted_at) as first_extraction,
            MAX(extracted_at) as last_extraction
        FROM extracted_data
        {where_clause}
        """
        
        results = await self.db_manager.execute_query(query, filters)
        return results[0] if results else {}
    
    async def get_data_quality_report(self, purpose: str = None) -> Dict[str, Any]:
        """Generate comprehensive data quality report"""
        
        filters = {}
        where_clause = ""
        
        if purpose:
            filters["purpose"] = purpose
            where_clause = "WHERE purpose = :purpose"
        
        # Overall quality metrics
        quality_query = f"""
        SELECT 
            ROUND(AVG(data_quality_score), 3) as avg_quality_score,
            ROUND(AVG(confidence_score), 3) as avg_confidence_score,
            COUNT(CASE WHEN data_quality_score > 0.8 THEN 1 END) as high_quality_extractions,
            COUNT(CASE WHEN data_quality_score BETWEEN 0.5 AND 0.8 THEN 1 END) as medium_quality_extractions,
            COUNT(CASE WHEN data_quality_score < 0.5 THEN 1 END) as low_quality_extractions,
            COUNT(*) as total_extractions
        FROM extracted_data
        {where_clause} AND success = true
        """
        
        quality_results = await self.db_manager.execute_query(quality_query, filters)
        quality_data = quality_results[0] if quality_results else {}
        
        # Field completeness analysis
        completeness_query = f"""
        SELECT 
            ROUND(AVG(field_count), 1) as avg_field_count,
            MIN(field_count) as min_field_count,
            MAX(field_count) as max_field_count,
            COUNT(CASE WHEN field_count >= 5 THEN 1 END) as rich_extractions,
            COUNT(CASE WHEN field_count < 3 THEN 1 END) as sparse_extractions
        FROM extracted_data
        {where_clause} AND success = true
        """
        
        completeness_results = await self.db_manager.execute_query(completeness_query, filters)
        completeness_data = completeness_results[0] if completeness_results else {}
        
        # Error analysis
        error_query = f"""
        SELECT 
            COUNT(*) as total_errors,
            COUNT(DISTINCT error_message) as unique_error_types
        FROM extracted_data
        {where_clause} AND success = false
        """
        
        error_results = await self.db_manager.execute_query(error_query, filters)
        error_data = error_results[0] if error_results else {}
        
        return {
            "quality_metrics": quality_data,
            "field_completeness": completeness_data,
            "error_analysis": error_data,
            "analysis_date": datetime.now().isoformat(),
            "scope": "all" if not purpose else f"purpose: {purpose}"
        }
    
    async def get_job_performance_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get performance summary for recent jobs"""
        
        query = """
        SELECT 
            ej.job_id,
            ej.name,
            ej.purpose,
            ej.status,
            ej.total_urls,
            ej.successful_extractions,
            ej.failed_extractions,
            ej.created_at,
            ej.completed_at,
            ej.total_execution_time,
            COUNT(ed.id) as actual_extractions,
            ROUND(AVG(ed.confidence_score), 3) as avg_confidence,
            ROUND(AVG(ed.data_quality_score), 3) as avg_data_quality
        FROM extraction_jobs ej
        LEFT JOIN extracted_data ed ON ej.job_id = ed.job_id
        GROUP BY ej.job_id, ej.name, ej.purpose, ej.status, ej.total_urls, 
                 ej.successful_extractions, ej.failed_extractions, ej.created_at, 
                 ej.completed_at, ej.total_execution_time
        ORDER BY ej.created_at DESC
        LIMIT :limit
        """
        
        results = await self.db_manager.execute_query(query, {"limit": limit})
        
        # Calculate additional metrics
        for job in results:
            if job['total_urls'] and job['actual_extractions']:
                job['completion_rate'] = round((job['actual_extractions'] / job['total_urls']) * 100, 2)
            else:
                job['completion_rate'] = 0
            
            if job['actual_extractions']:
                job['success_rate'] = round((job['successful_extractions'] / job['actual_extractions']) * 100, 2)
            else:
                job['success_rate'] = 0
        
        return results
    
    async def get_trending_domains(self, days_back: int = 7, limit: int = 20) -> List[Dict[str, Any]]:
        """Get trending domains by extraction volume"""
        
        date_threshold = datetime.now() - timedelta(days=days_back)
        
        query = """
        SELECT 
            domain,
            COUNT(*) as extraction_count,
            ROUND(AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate,
            ROUND(AVG(confidence_score), 3) as avg_confidence,
            COUNT(DISTINCT purpose) as purposes_used,
            MIN(extracted_at) as first_seen,
            MAX(extracted_at) as last_seen
        FROM extracted_data 
        WHERE extracted_at >= :date_threshold
        GROUP BY domain
        ORDER BY extraction_count DESC
        LIMIT :limit
        """
        
        results = await self.db_manager.execute_query(query, {
            "date_threshold": date_threshold,
            "limit": limit
        })
        
        return results
    
    async def get_strategy_effectiveness(self, website_type: str = None) -> List[Dict[str, Any]]:
        """Analyze strategy effectiveness for different website types"""
        
        filters = {}
        where_clause = ""
        
        if website_type:
            filters["website_type"] = website_type
            where_clause = "WHERE website_type = :website_type"
        
        query = f"""
        SELECT 
            strategy_used,
            website_type,
            COUNT(*) as usage_count,
            ROUND(AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate,
            ROUND(AVG(confidence_score), 3) as avg_confidence,
            ROUND(AVG(extraction_time), 3) as avg_execution_time,
            ROUND(AVG(field_count), 1) as avg_fields_extracted
        FROM extracted_data 
        {where_clause}
        GROUP BY strategy_used, website_type
        ORDER BY success_rate DESC, usage_count DESC
        """
        
        results = await self.db_manager.execute_query(query, filters)
        return results
    
    async def get_hourly_extraction_pattern(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Get extraction patterns by hour of day"""
        
        date_threshold = datetime.now() - timedelta(days=days_back)
        
        # Query depends on database type
        if isinstance(self.db_manager, type(self.db_manager)) and "SQLite" in type(self.db_manager).__name__:
            query = """
            SELECT 
                CAST(strftime('%H', extracted_at) AS INTEGER) as hour_of_day,
                COUNT(*) as extraction_count,
                ROUND(AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate,
                ROUND(AVG(extraction_time), 3) as avg_execution_time
            FROM extracted_data 
            WHERE extracted_at >= :date_threshold
            GROUP BY hour_of_day
            ORDER BY hour_of_day
            """
        else:  # PostgreSQL
            query = """
            SELECT 
                EXTRACT(HOUR FROM extracted_at) as hour_of_day,
                COUNT(*) as extraction_count,
                ROUND(AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) * 100, 2) as success_rate,
                ROUND(AVG(extraction_time), 3) as avg_execution_time
            FROM extracted_data 
            WHERE extracted_at >= :date_threshold
            GROUP BY hour_of_day
            ORDER BY hour_of_day
            """
        
        results = await self.db_manager.execute_query(query, {"date_threshold": date_threshold})
        return results
    
    async def generate_executive_summary(self, period_days: int = 30) -> Dict[str, Any]:
        """Generate executive summary for leadership dashboards"""
        
        date_threshold = datetime.now() - timedelta(days=period_days)
        
        # Get high-level metrics
        performance = await self.get_extraction_performance_metrics()
        job_summary = await self.get_job_performance_summary(limit=50)
        quality_report = await self.get_data_quality_report()
        
        # Calculate trends
        completed_jobs = len([job for job in job_summary if job['status'] == 'completed'])
        total_jobs = len(job_summary)
        
        # Calculate ROI metrics
        total_urls_processed = performance.get('total_extractions', 0)
        successful_extractions = performance.get('successful_extractions', 0)
        
        summary = {
            "period": f"Last {period_days} days",
            "generated_at": datetime.now().isoformat(),
            "key_metrics": {
                "total_urls_processed": total_urls_processed,
                "successful_extractions": successful_extractions,
                "overall_success_rate": performance.get('overall_success_rate', 0),
                "unique_domains_processed": performance.get('unique_domains', 0),
                "jobs_completed": completed_jobs,
                "job_completion_rate": round((completed_jobs / total_jobs * 100), 2) if total_jobs else 0
            },
            "quality_metrics": {
                "avg_data_quality": quality_report.get('quality_metrics', {}).get('avg_quality_score', 0),
                "avg_confidence": performance.get('avg_confidence', 0),
                "high_quality_extractions": quality_report.get('quality_metrics', {}).get('high_quality_extractions', 0),
                "avg_fields_per_extraction": performance.get('avg_fields_per_extraction', 0)
            },
            "performance_metrics": {
                "avg_extraction_time": performance.get('avg_extraction_time', 0),
                "processing_efficiency": round(successful_extractions / max(1, total_urls_processed) * 100, 2),
                "data_richness": quality_report.get('field_completeness', {}).get('avg_field_count', 0)
            },
            "recommendations": await self._generate_recommendations(performance, quality_report)
        }
        
        return summary
    
    async def _generate_recommendations(self, performance: Dict[str, Any], 
                                      quality_report: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        
        recommendations = []
        
        # Success rate recommendations
        success_rate = performance.get('overall_success_rate', 0)
        if success_rate < 70:
            recommendations.append("Consider improving extraction strategies - current success rate is below 70%")
        elif success_rate > 90:
            recommendations.append("Excellent success rate! Consider expanding to more challenging domains")
        
        # Data quality recommendations
        avg_quality = quality_report.get('quality_metrics', {}).get('avg_quality_score', 0)
        if avg_quality < 0.6:
            recommendations.append("Focus on data quality improvements - implement better normalization")
        
        # Performance recommendations
        avg_time = performance.get('avg_extraction_time', 0)
        if avg_time > 10:
            recommendations.append("Optimize extraction speed - average time per URL is high")
        
        # Field richness recommendations
        avg_fields = performance.get('avg_fields_per_extraction', 0)
        if avg_fields < 3:
            recommendations.append("Enhance extraction strategies to capture more data fields per URL")
        
        if not recommendations:
            recommendations.append("System is performing well across all metrics")
        
        return recommendations
    
    async def create_dashboard_data(self) -> Dict[str, Any]:
        """Create comprehensive dashboard data structure"""
        
        dashboard = {
            "timestamp": datetime.now().isoformat(),
            "overview": await self.get_extraction_performance_metrics(),
            "recent_jobs": await self.get_job_performance_summary(limit=5),
            "strategy_performance": await self.get_success_rates_by_strategy(days_back=7),
            "website_type_performance": await self.get_performance_by_website_type(days_back=7),
            "trending_domains": await self.get_trending_domains(days_back=7, limit=10),
            "hourly_pattern": await self.get_hourly_extraction_pattern(days_back=3),
            "quality_summary": await self.get_data_quality_report(),
            "executive_summary": await self.generate_executive_summary(period_days=7)
        }
        
        return dashboard

# Convenience functions for common analytics queries
async def get_quick_stats(db_manager) -> Dict[str, Any]:
    """Get quick statistics for monitoring"""
    
    engine = AnalyticsEngine(db_manager)
    
    performance = await engine.get_extraction_performance_metrics()
    recent_jobs = await engine.get_job_performance_summary(limit=5)
    
    return {
        "total_extractions": performance.get('total_extractions', 0),
        "success_rate": performance.get('overall_success_rate', 0),
        "avg_confidence": performance.get('avg_confidence', 0),
        "active_jobs": len([job for job in recent_jobs if job['status'] in ['pending', 'running']]),
        "last_updated": datetime.now().isoformat()
    }

async def analyze_job_performance(db_manager, job_id: str) -> Dict[str, Any]:
    """Analyze performance for a specific job"""
    
    engine = AnalyticsEngine(db_manager)
    
    job_metrics = await engine.get_extraction_performance_metrics(job_id=job_id)
    job_quality = await engine.get_data_quality_report(purpose=None)  # Would need job purpose
    
    return {
        "job_id": job_id,
        "performance": job_metrics,
        "quality": job_quality,
        "analysis_date": datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Example usage
    async def test_analytics():
        from ..database.sql_manager import SQLiteManager
        
        db_manager = SQLiteManager("./test_analytics.db")
        await db_manager.connect()
        
        engine = AnalyticsEngine(db_manager)
        
        # Test quick stats (with empty database)
        stats = await get_quick_stats(db_manager)
        print("Quick Stats:", stats)
        
        # Test dashboard creation
        dashboard = await engine.create_dashboard_data()
        print("Dashboard keys:", dashboard.keys())
        
        await db_manager.disconnect()
    
    import asyncio
    asyncio.run(test_analytics())
