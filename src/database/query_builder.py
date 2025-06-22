#!/usr/bin/env python3
"""
Query Builder
Builds complex SQL queries for analytics and data export
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta

logger = logging.getLogger("query_builder")

class QueryBuilder:
    """Builds complex SQL queries for different database types"""
    
    def __init__(self, database_type: str = "sqlite"):
        self.database_type = database_type.lower()
        
        # Database-specific SQL variants
        self.sql_variants = {
            "sqlite": {
                "datetime_now": "datetime('now')",
                "datetime_interval": "datetime('now', '-{} {}')",
                "limit": "LIMIT {}",
                "offset": "OFFSET {}",
                "json_extract": "json_extract({}, '$.'||{})",
                "concat": "{} || {}",
                "ilike": "LIKE",
                "random": "RANDOM()"
            },
            "postgresql": {
                "datetime_now": "NOW()",
                "datetime_interval": "NOW() - INTERVAL '{} {}'",
                "limit": "LIMIT {}",
                "offset": "OFFSET {}",
                "json_extract": "{}->>{}", 
                "concat": "{} || {}",
                "ilike": "ILIKE",
                "random": "RANDOM()"
            }
        }
    
    def build_job_status_query(self, job_id: str) -> Tuple[str, Dict[str, Any]]:
        """Build query to get comprehensive job status"""
        
        query = """
        SELECT 
            ej.job_id,
            ej.name,
            ej.description,
            ej.purpose,
            ej.status,
            ej.target_urls,
            ej.total_urls,
            ej.successful_extractions,
            ej.failed_extractions,
            ej.primary_strategy,
            ej.extraction_config,
            ej.created_at,
            ej.started_at,
            ej.completed_at,
            ej.total_execution_time,
            ej.average_time_per_url
        FROM extraction_jobs ej
        WHERE ej.job_id = :job_id
        """
        
        return query, {"job_id": job_id}
    
    def build_analytics_query(self, table: str, metrics: List[str], 
                            filters: Dict[str, Any] = None, 
                            group_by: List[str] = None,
                            time_window: str = None) -> Tuple[str, Dict[str, Any]]:
        """Build analytics query with metrics and grouping"""
        
        # Build SELECT clause with metrics
        select_parts = []
        
        for metric in metrics:
            if metric == "count":
                select_parts.append("COUNT(*) as record_count")
            elif metric == "success_rate":
                select_parts.append("AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) as success_rate")
            elif metric == "avg_confidence":
                select_parts.append("AVG(confidence_score) as avg_confidence")
            elif metric == "avg_execution_time":
                select_parts.append("AVG(extraction_time) as avg_execution_time")
            elif metric == "total_fields":
                select_parts.append("SUM(field_count) as total_fields")
            elif metric == "unique_domains":
                select_parts.append("COUNT(DISTINCT domain) as unique_domains")
        
        if group_by:
            select_parts.extend(group_by)
        
        select_clause = ", ".join(select_parts)
        
        # Build FROM clause
        query = f"SELECT {select_clause} FROM {table}"
        
        # Build WHERE clause
        where_conditions = []
        params = {}
        
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    # IN clause
                    placeholders = ", ".join([f":filter_{key}_{i}" for i in range(len(value))])
                    where_conditions.append(f"{key} IN ({placeholders})")
                    for i, v in enumerate(value):
                        params[f"filter_{key}_{i}"] = v
                else:
                    where_conditions.append(f"{key} = :filter_{key}")
                    params[f"filter_{key}"] = value
        
        # Add time window filter
        if time_window:
            time_filter, time_params = self._build_time_filter(time_window)
            if time_filter:
                where_conditions.append(time_filter)
                params.update(time_params)
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Add GROUP BY clause
        if group_by:
            query += f" GROUP BY {', '.join(group_by)}"
        
        return query, params
    
    def build_search_query(self, table: str, filters: Dict[str, Any] = None,
                         search_text: str = None, search_fields: List[str] = None,
                         order_by: str = None, order_desc: bool = False,
                         limit: int = None, offset: int = None) -> Tuple[str, Dict[str, Any]]:
        """Build search query with text search and filtering"""
        
        query = f"SELECT * FROM {table}"
        where_conditions = []
        params = {}
        
        # Add filters
        if filters:
            for key, value in filters.items():
                where_conditions.append(f"{key} = :filter_{key}")
                params[f"filter_{key}"] = value
        
        # Add text search
        if search_text and search_fields:
            search_conditions = []
            like_operator = self.sql_variants[self.database_type]["ilike"]
            
            for field in search_fields:
                search_conditions.append(f"{field} {like_operator} :search_text")
            
            where_conditions.append(f"({' OR '.join(search_conditions)})")
            params["search_text"] = f"%{search_text}%"
        
        # Build WHERE clause
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Add ORDER BY
        if order_by:
            direction = "DESC" if order_desc else "ASC"
            query += f" ORDER BY {order_by} {direction}"
        
        # Add LIMIT and OFFSET
        if limit:
            limit_clause = self.sql_variants[self.database_type]["limit"].format(limit)
            query += f" {limit_clause}"
            
            if offset:
                offset_clause = self.sql_variants[self.database_type]["offset"].format(offset)
                query += f" {offset_clause}"
        
        return query, params
    
    def build_data_export_query(self, table: str, filters: Dict[str, Any] = None,
                              columns: List[str] = None,
                              format_json: bool = False) -> Tuple[str, Dict[str, Any]]:
        """Build query for data export"""
        
        # Select specific columns or all
        if columns:
            select_clause = ", ".join(columns)
        else:
            select_clause = "*"
        
        query = f"SELECT {select_clause} FROM {table}"
        where_conditions = []
        params = {}
        
        # Add filters
        if filters:
            for key, value in filters.items():
                where_conditions.append(f"{key} = :filter_{key}")
                params[f"filter_{key}"] = value
        
        if where_conditions:
            query += " WHERE " + " AND ".join(where_conditions)
        
        # Order by creation time for consistent export
        if table == "extracted_data":
            query += " ORDER BY extracted_at ASC"
        elif table == "extraction_jobs":
            query += " ORDER BY created_at ASC"
        
        return query, params
    
    def build_performance_report_query(self, start_date: datetime = None, 
                                     end_date: datetime = None) -> Tuple[str, Dict[str, Any]]:
        """Build comprehensive performance report query"""
        
        # Default to last 7 days if no dates provided
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        query = """
        SELECT 
            DATE(extracted_at) as extraction_date,
            purpose,
            strategy_used,
            COUNT(*) as total_extractions,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_extractions,
            AVG(confidence_score) as avg_confidence,
            AVG(extraction_time) as avg_extraction_time,
            COUNT(DISTINCT domain) as unique_domains,
            AVG(field_count) as avg_fields_per_extraction
        FROM extracted_data
        WHERE extracted_at BETWEEN :start_date AND :end_date
        GROUP BY DATE(extracted_at), purpose, strategy_used
        ORDER BY extraction_date DESC, total_extractions DESC
        """
        
        params = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        
        return query, params
    
    def build_strategy_effectiveness_query(self, purpose: str = None,
                                         website_type: str = None,
                                         min_samples: int = 5) -> Tuple[str, Dict[str, Any]]:
        """Build query to analyze strategy effectiveness"""
        
        query = """
        SELECT 
            strategy_name,
            strategy_type,
            website_type,
            purpose,
            COUNT(*) as total_attempts,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_attempts,
            AVG(CASE WHEN success = true THEN 1.0 ELSE 0.0 END) as success_rate,
            AVG(confidence_score) as avg_confidence,
            AVG(execution_time) as avg_execution_time,
            COUNT(DISTINCT domain) as unique_domains_tested
        FROM strategy_results
        WHERE 1=1
        """
        
        params = {}
        
        if purpose:
            query += " AND purpose = :purpose"
            params["purpose"] = purpose
        
        if website_type:
            query += " AND website_type = :website_type"
            params["website_type"] = website_type
        
        query += f"""
        GROUP BY strategy_name, strategy_type, website_type, purpose
        HAVING COUNT(*) >= :min_samples
        ORDER BY success_rate DESC, avg_confidence DESC
        """
        
        params["min_samples"] = min_samples
        
        return query, params
    
    def build_data_quality_report_query(self, job_id: str = None) -> Tuple[str, Dict[str, Any]]:
        """Build query for data quality analysis"""
        
        query = """
        SELECT 
            purpose,
            website_type,
            COUNT(*) as total_records,
            AVG(confidence_score) as avg_confidence,
            AVG(data_quality_score) as avg_data_quality,
            AVG(field_count) as avg_field_count,
            SUM(CASE WHEN field_count >= 5 THEN 1 ELSE 0 END) as high_quality_records,
            SUM(CASE WHEN confidence_score >= 0.8 THEN 1 ELSE 0 END) as high_confidence_records
        FROM extracted_data
        WHERE success = true
        """
        
        params = {}
        
        if job_id:
            query += " AND job_id = :job_id"
            params["job_id"] = job_id
        
        query += """
        GROUP BY purpose, website_type
        ORDER BY avg_data_quality DESC, avg_confidence DESC
        """
        
        return query, params
    
    def build_learning_insights_query(self, website_type: str = None,
                                    purpose: str = None) -> Tuple[str, Dict[str, Any]]:
        """Build query to get learning insights for strategy improvement"""
        
        query = """
        SELECT 
            ld.website_type,
            ld.purpose,
            ld.strategy_name,
            ld.success_rate,
            ld.avg_confidence,
            ld.sample_size,
            ld.learned_selectors,
            ld.frameworks,
            COUNT(ed.id) as recent_usage
        FROM learning_data ld
        LEFT JOIN extracted_data ed ON (
            ed.website_type = ld.website_type 
            AND ed.purpose = ld.purpose 
            AND ed.strategy_used = ld.strategy_name
            AND ed.extracted_at > datetime('now', '-30 days')
        )
        WHERE ld.success_rate >= 0.7
        """
        
        params = {}
        
        if website_type:
            query += " AND ld.website_type = :website_type"
            params["website_type"] = website_type
        
        if purpose:
            query += " AND ld.purpose = :purpose"
            params["purpose"] = purpose
        
        query += """
        GROUP BY ld.id, ld.website_type, ld.purpose, ld.strategy_name
        ORDER BY ld.success_rate DESC, ld.sample_size DESC
        """
        
        return query, params
    
    def _build_time_filter(self, time_window: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Build time-based filter clause"""
        
        if not time_window:
            return None, {}
        
        # Parse time window (e.g., "1 hour", "7 days", "30 minutes")
        parts = time_window.lower().split()
        if len(parts) != 2:
            return None, {}
        
        try:
            amount = int(parts[0])
            unit = parts[1].rstrip('s')  # Remove plural 's'
        except ValueError:
            return None, {}
        
        # Map units to database interval format
        unit_mapping = {
            "minute": "minutes",
            "hour": "hours", 
            "day": "days",
            "week": "days",  # Convert weeks to days
            "month": "days"  # Convert months to days (approximate)
        }
        
        if unit == "week":
            amount *= 7
            unit = "day"
        elif unit == "month":
            amount *= 30
            unit = "day"
        
        db_unit = unit_mapping.get(unit)
        if not db_unit:
            return None, {}
        
        # Build database-specific time filter
        if self.database_type == "sqlite":
            time_expr = f"datetime('now', '-{amount} {db_unit}')"
            filter_clause = f"extracted_at > {time_expr}"
        else:  # PostgreSQL
            filter_clause = f"extracted_at > NOW() - INTERVAL '{amount} {db_unit}'"
        
        return filter_clause, {}
    
    def build_cleanup_query(self, table: str, retention_days: int = 30) -> Tuple[str, Dict[str, Any]]:
        """Build query to clean up old data"""
        
        # Determine the date column for each table
        date_columns = {
            "extracted_data": "extracted_at",
            "strategy_results": "executed_at",
            "website_analyses": "analyzed_at",
            "extraction_jobs": "created_at"
        }
        
        date_column = date_columns.get(table, "created_at")
        
        if self.database_type == "sqlite":
            cutoff_expr = f"datetime('now', '-{retention_days} days')"
        else:  # PostgreSQL
            cutoff_expr = f"NOW() - INTERVAL '{retention_days} days'"
        
        query = f"DELETE FROM {table} WHERE {date_column} < {cutoff_expr}"
        
        return query, {}

# Convenience functions for common queries
def get_job_summary_query(database_type: str = "sqlite") -> str:
    """Get a comprehensive job summary query"""
    
    if database_type == "sqlite":
        return """
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
            COUNT(ed.id) as data_records,
            AVG(ed.confidence_score) as avg_confidence,
            AVG(ed.extraction_time) as avg_time_per_url,
            ROUND((ej.successful_extractions * 100.0 / ej.total_urls), 2) as success_percentage
        FROM extraction_jobs ej
        LEFT JOIN extracted_data ed ON ej.job_id = ed.job_id
        GROUP BY ej.job_id, ej.name, ej.purpose, ej.status, ej.total_urls, 
                 ej.successful_extractions, ej.failed_extractions, ej.created_at, ej.completed_at
        ORDER BY ej.created_at DESC
        """
    else:  # PostgreSQL
        return """
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
            COUNT(ed.id) as data_records,
            AVG(ed.confidence_score) as avg_confidence,
            AVG(ed.extraction_time) as avg_time_per_url,
            ROUND((ej.successful_extractions::FLOAT * 100.0 / ej.total_urls), 2) as success_percentage
        FROM extraction_jobs ej
        LEFT JOIN extracted_data ed ON ej.job_id = ed.job_id
        GROUP BY ej.job_id, ej.name, ej.purpose, ej.status, ej.total_urls, 
                 ej.successful_extractions, ej.failed_extractions, ej.created_at, ej.completed_at
        ORDER BY ej.created_at DESC
        """

def get_performance_dashboard_query(database_type: str = "sqlite") -> str:
    """Get query for performance dashboard metrics"""
    
    if database_type == "sqlite":
        return """
        SELECT 
            'last_24_hours' as period,
            COUNT(*) as total_extractions,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_extractions,
            AVG(confidence_score) as avg_confidence,
            AVG(extraction_time) as avg_extraction_time,
            COUNT(DISTINCT job_id) as active_jobs,
            COUNT(DISTINCT domain) as unique_domains
        FROM extracted_data
        WHERE extracted_at > datetime('now', '-24 hours')
        
        UNION ALL
        
        SELECT 
            'last_7_days' as period,
            COUNT(*) as total_extractions,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_extractions,
            AVG(confidence_score) as avg_confidence,
            AVG(extraction_time) as avg_extraction_time,
            COUNT(DISTINCT job_id) as active_jobs,
            COUNT(DISTINCT domain) as unique_domains
        FROM extracted_data
        WHERE extracted_at > datetime('now', '-7 days')
        """
    else:  # PostgreSQL
        return """
        SELECT 
            'last_24_hours' as period,
            COUNT(*) as total_extractions,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_extractions,
            AVG(confidence_score) as avg_confidence,
            AVG(extraction_time) as avg_extraction_time,
            COUNT(DISTINCT job_id) as active_jobs,
            COUNT(DISTINCT domain) as unique_domains
        FROM extracted_data
        WHERE extracted_at > NOW() - INTERVAL '24 hours'
        
        UNION ALL
        
        SELECT 
            'last_7_days' as period,
            COUNT(*) as total_extractions,
            SUM(CASE WHEN success = true THEN 1 ELSE 0 END) as successful_extractions,
            AVG(confidence_score) as avg_confidence,
            AVG(extraction_time) as avg_extraction_time,
            COUNT(DISTINCT job_id) as active_jobs,
            COUNT(DISTINCT domain) as unique_domains
        FROM extracted_data
        WHERE extracted_at > NOW() - INTERVAL '7 days'
        """

if __name__ == "__main__":
    # Test query builder
    builder = QueryBuilder("sqlite")
    
    # Test job status query
    query, params = builder.build_job_status_query("test_job_123")
    print("Job Status Query:")
    print(query)
    print("Params:", params)
    print()
    
    # Test analytics query
    query, params = builder.build_analytics_query(
        table="extracted_data",
        metrics=["count", "success_rate", "avg_confidence"],
        filters={"purpose": "company_info"},
        time_window="7 days"
    )
    print("Analytics Query:")
    print(query)
    print("Params:", params)
