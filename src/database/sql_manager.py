#!/usr/bin/env python3
"""
SQL Manager
Handles SQLite and PostgreSQL connections for intelligent web scraping
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import sqlite3
import aiosqlite
try:
    import asyncpg
except ImportError:
    asyncpg = None
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager

logger = logging.getLogger("sql_manager")

Base = declarative_base()

class SQLManager(ABC):
    """Abstract base class for SQL database managers"""
    
    def __init__(self, connection_string: str, **kwargs):
        self.connection_string = connection_string
        self.engine = None
        self.session_factory = None
        self.is_connected = False
        
    @abstractmethod
    async def connect(self):
        """Connect to the database"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Disconnect from the database"""
        pass
    
    @abstractmethod
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a query and return results"""
        pass
    
    @abstractmethod
    async def execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute query with multiple parameter sets"""
        pass
    
    @abstractmethod
    async def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> int:
        """Bulk insert data into table"""
        pass
    
    @asynccontextmanager
    async def session(self):
        """Get database session"""
        if not self.session_factory:
            raise RuntimeError("Database not connected")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                raise e

class SQLiteManager(SQLManager):
    """SQLite database manager for development and lightweight deployments"""
    
    def __init__(self, db_path: str = "./data/scraping.db", **kwargs):
        # Ensure directory exists
        db_dir = os.path.dirname(db_path) if os.path.dirname(db_path) else "."
        os.makedirs(db_dir, exist_ok=True)
        
        connection_string = f"sqlite+aiosqlite:///{db_path}"
        super().__init__(connection_string, **kwargs)
        self.db_path = db_path
        self.connection = None
        
    async def connect(self):
        """Connect to SQLite database"""
        try:
            # Create async engine
            self.engine = create_async_engine(
                self.connection_string,
                echo=False,
                future=True
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.is_connected = True
            logger.info(f"Connected to SQLite database: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from SQLite database"""
        if self.engine:
            await self.engine.dispose()
            self.is_connected = False
            logger.info("Disconnected from SQLite database")
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute query and return results as list of dictionaries"""
        try:
            async with self.engine.begin() as conn:
                if params:
                    result = await conn.execute(text(query), params)
                else:
                    result = await conn.execute(text(query))
                
                # Convert to list of dictionaries
                rows = result.fetchall()
                if rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute query with multiple parameter sets"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), params_list)
                return result.rowcount
                
        except Exception as e:
            logger.error(f"Bulk query execution failed: {e}")
            raise
    
    async def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> int:
        """Bulk insert data into table"""
        if not data:
            return 0
        
        try:
            # Build insert query
            columns = list(data[0].keys())
            placeholders = ", ".join([f":{col}" for col in columns])
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            
            return await self.execute_many(query, data)
            
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            raise
    
    async def create_tables(self, base_class=None):
        """Create all tables from SQLAlchemy models"""
        try:
            if base_class is None:
                base_class = Base
                
            async with self.engine.begin() as conn:
                await conn.run_sync(base_class.metadata.create_all)
                
            logger.info("Tables created successfully")
            
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            raise
    
    def get_file_size(self) -> int:
        """Get database file size in bytes"""
        try:
            return os.path.getsize(self.db_path)
        except FileNotFoundError:
            return 0
    
    def get_file_size_mb(self) -> float:
        """Get database file size in MB"""
        return self.get_file_size() / (1024 * 1024)

class PostgreSQLManager(SQLManager):
    """PostgreSQL database manager for production deployments"""
    
    def __init__(self, connection_string: str, **kwargs):
        if asyncpg is None:
            raise ImportError("asyncpg is required for PostgreSQL support. Install with: pip install asyncpg")
        super().__init__(connection_string, **kwargs)
        self.pool = None
        
    async def connect(self):
        """Connect to PostgreSQL database"""
        try:
            # Create async engine with connection pooling
            self.engine = create_async_engine(
                self.connection_string,
                echo=False,
                future=True,
                pool_size=10,
                max_overflow=20,
                pool_recycle=3600
            )
            
            # Create session factory
            self.session_factory = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Test connection
            async with self.engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            
            self.is_connected = True
            logger.info("Connected to PostgreSQL database")
            
        except Exception as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from PostgreSQL database"""
        if self.engine:
            await self.engine.dispose()
            self.is_connected = False
            logger.info("Disconnected from PostgreSQL database")
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        try:
            async with self.engine.begin() as conn:
                if params:
                    result = await conn.execute(text(query), params)
                else:
                    result = await conn.execute(text(query))
                
                rows = result.fetchall()
                if rows:
                    columns = result.keys()
                    return [dict(zip(columns, row)) for row in rows]
                return []
                
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def execute_many(self, query: str, params_list: List[Dict[str, Any]]) -> int:
        """Execute query with multiple parameter sets"""
        try:
            async with self.engine.begin() as conn:
                result = await conn.execute(text(query), params_list)
                return result.rowcount
                
        except Exception as e:
            logger.error(f"Bulk query execution failed: {e}")
            raise
    
    async def bulk_insert(self, table: str, data: List[Dict[str, Any]]) -> int:
        """Bulk insert using PostgreSQL COPY for performance"""
        if not data:
            return 0
        
        try:
            # For PostgreSQL, we can use more efficient bulk operations
            columns = list(data[0].keys())
            placeholders = ", ".join([f":{col}" for col in columns])
            query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            
            return await self.execute_many(query, data)
            
        except Exception as e:
            logger.error(f"Bulk insert failed: {e}")
            raise
    
    async def create_tables(self, base_class=None):
        """Create all tables from SQLAlchemy models"""
        try:
            if base_class is None:
                base_class = Base
                
            async with self.engine.begin() as conn:
                await conn.run_sync(base_class.metadata.create_all)
                
            logger.info("Tables created successfully")
            
        except Exception as e:
            logger.error(f"Table creation failed: {e}")
            raise

class DatabaseFactory:
    """Factory for creating appropriate database manager instances"""
    
    @staticmethod
    def create_database_manager(
        database_type: str = "sqlite",
        connection_string: str = None,
        **kwargs
    ) -> SQLManager:
        """Create database manager based on type and configuration"""
        
        if database_type.lower() == "sqlite":
            db_path = connection_string or kwargs.get("db_path", "./data/scraping.db")
            return SQLiteManager(db_path, **kwargs)
        
        elif database_type.lower() == "postgresql":
            if not connection_string:
                # Build from environment variables
                host = kwargs.get("host", os.getenv("POSTGRES_HOST", "localhost"))
                port = kwargs.get("port", os.getenv("POSTGRES_PORT", "5432"))
                database = kwargs.get("database", os.getenv("POSTGRES_DB", "intelligent_scraping"))
                username = kwargs.get("username", os.getenv("POSTGRES_USER", "scraper_user"))
                password = kwargs.get("password", os.getenv("POSTGRES_PASSWORD", "secure_password_123"))
                
                connection_string = f"postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}"
            
            return PostgreSQLManager(connection_string, **kwargs)
        
        else:
            raise ValueError(f"Unsupported database type: {database_type}")
    
    @staticmethod
    def from_env() -> SQLManager:
        """Create database manager from environment variables"""
        
        database_type = os.getenv("DATABASE_TYPE", "sqlite").lower()
        
        if database_type == "sqlite":
            sqlite_path = os.getenv("SQLITE_PATH", "./data/scraping.db")
            return SQLiteManager(sqlite_path)
        
        elif database_type == "postgresql":
            postgres_url = os.getenv("POSTGRES_URL")
            if postgres_url:
                return PostgreSQLManager(postgres_url)
            else:
                # Build from individual environment variables
                return DatabaseFactory.create_database_manager("postgresql")
        
        else:
            raise ValueError(f"Unsupported DATABASE_TYPE: {database_type}")

# Convenience functions for common operations
async def get_database_stats(db_manager: SQLManager) -> Dict[str, Any]:
    """Get database statistics"""
    
    stats = {
        "database_type": type(db_manager).__name__,
        "is_connected": db_manager.is_connected,
        "tables": {}
    }
    
    if isinstance(db_manager, SQLiteManager):
        stats["file_size_mb"] = db_manager.get_file_size_mb()
        stats["file_path"] = db_manager.db_path
    
    try:
        # Get table counts
        tables = ["extraction_jobs", "extracted_data", "strategy_results", "website_analyses"]
        
        for table in tables:
            try:
                result = await db_manager.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                stats["tables"][table] = result[0]["count"] if result else 0
            except:
                stats["tables"][table] = "table_not_found"
    
    except Exception as e:
        stats["error"] = str(e)
    
    return stats

# Example usage and testing
async def test_database_connection():
    """Test database connections"""
    
    # Test SQLite
    sqlite_manager = SQLiteManager("./test_scraping.db")
    try:
        await sqlite_manager.connect()
        
        # Test basic operations
        await sqlite_manager.execute_query("CREATE TABLE IF NOT EXISTS test (id INTEGER, name TEXT)")
        await sqlite_manager.execute_query("INSERT INTO test (id, name) VALUES (:id, :name)", 
                                         {"id": 1, "name": "test"})
        
        result = await sqlite_manager.execute_query("SELECT * FROM test")
        logger.info(f"SQLite test result: {result}")
        
        await sqlite_manager.disconnect()
        
        # Clean up
        if os.path.exists("./test_scraping.db"):
            os.remove("./test_scraping.db")
        
        return True
        
    except Exception as e:
        logger.error(f"SQLite test failed: {e}")
        return False

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_database_connection())
