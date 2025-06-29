#!/usr/bin/env python3
"""
Database Migration Script for AI-First Architecture

This script helps migrate from the old database schema to the new AI-first schema.
It's only needed for PostgreSQL users. SQLite users can skip this as tables are auto-created.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import asyncpg
    import pandas as pd
except ImportError:
    print("Please install required packages: pip install asyncpg pandas")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.conn: Optional[asyncpg.Connection] = None
    
    async def connect(self):
        """Connect to database"""
        try:
            self.conn = await asyncpg.connect(self.database_url)
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from database"""
        if self.conn:
            await self.conn.close()
            logger.info("Disconnected from database")
    
    async def create_new_tables(self):
        """Create tables for AI-first architecture"""
        
        # Scraped data table (simplified)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scraped_data (
                id SERIAL PRIMARY KEY,
                url TEXT NOT NULL,
                domain TEXT,
                data JSONB NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_scraped_data_url ON scraped_data(url);
            CREATE INDEX IF NOT EXISTS idx_scraped_data_domain ON scraped_data(domain);
            CREATE INDEX IF NOT EXISTS idx_scraped_data_created ON scraped_data(created_at);
        """)
        logger.info("Created scraped_data table")
        
        # AI execution history
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ai_executions (
                id SERIAL PRIMARY KEY,
                request TEXT NOT NULL,
                plan JSONB NOT NULL,
                result JSONB,
                success BOOLEAN DEFAULT FALSE,
                execution_time FLOAT,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_ai_executions_success ON ai_executions(success);
            CREATE INDEX IF NOT EXISTS idx_ai_executions_created ON ai_executions(created_at);
        """)
        logger.info("Created ai_executions table")
        
        # Learning patterns (for ChromaDB reference)
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS learning_patterns (
                id SERIAL PRIMARY KEY,
                pattern_type TEXT NOT NULL,
                pattern_data JSONB NOT NULL,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_learning_patterns_type ON learning_patterns(pattern_type);
            CREATE INDEX IF NOT EXISTS idx_learning_patterns_last_used ON learning_patterns(last_used);
        """)
        logger.info("Created learning_patterns table")
    
    async def migrate_old_data(self):
        """Migrate data from old tables if they exist"""
        
        # Check if old tables exist
        old_tables = await self.conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('web_scraping_results', 'extraction_strategies', 'crawl_jobs')
        """)
        
        if not old_tables:
            logger.info("No old tables found. Skipping data migration.")
            return
        
        migrated_count = 0
        
        # Migrate web_scraping_results if exists
        if any(t['table_name'] == 'web_scraping_results' for t in old_tables):
            logger.info("Migrating web_scraping_results...")
            
            old_results = await self.conn.fetch("""
                SELECT url, extracted_data, strategy_used, created_at 
                FROM web_scraping_results
                WHERE extracted_data IS NOT NULL
            """)
            
            for result in old_results:
                await self.conn.execute("""
                    INSERT INTO scraped_data (url, data, metadata, created_at)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (url) DO UPDATE
                    SET data = EXCLUDED.data,
                        updated_at = CURRENT_TIMESTAMP
                """, 
                    result['url'],
                    result['extracted_data'],
                    {"legacy_strategy": result.get('strategy_used', 'unknown')},
                    result['created_at']
                )
                migrated_count += 1
            
            logger.info(f"Migrated {migrated_count} records from web_scraping_results")
        
        # Archive old tables instead of dropping
        for table in old_tables:
            table_name = table['table_name']
            archive_name = f"archive_{table_name}_{datetime.now().strftime('%Y%m%d')}"
            
            await self.conn.execute(f"""
                ALTER TABLE {table_name} RENAME TO {archive_name}
            """)
            logger.info(f"Archived {table_name} as {archive_name}")
    
    async def create_migration_report(self):
        """Generate migration report"""
        
        report = {
            "migration_date": datetime.now().isoformat(),
            "new_tables": [],
            "migrated_records": 0,
            "archived_tables": []
        }
        
        # Count records in new tables
        tables = ['scraped_data', 'ai_executions', 'learning_patterns']
        for table in tables:
            count = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            report["new_tables"].append({
                "table": table,
                "record_count": count
            })
        
        # Check for archived tables
        archived = await self.conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'archive_%'
        """)
        
        report["archived_tables"] = [t['table_name'] for t in archived]
        
        # Save report
        with open('migration_report.json', 'w') as f:
            import json
            json.dump(report, f, indent=2)
        
        logger.info("Migration report saved to migration_report.json")
        return report
    
    async def run_migration(self):
        """Run the complete migration"""
        try:
            await self.connect()
            
            logger.info("Starting database migration...")
            
            # Create new tables
            await self.create_new_tables()
            
            # Migrate old data
            await self.migrate_old_data()
            
            # Generate report
            report = await self.create_migration_report()
            
            logger.info("Migration completed successfully!")
            
            # Print summary
            print("\n" + "="*50)
            print("MIGRATION SUMMARY")
            print("="*50)
            print(f"Migration Date: {report['migration_date']}")
            print("\nNew Tables Created:")
            for table_info in report['new_tables']:
                print(f"  - {table_info['table']: <20} {table_info['record_count']} records")
            
            if report['archived_tables']:
                print("\nArchived Tables:")
                for table in report['archived_tables']:
                    print(f"  - {table}")
            
            print("\n✅ Migration completed successfully!")
            print("📄 See migration_report.json for details")
            print("="*50)
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            raise
        finally:
            await self.disconnect()


async def main():
    """Main migration function"""
    
    # Get database URL from environment or command line
    if len(sys.argv) > 1:
        database_url = sys.argv[1]
    else:
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/intelligent_crawler')
    
    print(f"🚀 AI-First Database Migration Tool")
    print(f"📊 Database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    print("")
    
    # Confirm migration
    response = input("This will migrate your database to the AI-first schema. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Migration cancelled.")
        return
    
    # Run migration
    migrator = DatabaseMigrator(database_url)
    await migrator.run_migration()


if __name__ == "__main__":
    asyncio.run(main())
