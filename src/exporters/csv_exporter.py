#!/usr/bin/env python3
"""
CSV Exporter
Export scraped data to CSV format with advanced options
"""

import csv
import logging
from typing import Dict, Any, List, Optional, Union, IO
from datetime import datetime
import json
import os

logger = logging.getLogger("csv_exporter")

class CSVExporter:
    """Exports scraped data to CSV format with normalization and flattening"""
    
    def __init__(self, flatten_json: bool = True, max_text_length: int = 32767):
        self.flatten_json = flatten_json
        self.max_text_length = max_text_length  # Excel cell limit
        
    def export_job_data(self, job_data: List[Dict[str, Any]], 
                       output_path: str, include_metadata: bool = True) -> Dict[str, Any]:
        """
        Export job extraction data to CSV
        
        Args:
            job_data: List of extraction records
            output_path: Path to save CSV file
            include_metadata: Whether to include extraction metadata
            
        Returns:
            Export summary statistics
        """
        
        if not job_data:
            return {"success": False, "error": "No data to export"}
        
        try:
            # Prepare data for CSV export
            csv_data = self._prepare_csv_data(job_data, include_metadata)
            
            # Write to CSV
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if csv_data:
                    fieldnames = list(csv_data[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    writer.writerows(csv_data)
            
            # Generate summary
            summary = {
                "success": True,
                "output_path": output_path,
                "records_exported": len(csv_data),
                "columns_exported": len(csv_data[0].keys()) if csv_data else 0,
                "file_size_bytes": os.path.getsize(output_path),
                "exported_at": datetime.now().isoformat()
            }
            
            logger.info(f"Exported {len(csv_data)} records to {output_path}")
            return summary
            
        except Exception as e:
            logger.error(f"CSV export failed: {e}")
            return {"success": False, "error": str(e)}
    
    def export_analytics_report(self, analytics_data: Dict[str, Any], 
                               output_path: str) -> Dict[str, Any]:
        """Export analytics report to CSV format"""
        
        try:
            # Convert analytics data to CSV-friendly format
            csv_records = []
            
            # Export different sections of analytics
            for section_name, section_data in analytics_data.items():
                if isinstance(section_data, list):
                    # List of dictionaries (like strategy performance)
                    for record in section_data:
                        csv_record = {
                            "section": section_name,
                            **self._flatten_dict(record)
                        }
                        csv_records.append(csv_record)
                        
                elif isinstance(section_data, dict):
                    # Single dictionary (like overview metrics)
                    csv_record = {
                        "section": section_name,
                        **self._flatten_dict(section_data)
                    }
                    csv_records.append(csv_record)
            
            # Write to CSV
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if csv_records:
                    fieldnames = list(csv_records[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    writer.writerows(csv_records)
            
            return {
                "success": True,
                "output_path": output_path,
                "records_exported": len(csv_records),
                "exported_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Analytics CSV export failed: {e}")
            return {"success": False, "error": str(e)}
    
    def export_to_string(self, data: List[Dict[str, Any]], 
                        include_metadata: bool = True) -> str:
        """Export data to CSV string"""
        
        try:
            from io import StringIO
            
            csv_data = self._prepare_csv_data(data, include_metadata)
            
            if not csv_data:
                return ""
            
            output = StringIO()
            fieldnames = list(csv_data[0].keys())
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(csv_data)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"CSV string export failed: {e}")
            return ""
    
    def _prepare_csv_data(self, job_data: List[Dict[str, Any]], 
                         include_metadata: bool) -> List[Dict[str, Any]]:
        """Prepare data for CSV export with flattening and normalization"""
        
        csv_records = []
        
        for record in job_data:
            csv_record = {}
            
            # Core fields
            csv_record['url'] = record.get('url', '')
            csv_record['job_id'] = record.get('job_id', '')
            csv_record['purpose'] = record.get('purpose', '')
            csv_record['success'] = record.get('success', False)
            csv_record['extracted_at'] = record.get('extracted_at', '')
            
            # Extract and flatten main data
            raw_data = record.get('raw_data', {})
            normalized_data = record.get('normalized_data', {})
            
            # Use normalized data if available, otherwise raw data
            main_data = normalized_data if normalized_data else raw_data
            
            if self.flatten_json and isinstance(main_data, dict):
                flattened_data = self._flatten_dict(main_data)
                csv_record.update(flattened_data)
            elif isinstance(main_data, dict):
                # Convert complex objects to JSON strings
                for key, value in main_data.items():
                    if isinstance(value, (dict, list)):
                        csv_record[key] = json.dumps(value)
                    else:
                        csv_record[key] = str(value) if value is not None else ''
            
            # Include metadata if requested
            if include_metadata:
                csv_record['confidence_score'] = record.get('confidence_score', 0)
                csv_record['data_quality_score'] = record.get('data_quality_score', 0)
                csv_record['field_count'] = record.get('field_count', 0)
                csv_record['extraction_time'] = record.get('extraction_time', 0)
                csv_record['strategy_used'] = record.get('strategy_used', '')
                csv_record['website_type'] = record.get('website_type', '')
                csv_record['domain'] = record.get('domain', '')
                
                if record.get('error_message'):
                    csv_record['error_message'] = str(record['error_message'])
            
            # Clean up the record
            csv_record = self._clean_csv_record(csv_record)
            csv_records.append(csv_record)
        
        return csv_records
    
    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = '', 
                     separator: str = '_') -> Dict[str, Any]:
        """Flatten nested dictionary for CSV export"""
        
        items = []
        
        for key, value in data.items():
            new_key = f"{parent_key}{separator}{key}" if parent_key else key
            
            if isinstance(value, dict):
                # Recursively flatten nested dictionaries
                items.extend(self._flatten_dict(value, new_key, separator).items())
            elif isinstance(value, list):
                # Handle lists
                if value and isinstance(value[0], dict):
                    # List of dictionaries - flatten first item and indicate list
                    items.extend(self._flatten_dict(value[0], f"{new_key}_0", separator).items())
                    items.append((f"{new_key}_count", len(value)))
                    if len(value) > 1:
                        items.append((f"{new_key}_additional", json.dumps(value[1:])))
                else:
                    # Simple list - join as string
                    items.append((new_key, ', '.join(str(v) for v in value) if value else ''))
            else:
                items.append((new_key, value))
        
        return dict(items)
    
    def _clean_csv_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """Clean CSV record for Excel compatibility"""
        
        cleaned = {}
        
        for key, value in record.items():
            # Clean key name
            clean_key = str(key).replace('\n', ' ').replace('\r', ' ').strip()
            
            # Clean value
            if value is None:
                clean_value = ''
            elif isinstance(value, str):
                # Truncate long text for Excel compatibility
                clean_value = value[:self.max_text_length] if len(value) > self.max_text_length else value
                # Remove problematic characters
                clean_value = clean_value.replace('\x00', '').replace('\r\n', ' ').replace('\n', ' ')
            elif isinstance(value, (int, float, bool)):
                clean_value = value
            else:
                # Convert other types to string
                clean_value = str(value)[:self.max_text_length]
            
            cleaned[clean_key] = clean_value
        
        return cleaned
    
    def create_summary_csv(self, job_data: List[Dict[str, Any]], 
                          output_path: str) -> Dict[str, Any]:
        """Create a summary CSV with key metrics per URL"""
        
        try:
            summary_records = []
            
            for record in job_data:
                summary_record = {
                    'url': record.get('url', ''),
                    'domain': record.get('domain', ''),
                    'purpose': record.get('purpose', ''),
                    'success': record.get('success', False),
                    'confidence_score': record.get('confidence_score', 0),
                    'data_quality_score': record.get('data_quality_score', 0),
                    'fields_extracted': record.get('field_count', 0),
                    'extraction_time_seconds': record.get('extraction_time', 0),
                    'strategy_used': record.get('strategy_used', ''),
                    'website_type': record.get('website_type', ''),
                    'extracted_at': record.get('extracted_at', ''),
                    'has_error': bool(record.get('error_message'))
                }
                
                # Add key extracted fields if available
                normalized_data = record.get('normalized_data', {})
                if normalized_data:
                    # Add most common fields
                    common_fields = ['company_name', 'title', 'email', 'phone', 'address', 'price']
                    for field in common_fields:
                        if field in normalized_data:
                            summary_record[f'extracted_{field}'] = str(normalized_data[field])[:100]
                
                summary_records.append(summary_record)
            
            # Write summary CSV
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if summary_records:
                    fieldnames = list(summary_records[0].keys())
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    writer.writerows(summary_records)
            
            return {
                "success": True,
                "output_path": output_path,
                "records_exported": len(summary_records),
                "exported_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Summary CSV export failed: {e}")
            return {"success": False, "error": str(e)}

# Convenience functions
def export_job_to_csv(job_data: List[Dict[str, Any]], output_path: str, 
                     flatten_json: bool = True, include_metadata: bool = True) -> Dict[str, Any]:
    """Quick function to export job data to CSV"""
    
    exporter = CSVExporter(flatten_json=flatten_json)
    return exporter.export_job_data(job_data, output_path, include_metadata)

def export_analytics_to_csv(analytics_data: Dict[str, Any], 
                           output_path: str) -> Dict[str, Any]:
    """Quick function to export analytics to CSV"""
    
    exporter = CSVExporter()
    return exporter.export_analytics_report(analytics_data, output_path)

if __name__ == "__main__":
    # Test the CSV exporter
    test_data = [
        {
            "url": "https://example.com",
            "job_id": "test_job_1",
            "purpose": "company_info",
            "success": True,
            "raw_data": {
                "company_name": "Test Corp",
                "email": "contact@test.com",
                "phones": ["+1-555-123-4567", "+1-555-987-6543"],
                "address": {
                    "street": "123 Main St",
                    "city": "Anytown",
                    "state": "CA"
                }
            },
            "normalized_data": {
                "company_name": "Test Corp",
                "email": "contact@test.com",
                "phone": "+1-555-123-4567",
                "street_address": "123 Main St, Anytown, CA"
            },
            "confidence_score": 0.95,
            "data_quality_score": 0.88,
            "field_count": 4,
            "extraction_time": 2.3,
            "strategy_used": "DirectoryCSSStrategy",
            "extracted_at": "2024-01-01T12:00:00"
        }
    ]
    
    # Test export
    result = export_job_to_csv(test_data, "./test_export.csv")
    print("Export result:", result)
    
    # Test string export
    exporter = CSVExporter()
    csv_string = exporter.export_to_string(test_data)
    print("CSV String preview:")
    print(csv_string[:500])
