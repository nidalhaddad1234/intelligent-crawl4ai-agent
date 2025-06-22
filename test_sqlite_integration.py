#!/usr/bin/env python3
"""
Test SQLite Integration
Comprehensive test of the intelligent scraping system with SQLite database
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database.sql_manager import SQLiteManager, DatabaseFactory
from database.schema_manager import SchemaManager
from database.data_normalizer import DataNormalizer, normalize_extraction_result
from database.query_builder import QueryBuilder
from models.extraction_models import (
    Base, ExtractionJob, ExtractedData, StrategyResult, 
    create_extraction_job, create_extracted_data
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sqlite_integration_test")

async def test_sqlite_manager():
    """Test SQLite manager basic operations"""
    logger.info("Testing SQLite Manager...")
    
    # Create test database
    db_manager = SQLiteManager("./test_sqlite_integration.db")
    
    try:
        # Test connection
        await db_manager.connect()
        logger.info("✅ SQLite connection successful")
        
        # Test table creation
        await db_manager.create_tables(Base)
        logger.info("✅ Database tables created")
        
        # Test basic query
        result = await db_manager.execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row['name'] for row in result]
        logger.info(f"✅ Created tables: {table_names}")
        
        expected_tables = ['extraction_jobs', 'extracted_data', 'strategy_results', 'website_analyses', 'learning_data']
        missing_tables = [t for t in expected_tables if t not in table_names]
        
        if missing_tables:
            logger.error(f"❌ Missing tables: {missing_tables}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ SQLite manager test failed: {e}")
        return False
    
    finally:
        await db_manager.disconnect()

async def test_data_models():
    """Test SQLAlchemy data models"""
    logger.info("Testing SQLAlchemy Models...")
    
    db_manager = SQLiteManager("./test_sqlite_integration.db")
    
    try:
        await db_manager.connect()
        
        # Test creating extraction job
        job = create_extraction_job(
            name="Test Job",
            purpose="company_info", 
            target_urls=["https://example.com", "https://test.com"],
            description="Testing SQLite integration"
        )
        
        # Store job
        async with db_manager.session() as session:
            session.add(job)
            await session.flush()
            job_id = job.job_id
            logger.info(f"✅ Created extraction job: {job_id}")
        
        # Test creating extracted data
        extracted_record = create_extracted_data(
            job_id=job_id,
            url="https://example.com",
            purpose="company_info",
            strategy_used="css_extraction",
            raw_data={
                "company_name": "Example Corp",
                "email": "contact@example.com",
                "phone": "(555) 123-4567",
                "website": "https://example.com"
            },
            success=True,
            confidence_score=0.85,
            extraction_time=2.5
        )
        
        # Store extracted data
        async with db_manager.session() as session:
            session.add(extracted_record)
            logger.info("✅ Created extracted data record")
        
        # Test querying data
        query = "SELECT * FROM extraction_jobs WHERE job_id = :job_id"
        result = await db_manager.execute_query(query, {"job_id": job_id})
        
        if result:
            logger.info(f"✅ Successfully queried job data: {result[0]['name']}")
        else:
            logger.error("❌ Failed to query job data")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data models test failed: {e}")
        return False
    
    finally:
        await db_manager.disconnect()

async def test_data_normalization():
    """Test data normalization pipeline"""
    logger.info("Testing Data Normalization...")
    
    try:
        normalizer = DataNormalizer()
        
        # Test data with various formats
        test_data = {
            "Company Name": "  ACME CORP INC.  ",
            "E-mail Address": "Contact@ACME.COM",
            "Phone Number": "(555) 123-4567",
            "Web Site": "www.acme.com",
            "Rating": "4.5/5 stars",
            "Price Range": "$99.99 - $199.99",
            "Address": "123 Main St, New York, NY 10001"
        }
        
        # Normalize the data
        normalized = normalizer.normalize_extracted_data(test_data, "company_info")
        
        # Check results
        expected_fields = ['company_name', 'email_address', 'phone_number', 'web_site']
        found_fields = [field for field in expected_fields if field in normalized]
        
        logger.info(f"✅ Normalized {len(normalized)} fields")
        logger.info(f"✅ Found expected fields: {found_fields}")
        
        # Test quality score calculation
        quality_score = normalizer.calculate_data_quality_score(test_data, normalized)
        logger.info(f"✅ Data quality score: {quality_score:.2f}")
        
        # Test normalize_extraction_result function
        extraction_result = {
            "success": True,
            "extracted_data": test_data,
            "confidence_score": 0.8
        }
        
        enhanced_result = normalize_extraction_result(extraction_result, "company_info", "https://acme.com")
        logger.info(f"✅ Enhanced result with {len(enhanced_result['normalized_data'])} normalized fields")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data normalization test failed: {e}")
        return False

async def test_schema_manager():
    """Test automatic schema detection and management"""
    logger.info("Testing Schema Manager...")
    
    db_manager = SQLiteManager("./test_sqlite_integration.db")
    
    try:
        await db_manager.connect()
        schema_manager = SchemaManager(db_manager)
        
        # Test data for schema detection
        sample_data = [
            {
                "company_name": "Acme Corp",
                "email": "contact@acme.com",
                "phone": "+1-555-123-4567",
                "website": "https://acme.com",
                "rating": "4.5/5",
                "employees": "100-500",
                "founded": "2010"
            },
            {
                "company_name": "Tech Solutions Inc",
                "email": "info@techsolutions.com", 
                "phone": "(555) 987-6543",
                "website": "https://techsolutions.com",
                "rating": "4.8",
                "employees": "50-100",
                "founded": "2015"
            }
        ]
        
        # Create schema from sample data
        schema = await schema_manager.create_schema_from_data(
            sample_data, 
            "test_companies",
            "company_info"
        )
        
        logger.info(f"✅ Generated schema with {len(schema)} fields")
        logger.info(f"✅ Schema fields: {list(schema.keys())}")
        
        # Test data type detection
        for record in sample_data:
            for field, value in record.items():
                detected_type = schema_manager.detect_data_type(field, value, "company_info")
                logger.info(f"   {field}: {value} -> {detected_type}")
        
        # Test table exists
        result = await db_manager.execute_query(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='test_companies'"
        )
        
        if result:
            logger.info("✅ Dynamic table created successfully")
        else:
            logger.error("❌ Dynamic table creation failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Schema manager test failed: {e}")
        return False
    
    finally:
        await db_manager.disconnect()

async def test_query_builder():
    """Test query builder for complex analytics"""
    logger.info("Testing Query Builder...")
    
    try:
        builder = QueryBuilder("sqlite")
        
        # Test job status query
        query, params = builder.build_job_status_query("test_job_123")
        logger.info("✅ Built job status query")
        
        # Test analytics query
        query, params = builder.build_analytics_query(
            table="extracted_data",
            metrics=["count", "success_rate", "avg_confidence"],
            filters={"purpose": "company_info"},
            time_window="7 days"
        )
        logger.info("✅ Built analytics query")
        
        # Test search query
        query, params = builder.build_search_query(
            table="extracted_data",
            filters={"success": True},
            search_text="acme",
            search_fields=["url", "raw_data"],
            order_by="extracted_at",
            order_desc=True,
            limit=10
        )
        logger.info("✅ Built search query")
        
        # Test performance report query
        query, params = builder.build_performance_report_query()
        logger.info("✅ Built performance report query")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Query builder test failed: {e}")
        return False

async def test_database_factory():
    """Test database factory for environment-based selection"""
    logger.info("Testing Database Factory...")
    
    try:
        # Test SQLite creation
        sqlite_manager = DatabaseFactory.create_database_manager(
            database_type="sqlite",
            connection_string="./test_factory_sqlite.db"
        )
        
        await sqlite_manager.connect()
        logger.info("✅ Factory created SQLite manager")
        
        # Test query execution
        await sqlite_manager.execute_query("CREATE TABLE test_table (id INTEGER, name TEXT)")
        await sqlite_manager.execute_query("INSERT INTO test_table (id, name) VALUES (1, 'test')")
        
        result = await sqlite_manager.execute_query("SELECT * FROM test_table")
        if result and result[0]['name'] == 'test':
            logger.info("✅ Factory SQLite manager works correctly")
        else:
            logger.error("❌ Factory SQLite manager query failed")
            return False
        
        await sqlite_manager.disconnect()
        
        # Clean up test file
        if os.path.exists("./test_factory_sqlite.db"):
            os.remove("./test_factory_sqlite.db")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Database factory test failed: {e}")
        return False

async def test_full_integration():
    """Test full integration with normalized data storage"""
    logger.info("Testing Full Integration Pipeline...")
    
    db_manager = SQLiteManager("./test_sqlite_integration.db")
    
    try:
        await db_manager.connect()
        normalizer = DataNormalizer()
        
        # Create a realistic extraction job
        job = create_extraction_job(
            name="Integration Test Job",
            purpose="company_info",
            target_urls=[
                "https://example.com",
                "https://acme-corp.com", 
                "https://tech-solutions.com"
            ],
            description="Full integration test with multiple companies"
        )
        
        # Store job
        async with db_manager.session() as session:
            session.add(job)
            await session.flush()
            job_id = job.job_id
        
        # Simulate extraction results
        test_extractions = [
            {
                "url": "https://example.com",
                "raw_data": {
                    "company_name": "Example Corp",
                    "email": "contact@example.com",
                    "phone": "(555) 123-4567",
                    "website": "https://example.com",
                    "description": "A leading technology company"
                },
                "success": True,
                "confidence_score": 0.9,
                "strategy_used": "css_extraction"
            },
            {
                "url": "https://acme-corp.com",
                "raw_data": {
                    "company_name": "ACME Corporation",
                    "email": "info@acme-corp.com", 
                    "phone": "+1-555-987-6543",
                    "website": "www.acme-corp.com",
                    "description": "Industrial solutions provider"
                },
                "success": True,
                "confidence_score": 0.85,
                "strategy_used": "hybrid_extraction"
            },
            {
                "url": "https://tech-solutions.com",
                "raw_data": {},
                "success": False,
                "error_message": "Site unavailable",
                "strategy_used": "css_extraction"
            }
        ]
        
        # Process and store each extraction
        extraction_records = []
        
        for extraction in test_extractions:
            # Normalize the data
            if extraction["success"]:
                normalized_result = normalize_extraction_result(extraction, "company_info", extraction["url"])
                normalized_data = normalized_result.get("normalized_data", {})
                data_quality = normalized_result.get("data_quality_score", 0.0)
            else:
                normalized_data = {}
                data_quality = 0.0
            
            # Create record
            record = create_extracted_data(
                job_id=job_id,
                url=extraction["url"],
                purpose="company_info",
                strategy_used=extraction["strategy_used"],
                raw_data=extraction["raw_data"],
                normalized_data=normalized_data,
                success=extraction["success"],
                confidence_score=extraction.get("confidence_score", 0.0),
                data_quality_score=data_quality,
                extraction_time=2.0,
                error_message=extraction.get("error_message")
            )
            
            extraction_records.append(record)
        
        # Bulk store all records
        async with db_manager.session() as session:
            session.add_all(extraction_records)
        
        logger.info(f"✅ Stored {len(extraction_records)} extraction records")
        
        # Test analytics queries
        builder = QueryBuilder("sqlite")
        
        # Get job summary
        query, params = builder.build_analytics_query(
            table="extracted_data",
            metrics=["count", "success_rate", "avg_confidence"],
            filters={"job_id": job_id}
        )
        
        analytics = await db_manager.execute_query(query, params)
        if analytics:
            stats = analytics[0]
            logger.info(f"✅ Job Analytics: {stats['record_count']} records, "
                       f"{stats['success_rate']:.1%} success rate, "
                       f"{stats['avg_confidence']:.2f} avg confidence")
        
        # Test data export
        export_query, export_params = builder.build_data_export_query(
            table="extracted_data",
            filters={"job_id": job_id, "success": True}
        )
        
        export_data = await db_manager.execute_query(export_query, export_params)
        logger.info(f"✅ Exported {len(export_data)} successful extractions")
        
        # Display sample normalized data
        if export_data:
            sample_record = export_data[0]
            logger.info(f"✅ Sample normalized data: {sample_record.get('normalized_data', {})}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Full integration test failed: {e}")
        return False
    
    finally:
        await db_manager.disconnect()

async def run_all_tests():
    """Run all SQLite integration tests"""
    
    logger.info("🧪 Starting Comprehensive SQLite Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("SQLite Manager", test_sqlite_manager),
        ("Data Models", test_data_models),
        ("Data Normalization", test_data_normalization),
        ("Schema Manager", test_schema_manager),
        ("Query Builder", test_query_builder),
        ("Database Factory", test_database_factory),
        ("Full Integration", test_full_integration),
    ]
    
    results = {}
    passed = 0
    
    for test_name, test_func in tests:
        logger.info(f"\n🔹 Running: {test_name}")
        logger.info("-" * 40)
        
        try:
            result = await test_func()
            results[test_name] = "PASS" if result else "FAIL"
            if result:
                passed += 1
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            results[test_name] = f"ERROR: {e}"
            logger.error(f"💥 {test_name}: ERROR - {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("🎯 SQLITE INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    for test_name, result in results.items():
        status_emoji = "✅" if result == "PASS" else "❌"
        logger.info(f"{status_emoji} {test_name}: {result}")
    
    total_tests = len(tests)
    success_rate = (passed / total_tests) * 100
    
    logger.info(f"\n📊 Results: {passed}/{total_tests} tests passed ({success_rate:.1f}%)")
    
    if passed == total_tests:
        logger.info("🎉 ALL TESTS PASSED! SQLite integration is fully functional!")
        logger.info("\n💡 Next Steps:")
        logger.info("   1. Set DATABASE_TYPE=sqlite in your .env file")
        logger.info("   2. Start using the system with: python test_integration.py")
        logger.info("   3. Check your SQLite database at: ./data/scraping.db")
    else:
        logger.warning(f"⚠️  {total_tests - passed} tests failed. Check logs above for details.")
    
    # Cleanup test databases
    test_files = ["./test_sqlite_integration.db", "./test_factory_sqlite.db"]
    for test_file in test_files:
        if os.path.exists(test_file):
            os.remove(test_file)
            logger.info(f"🧹 Cleaned up test file: {test_file}")
    
    return passed == total_tests

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
