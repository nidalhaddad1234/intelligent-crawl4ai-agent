"""
Database Tool - AI-discoverable database operations

This tool provides database capabilities for storing and retrieving scraped data.
"""

import sqlite3
import psycopg2
from typing import Dict, Any, List, Optional, Union
import json
import os
from datetime import datetime

from ..registry import ai_tool, create_example


@ai_tool(
    name="store_data",
    description="Store extracted data in the database with automatic schema detection",
    category="storage",
    examples=[
        create_example(
            "Store product data",
            table_name="products",
            data={"name": "iPhone 15", "price": 999.99, "url": "https://example.com/iphone"},
            upsert_key="url"
        ),
        create_example(
            "Store multiple records",
            table_name="articles",
            data=[
                {"title": "Article 1", "content": "...", "date": "2024-01-01"},
                {"title": "Article 2", "content": "...", "date": "2024-01-02"}
            ]
        )
    ],
    capabilities=[
        "Store data in SQLite or PostgreSQL",
        "Automatic table creation",
        "Schema detection from data",
        "Upsert capabilities",
        "Batch inserts",
        "JSON field support"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def store_data(
    table_name: str,
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    upsert_key: Optional[str] = None,
    database: str = "sqlite",
    connection_string: Optional[str] = None
) -> Dict[str, Any]:
    """
    Store data in database with automatic schema handling
    
    Args:
        table_name: Name of the table to store data in
        data: Single record dict or list of records
        upsert_key: Column to use for upsert operations
        database: Database type - 'sqlite' or 'postgresql'
        connection_string: Database connection string
        
    Returns:
        Dictionary with operation results
    """
    try:
        # Ensure data is a list
        records = data if isinstance(data, list) else [data]
        
        if database == "sqlite":
            db_path = connection_string or os.getenv("SQLITE_PATH", "scraping_data.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        else:
            conn_str = connection_string or os.getenv("POSTGRES_URL")
            conn = psycopg2.connect(conn_str)
        
        cursor = conn.cursor()
        
        # Create table if not exists
        if records:
            columns = _infer_schema(records[0])
            _create_table_if_not_exists(cursor, table_name, columns, database)
        
        # Insert or update data
        inserted = 0
        updated = 0
        
        for record in records:
            # Add metadata
            record['_stored_at'] = datetime.now().isoformat()
            
            if upsert_key and upsert_key in record:
                # Upsert operation
                if database == "sqlite":
                    _sqlite_upsert(cursor, table_name, record, upsert_key)
                else:
                    _postgres_upsert(cursor, table_name, record, upsert_key)
                updated += 1
            else:
                # Regular insert
                columns = list(record.keys())
                values = list(record.values())
                placeholders = ','.join(['?' if database == 'sqlite' else '%s' for _ in values])
                
                query = f"INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})"
                cursor.execute(query, values)
                inserted += 1
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "table": table_name,
            "inserted": inserted,
            "updated": updated,
            "total_records": len(records)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table": table_name
        }


@ai_tool(
    name="query_data",
    description="Query data from the database with flexible filtering",
    category="storage",
    examples=[
        create_example(
            "Get all products under $500",
            table_name="products",
            filters={"price": {"<": 500}},
            order_by="price ASC",
            limit=10
        ),
        create_example(
            "Search articles by keyword",
            table_name="articles",
            search={"title": "AI", "content": "machine learning"},
            limit=20
        )
    ],
    capabilities=[
        "Flexible querying with filters",
        "Full-text search",
        "Sorting and pagination",
        "Aggregations",
        "JSON field queries"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def query_data(
    table_name: str,
    filters: Optional[Dict[str, Any]] = None,
    search: Optional[Dict[str, str]] = None,
    columns: Optional[List[str]] = None,
    order_by: Optional[str] = None,
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    database: str = "sqlite",
    connection_string: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query data from database
    
    Args:
        table_name: Table to query
        filters: Filter conditions (e.g., {"price": {"<": 100}})
        search: Text search in columns
        columns: Specific columns to return
        order_by: Sort order (e.g., "price DESC")
        limit: Maximum records to return
        offset: Number of records to skip
        database: Database type
        connection_string: Database connection
        
    Returns:
        Dictionary with query results
    """
    try:
        if database == "sqlite":
            db_path = connection_string or os.getenv("SQLITE_PATH", "scraping_data.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        else:
            conn_str = connection_string or os.getenv("POSTGRES_URL")
            conn = psycopg2.connect(conn_str)
        
        cursor = conn.cursor()
        
        # Build query
        select_clause = '*' if not columns else ','.join(columns)
        query = f"SELECT {select_clause} FROM {table_name}"
        params = []
        
        # Add WHERE clauses
        where_clauses = []
        
        if filters:
            for col, condition in filters.items():
                if isinstance(condition, dict):
                    for op, val in condition.items():
                        where_clauses.append(f"{col} {op} ?")
                        params.append(val)
                else:
                    where_clauses.append(f"{col} = ?")
                    params.append(condition)
        
        if search:
            for col, term in search.items():
                where_clauses.append(f"{col} LIKE ?")
                params.append(f"%{term}%")
        
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        if limit:
            query += f" LIMIT {limit}"
            
        if offset:
            query += f" OFFSET {offset}"
        
        # Execute query
        if database == "postgresql":
            query = query.replace("?", "%s")
            
        cursor.execute(query, params)
        
        # Fetch results
        rows = cursor.fetchall()
        
        # Convert to dict
        if database == "sqlite":
            results = [dict(row) for row in rows]
        else:
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "table": table_name
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table": table_name
        }


@ai_tool(
    name="aggregate_data",
    description="Perform aggregations on stored data",
    category="analysis",
    examples=[
        create_example(
            "Average price by category",
            table_name="products",
            group_by="category",
            aggregations={"price": ["avg", "min", "max", "count"]}
        ),
        create_example(
            "Daily article count",
            table_name="articles",
            group_by="DATE(created_at)",
            aggregations={"*": ["count"]}
        )
    ],
    capabilities=[
        "Group by operations",
        "Multiple aggregation functions",
        "Date-based grouping",
        "Having clauses",
        "Complex aggregations"
    ],
    performance={
        "speed": "medium",
        "reliability": "high",
        "cost": "low"
    }
)
async def aggregate_data(
    table_name: str,
    group_by: Union[str, List[str]],
    aggregations: Dict[str, List[str]],
    filters: Optional[Dict[str, Any]] = None,
    having: Optional[Dict[str, Any]] = None,
    database: str = "sqlite",
    connection_string: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform aggregations on data
    
    Args:
        table_name: Table to aggregate
        group_by: Column(s) to group by
        aggregations: Dict of column -> [functions]
        filters: WHERE conditions
        having: HAVING conditions
        database: Database type
        connection_string: Connection string
        
    Returns:
        Dictionary with aggregation results
    """
    try:
        if database == "sqlite":
            db_path = connection_string or os.getenv("SQLITE_PATH", "scraping_data.db")
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
        else:
            conn_str = connection_string or os.getenv("POSTGRES_URL")
            conn = psycopg2.connect(conn_str)
        
        cursor = conn.cursor()
        
        # Build aggregation query
        select_parts = []
        
        # Add group by columns
        if isinstance(group_by, str):
            group_by_list = [group_by]
        else:
            group_by_list = group_by
            
        select_parts.extend(group_by_list)
        
        # Add aggregations
        for col, funcs in aggregations.items():
            for func in funcs:
                if col == "*":
                    select_parts.append(f"{func.upper()}(*) AS {func}_all")
                else:
                    select_parts.append(f"{func.upper()}({col}) AS {func}_{col}")
        
        query = f"SELECT {','.join(select_parts)} FROM {table_name}"
        params = []
        
        # Add WHERE clause
        if filters:
            where_clauses = []
            for col, val in filters.items():
                where_clauses.append(f"{col} = ?")
                params.append(val)
            query += " WHERE " + " AND ".join(where_clauses)
        
        # Add GROUP BY
        query += f" GROUP BY {','.join(group_by_list)}"
        
        # Add HAVING clause
        if having:
            having_clauses = []
            for condition, val in having.items():
                having_clauses.append(f"{condition} ?")
                params.append(val)
            query += " HAVING " + " AND ".join(having_clauses)
        
        # Execute
        if database == "postgresql":
            query = query.replace("?", "%s")
            
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert results
        if database == "sqlite":
            results = [dict(row) for row in rows]
        else:
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in rows]
        
        conn.close()
        
        return {
            "success": True,
            "data": results,
            "count": len(results),
            "table": table_name,
            "group_by": group_by_list
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "table": table_name
        }


# Helper functions
def _infer_schema(record: Dict[str, Any]) -> Dict[str, str]:
    """Infer SQL schema from a record"""
    type_map = {
        int: "INTEGER",
        float: "REAL",
        str: "TEXT",
        bool: "INTEGER",
        dict: "TEXT",  # Store as JSON
        list: "TEXT",  # Store as JSON
        type(None): "TEXT"
    }
    
    schema = {}
    for key, value in record.items():
        value_type = type(value)
        schema[key] = type_map.get(value_type, "TEXT")
    
    return schema


def _create_table_if_not_exists(cursor, table_name: str, columns: Dict[str, str], database: str):
    """Create table with inferred schema"""
    column_defs = []
    
    for col, col_type in columns.items():
        column_defs.append(f"{col} {col_type}")
    
    # Add metadata columns
    column_defs.append("_stored_at TEXT")
    
    create_query = f"CREATE TABLE IF NOT EXISTS {table_name} ({','.join(column_defs)})"
    cursor.execute(create_query)


def _sqlite_upsert(cursor, table_name: str, record: Dict[str, Any], upsert_key: str):
    """SQLite upsert operation"""
    columns = list(record.keys())
    values = list(record.values())
    
    # Insert or replace
    placeholders = ','.join(['?' for _ in values])
    update_set = ','.join([f"{col}=excluded.{col}" for col in columns if col != upsert_key])
    
    query = f"""
    INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})
    ON CONFLICT({upsert_key}) DO UPDATE SET {update_set}
    """
    
    cursor.execute(query, values)


def _postgres_upsert(cursor, table_name: str, record: Dict[str, Any], upsert_key: str):
    """PostgreSQL upsert operation"""
    columns = list(record.keys())
    values = list(record.values())
    
    placeholders = ','.join(['%s' for _ in values])
    update_set = ','.join([f"{col}=EXCLUDED.{col}" for col in columns if col != upsert_key])
    
    query = f"""
    INSERT INTO {table_name} ({','.join(columns)}) VALUES ({placeholders})
    ON CONFLICT({upsert_key}) DO UPDATE SET {update_set}
    """
    
    cursor.execute(query, values)
