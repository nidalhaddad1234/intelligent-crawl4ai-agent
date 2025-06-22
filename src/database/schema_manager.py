#!/usr/bin/env python3
"""
Schema Manager
Handles automatic schema detection and creation for extracted data
"""

import logging
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from urllib.parse import urlparse

logger = logging.getLogger("schema_manager")

class SchemaManager:
    """Manages database schemas and auto-detection of data types"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        
        # Data type detection patterns
        self.type_patterns = {
            'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
            'phone': re.compile(r'^[\+]?[\d\s\(\)\-\.]{10,}$'),
            'url': re.compile(r'^https?://[^\s]+$'),
            'price': re.compile(r'^[\$€£¥]?[\d,]+\.?\d*$'),
            'date': re.compile(r'^\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}$'),
            'rating': re.compile(r'^[\d\.]+\s*[/⭐★]?\s*[\d]?$'),
            'number': re.compile(r'^[\d,]+\.?\d*$')
        }
    
    async def create_schema_from_data(self, sample_data: List[Dict[str, Any]], 
                                    table_name: str, purpose: str = None) -> Dict[str, str]:
        """
        Analyze sample data and create appropriate database schema
        
        Args:
            sample_data: List of dictionaries representing extracted data
            table_name: Name for the table
            purpose: Extraction purpose (helps with field interpretation)
            
        Returns:
            Dictionary mapping field names to SQL data types
        """
        
        if not sample_data:
            return {}
        
        logger.info(f"Creating schema for {table_name} with {len(sample_data)} samples")
        
        # Analyze all fields across all samples
        field_analysis = {}
        
        for record in sample_data:
            if not isinstance(record, dict):
                continue
                
            for field_name, value in record.items():
                if field_name not in field_analysis:
                    field_analysis[field_name] = {
                        'values': [],
                        'types': set(),
                        'max_length': 0,
                        'is_nullable': False,
                        'frequency': 0
                    }
                
                analysis = field_analysis[field_name]
                analysis['frequency'] += 1
                
                # Handle None/null values
                if value is None or value == '':
                    analysis['is_nullable'] = True
                    continue
                
                # Store value for analysis
                analysis['values'].append(value)
                
                # Detect data type
                detected_type = self.detect_data_type(field_name, value, purpose)
                analysis['types'].add(detected_type)
                
                # Track maximum length for strings
                if isinstance(value, str):
                    analysis['max_length'] = max(analysis['max_length'], len(value))
        
        # Generate SQL schema
        schema = {}
        total_samples = len(sample_data)
        
        for field_name, analysis in field_analysis.items():
            sql_type = self._determine_sql_type(field_name, analysis, total_samples)
            schema[field_name] = sql_type
        
        # Create the table if it doesn't exist
        await self._create_table_if_not_exists(table_name, schema)
        
        return schema
    
    def detect_data_type(self, field_name: str, value: Any, purpose: str = None) -> str:
        """
        Detect the data type of a field based on its name, value, and context
        
        Args:
            field_name: Name of the field
            value: Value to analyze
            purpose: Extraction purpose for context
            
        Returns:
            Detected data type as string
        """
        
        # Handle non-string values
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, (list, dict)):
            return 'json'
        elif isinstance(value, datetime):
            return 'datetime'
        
        # Convert to string for pattern matching
        str_value = str(value).strip()
        
        if not str_value:
            return 'text'
        
        # Field name-based detection (contextual)
        field_lower = field_name.lower()
        
        # Common field name patterns
        if any(keyword in field_lower for keyword in ['email', 'mail']):
            if self.type_patterns['email'].match(str_value):
                return 'email'
        
        if any(keyword in field_lower for keyword in ['phone', 'tel', 'mobile']):
            if self.type_patterns['phone'].match(str_value):
                return 'phone'
        
        if any(keyword in field_lower for keyword in ['url', 'link', 'website', 'href']):
            if self.type_patterns['url'].match(str_value):
                return 'url'
        
        if any(keyword in field_lower for keyword in ['price', 'cost', 'amount', 'fee']):
            if self.type_patterns['price'].match(str_value):
                return 'price'
        
        if any(keyword in field_lower for keyword in ['date', 'time', 'created', 'updated']):
            if self.type_patterns['date'].match(str_value):
                return 'date'
        
        if any(keyword in field_lower for keyword in ['rating', 'score', 'stars']):
            if self.type_patterns['rating'].match(str_value):
                return 'rating'
        
        # Pattern-based detection
        for pattern_name, pattern in self.type_patterns.items():
            if pattern.match(str_value):
                return pattern_name
        
        # Length-based classification for text
        if len(str_value) > 500:
            return 'long_text'
        elif len(str_value) > 100:
            return 'medium_text'
        else:
            return 'text'
    
    def _determine_sql_type(self, field_name: str, analysis: Dict[str, Any], 
                          total_samples: int) -> str:
        """
        Determine the appropriate SQL data type for a field
        
        Args:
            field_name: Name of the field
            analysis: Analysis results from detect_data_type
            total_samples: Total number of samples analyzed
            
        Returns:
            SQL data type string
        """
        
        types = analysis['types']
        max_length = analysis['max_length']
        is_nullable = analysis['is_nullable']
        frequency = analysis['frequency']
        
        # Calculate fill rate
        fill_rate = frequency / total_samples if total_samples > 0 else 0
        
        # Handle mixed types - choose most restrictive common type
        if len(types) > 1:
            if 'json' in types:
                return 'JSON'
            elif any(t in types for t in ['long_text', 'medium_text', 'text']):
                return f'TEXT'
            elif 'float' in types or 'number' in types:
                return 'REAL'
            else:
                return 'TEXT'
        
        # Single type mapping
        primary_type = list(types)[0] if types else 'text'
        
        type_mapping = {
            'boolean': 'BOOLEAN',
            'integer': 'INTEGER',
            'float': 'REAL',
            'email': f'VARCHAR({min(max_length + 50, 320)})',  # RFC 5321 limit
            'phone': f'VARCHAR({min(max_length + 10, 50)})',
            'url': f'VARCHAR({min(max_length + 100, 2000)})',
            'price': 'DECIMAL(10,2)',
            'date': 'DATETIME',
            'datetime': 'DATETIME',
            'rating': 'REAL',
            'number': 'REAL',
            'json': 'JSON',
            'long_text': 'TEXT',
            'medium_text': f'VARCHAR({min(max_length + 100, 1000)})',
            'text': f'VARCHAR({min(max_length + 50, 500)})'
        }
        
        return type_mapping.get(primary_type, 'TEXT')
    
    async def _create_table_if_not_exists(self, table_name: str, schema: Dict[str, str]):
        """Create table with dynamic schema if it doesn't exist"""
        
        try:
            # Build CREATE TABLE statement
            columns = []
            
            # Add standard columns
            columns.append("id INTEGER PRIMARY KEY AUTOINCREMENT" if isinstance(self.db_manager, type(self.db_manager)) 
                          and "SQLite" in type(self.db_manager).__name__ else "id SERIAL PRIMARY KEY")
            columns.append("created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            columns.append("updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            
            # Add detected columns
            for field_name, sql_type in schema.items():
                # Sanitize field name
                safe_field_name = self._sanitize_field_name(field_name)
                columns.append(f"{safe_field_name} {sql_type}")
            
            # Create table
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(columns)}
            )
            """
            
            await self.db_manager.execute_query(create_sql)
            logger.info(f"Table {table_name} created/verified with {len(schema)} fields")
            
        except Exception as e:
            logger.error(f"Failed to create table {table_name}: {e}")
            raise
    
    def _sanitize_field_name(self, field_name: str) -> str:
        """Sanitize field name for SQL safety"""
        
        # Replace special characters with underscores
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', field_name)
        
        # Ensure it starts with a letter or underscore
        if not re.match(r'^[a-zA-Z_]', sanitized):
            sanitized = f"field_{sanitized}"
        
        # Limit length
        if len(sanitized) > 63:  # PostgreSQL identifier limit
            sanitized = sanitized[:63]
        
        # Avoid SQL keywords
        sql_keywords = {
            'select', 'from', 'where', 'insert', 'update', 'delete', 'create', 'drop',
            'table', 'index', 'primary', 'key', 'foreign', 'references', 'null',
            'not', 'and', 'or', 'order', 'by', 'group', 'having', 'limit'
        }
        
        if sanitized.lower() in sql_keywords:
            sanitized = f"{sanitized}_field"
        
        return sanitized
    
    async def analyze_existing_data(self, table_name: str, purpose: str = None) -> Dict[str, Any]:
        """
        Analyze existing data in a table to understand its structure and quality
        
        Args:
            table_name: Name of table to analyze
            purpose: Purpose context for analysis
            
        Returns:
            Analysis results including data quality metrics
        """
        
        try:
            # Get sample data
            sample_query = f"SELECT * FROM {table_name} LIMIT 1000"
            sample_data = await self.db_manager.execute_query(sample_query)
            
            if not sample_data:
                return {"error": "No data found in table"}
            
            # Get table info
            count_query = f"SELECT COUNT(*) as total FROM {table_name}"
            count_result = await self.db_manager.execute_query(count_query)
            total_rows = count_result[0]['total'] if count_result else 0
            
            # Analyze field completeness
            field_analysis = {}
            
            for record in sample_data:
                for field_name, value in record.items():
                    if field_name not in field_analysis:
                        field_analysis[field_name] = {
                            'total_values': 0,
                            'null_values': 0,
                            'empty_values': 0,
                            'unique_values': set(),
                            'data_types': set()
                        }
                    
                    analysis = field_analysis[field_name]
                    analysis['total_values'] += 1
                    
                    if value is None:
                        analysis['null_values'] += 1
                    elif str(value).strip() == '':
                        analysis['empty_values'] += 1
                    else:
                        analysis['unique_values'].add(str(value))
                        analysis['data_types'].add(type(value).__name__)
            
            # Calculate quality metrics
            quality_metrics = {}
            for field_name, analysis in field_analysis.items():
                total = analysis['total_values']
                nulls = analysis['null_values']
                empties = analysis['empty_values']
                
                quality_metrics[field_name] = {
                    'completeness': (total - nulls - empties) / total if total > 0 else 0,
                    'uniqueness': len(analysis['unique_values']) / total if total > 0 else 0,
                    'data_types': list(analysis['data_types']),
                    'sample_values': list(analysis['unique_values'])[:10]
                }
            
            return {
                'table_name': table_name,
                'total_rows': total_rows,
                'sample_size': len(sample_data),
                'field_count': len(field_analysis),
                'quality_metrics': quality_metrics,
                'overall_quality': sum(m['completeness'] for m in quality_metrics.values()) / len(quality_metrics) if quality_metrics else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze table {table_name}: {e}")
            return {"error": str(e)}
    
    async def suggest_schema_improvements(self, table_name: str) -> List[str]:
        """
        Suggest improvements to an existing table schema
        
        Args:
            table_name: Name of table to analyze
            
        Returns:
            List of improvement suggestions
        """
        
        suggestions = []
        
        try:
            analysis = await self.analyze_existing_data(table_name)
            
            if 'error' in analysis:
                return [f"Could not analyze table: {analysis['error']}"]
            
            quality_metrics = analysis.get('quality_metrics', {})
            
            for field_name, metrics in quality_metrics.items():
                completeness = metrics['completeness']
                uniqueness = metrics['uniqueness']
                
                # Suggest improvements based on data quality
                if completeness < 0.5:
                    suggestions.append(f"Field '{field_name}' has low completeness ({completeness:.1%}) - consider improving extraction")
                
                if uniqueness > 0.95 and field_name not in ['id', 'url', 'job_id']:
                    suggestions.append(f"Field '{field_name}' has high uniqueness ({uniqueness:.1%}) - consider adding unique constraint")
                
                if len(metrics['data_types']) > 1:
                    suggestions.append(f"Field '{field_name}' has mixed data types {metrics['data_types']} - consider data normalization")
            
            # Overall suggestions
            if analysis['overall_quality'] < 0.7:
                suggestions.append(f"Overall data quality is {analysis['overall_quality']:.1%} - consider improving extraction strategies")
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Failed to generate suggestions for {table_name}: {e}")
            return [f"Error generating suggestions: {e}"]
    
    def get_purpose_schema_template(self, purpose: str) -> Dict[str, str]:
        """
        Get a schema template for common extraction purposes
        
        Args:
            purpose: Extraction purpose
            
        Returns:
            Dictionary with recommended field names and types
        """
        
        templates = {
            'company_info': {
                'company_name': 'VARCHAR(200)',
                'description': 'TEXT',
                'industry': 'VARCHAR(100)',
                'website': 'VARCHAR(500)',
                'email': 'VARCHAR(320)',
                'phone': 'VARCHAR(50)',
                'address': 'VARCHAR(500)',
                'founded': 'VARCHAR(50)',
                'employees': 'VARCHAR(50)',
                'revenue': 'VARCHAR(100)'
            },
            'contact_discovery': {
                'emails': 'JSON',
                'phones': 'JSON', 
                'addresses': 'JSON',
                'social_links': 'JSON',
                'contact_forms': 'JSON',
                'key_personnel': 'JSON'
            },
            'product_data': {
                'product_name': 'VARCHAR(300)',
                'price': 'DECIMAL(10,2)',
                'description': 'TEXT',
                'brand': 'VARCHAR(100)',
                'category': 'VARCHAR(100)',
                'rating': 'REAL',
                'availability': 'VARCHAR(50)',
                'image_url': 'VARCHAR(1000)',
                'sku': 'VARCHAR(100)'
            },
            'news_content': {
                'headline': 'VARCHAR(500)',
                'content': 'TEXT',
                'author': 'VARCHAR(200)',
                'publish_date': 'DATETIME',
                'category': 'VARCHAR(100)',
                'tags': 'JSON',
                'summary': 'TEXT',
                'source': 'VARCHAR(200)'
            },
            'profile_info': {
                'name': 'VARCHAR(200)',
                'title': 'VARCHAR(200)',
                'company': 'VARCHAR(200)',
                'location': 'VARCHAR(200)',
                'bio': 'TEXT',
                'experience': 'JSON',
                'education': 'JSON',
                'skills': 'JSON',
                'connections': 'VARCHAR(50)'
            }
        }
        
        return templates.get(purpose, {})

# Helper functions
def normalize_extracted_data(data: Dict[str, Any], purpose: str = None) -> Dict[str, Any]:
    """
    Normalize extracted data for consistent storage
    
    Args:
        data: Raw extracted data
        purpose: Extraction purpose for context
        
    Returns:
        Normalized data dictionary
    """
    
    if not isinstance(data, dict):
        return {'raw_content': str(data)}
    
    normalized = {}
    
    for key, value in data.items():
        # Normalize key name
        normalized_key = re.sub(r'[^a-zA-Z0-9_]', '_', str(key).lower())
        
        # Normalize value
        if value is None:
            normalized[normalized_key] = None
        elif isinstance(value, (list, dict)):
            normalized[normalized_key] = value
        else:
            # Clean string values
            str_value = str(value).strip()
            
            # Detect and clean common patterns
            if '@' in str_value and '.' in str_value:
                # Possible email
                str_value = str_value.lower()
            elif str_value.startswith(('http://', 'https://')):
                # URL - normalize
                str_value = str_value.lower()
            elif any(char in str_value for char in ['(', ')', '-', '+']):
                # Possible phone number - keep as is but clean
                str_value = re.sub(r'\s+', ' ', str_value)
            
            normalized[normalized_key] = str_value if str_value else None
    
    return normalized

if __name__ == "__main__":
    # Example usage
    sample_data = [
        {
            'company_name': 'Acme Corp',
            'email': 'contact@acme.com',
            'phone': '+1-555-123-4567',
            'website': 'https://acme.com',
            'rating': '4.5/5'
        },
        {
            'company_name': 'Tech Solutions Inc',
            'email': 'info@techsolutions.com',
            'phone': '(555) 987-6543',
            'website': 'https://techsolutions.com',
            'rating': '4.8'
        }
    ]
    
    schema_manager = SchemaManager(None)  # Mock db_manager for testing
    
    # Test data type detection
    for record in sample_data:
        for field, value in record.items():
            detected_type = schema_manager.detect_data_type(field, value, 'company_info')
            print(f"{field}: {value} -> {detected_type}")
