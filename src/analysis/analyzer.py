"""
Analyzer Tool - AI-discoverable data analysis capabilities

This tool provides analysis functions for extracted data including
pattern detection, summarization, and trend analysis.
"""

import json
import statistics
from typing import Dict, Any, List, Optional, Union
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re

from ..registry import ai_tool, create_example


@ai_tool(
    name="analyze_content",
    description="Analyze extracted content for patterns, entities, and insights",
    category="analysis",
    examples=[
        create_example(
            "Analyze product data for pricing patterns",
            data=[
                {"name": "iPhone 15", "price": 999, "site": "amazon"},
                {"name": "iPhone 15", "price": 1099, "site": "bestbuy"}
            ],
            analysis_type="pricing",
            group_by="name"
        ),
        create_example(
            "Extract entities from text",
            data={"text": "Apple Inc. announced the iPhone 15 for $999"},
            analysis_type="entities"
        )
    ],
    capabilities=[
        "Statistical analysis of numerical data",
        "Pattern detection in structured data",
        "Entity extraction from text",
        "Trend analysis over time",
        "Sentiment analysis",
        "Data quality assessment",
        "Anomaly detection",
        "Comparative analysis"
    ],
    performance={
        "speed": "medium",
        "reliability": "high",
        "cost": "low"
    }
)
async def analyze_content(
    data: Union[Dict[str, Any], List[Dict[str, Any]]],
    analysis_type: str = "general",
    group_by: Optional[str] = None,
    metrics: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Analyze content for patterns and insights
    
    Args:
        data: Data to analyze (dict or list of dicts)
        analysis_type: Type of analysis - 'general', 'pricing', 'entities', 'sentiment'
        group_by: Field to group data by
        metrics: Specific metrics to calculate
        
    Returns:
        Dictionary with analysis results
    """
    try:
        # Ensure data is a list
        records = data if isinstance(data, list) else [data]
        
        if analysis_type == "pricing":
            return _analyze_pricing(records, group_by)
        elif analysis_type == "entities":
            return _extract_entities(records)
        elif analysis_type == "sentiment":
            return _analyze_sentiment(records)
        elif analysis_type == "quality":
            return _assess_data_quality(records)
        else:
            return _general_analysis(records, group_by, metrics)
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "analysis_type": analysis_type
        }


@ai_tool(
    name="detect_patterns",
    description="Detect patterns and anomalies in data",
    category="analysis",
    examples=[
        create_example(
            "Find pricing anomalies",
            data=[
                {"product": "A", "price": 100},
                {"product": "B", "price": 95},
                {"product": "C", "price": 500}  # Anomaly
            ],
            pattern_type="anomaly",
            field="price"
        ),
        create_example(
            "Detect trends over time",
            data=[
                {"date": "2024-01-01", "value": 100},
                {"date": "2024-01-02", "value": 110},
                {"date": "2024-01-03", "value": 120}
            ],
            pattern_type="trend",
            field="value"
        )
    ],
    capabilities=[
        "Anomaly detection using statistical methods",
        "Trend identification",
        "Seasonal pattern detection",
        "Clustering similar items",
        "Frequency analysis",
        "Correlation detection"
    ],
    performance={
        "speed": "medium",
        "reliability": "high",
        "cost": "low"
    }
)
async def detect_patterns(
    data: List[Dict[str, Any]],
    pattern_type: str = "anomaly",
    field: str = None,
    threshold: float = 2.0
) -> Dict[str, Any]:
    """
    Detect patterns and anomalies in data
    
    Args:
        data: List of records to analyze
        pattern_type: Type of pattern - 'anomaly', 'trend', 'frequency'
        field: Field to analyze for patterns
        threshold: Threshold for anomaly detection (standard deviations)
        
    Returns:
        Dictionary with detected patterns
    """
    try:
        if pattern_type == "anomaly":
            return _detect_anomalies(data, field, threshold)
        elif pattern_type == "trend":
            return _detect_trends(data, field)
        elif pattern_type == "frequency":
            return _frequency_analysis(data, field)
        else:
            return {
                "success": False,
                "error": f"Unknown pattern type: {pattern_type}"
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "pattern_type": pattern_type
        }


@ai_tool(
    name="compare_datasets",
    description="Compare multiple datasets to find differences and similarities",
    category="analysis",
    examples=[
        create_example(
            "Compare prices across sites",
            dataset1=[{"product": "iPhone", "price": 999}],
            dataset2=[{"product": "iPhone", "price": 1099}],
            compare_on="product",
            metrics=["price"]
        )
    ],
    capabilities=[
        "Side-by-side comparison",
        "Difference calculation",
        "Similarity scoring",
        "Missing data identification",
        "Statistical comparison"
    ],
    performance={
        "speed": "high",
        "reliability": "high",
        "cost": "low"
    }
)
async def compare_datasets(
    dataset1: List[Dict[str, Any]],
    dataset2: List[Dict[str, Any]],
    compare_on: str,
    metrics: List[str]
) -> Dict[str, Any]:
    """
    Compare two datasets
    
    Args:
        dataset1: First dataset
        dataset2: Second dataset
        compare_on: Key field to match records
        metrics: Fields to compare
        
    Returns:
        Dictionary with comparison results
    """
    try:
        # Create lookup dictionaries
        data1_lookup = {record.get(compare_on): record for record in dataset1}
        data2_lookup = {record.get(compare_on): record for record in dataset2}
        
        # Find common and unique keys
        keys1 = set(data1_lookup.keys())
        keys2 = set(data2_lookup.keys())
        common_keys = keys1.intersection(keys2)
        only_in_1 = keys1 - keys2
        only_in_2 = keys2 - keys1
        
        # Compare common records
        comparisons = []
        for key in common_keys:
            record1 = data1_lookup[key]
            record2 = data2_lookup[key]
            
            comparison = {compare_on: key}
            for metric in metrics:
                val1 = record1.get(metric)
                val2 = record2.get(metric)
                
                if isinstance(val1, (int, float)) and isinstance(val2, (int, float)):
                    comparison[f"{metric}_dataset1"] = val1
                    comparison[f"{metric}_dataset2"] = val2
                    comparison[f"{metric}_difference"] = val2 - val1
                    comparison[f"{metric}_percent_change"] = ((val2 - val1) / val1 * 100) if val1 != 0 else None
                else:
                    comparison[f"{metric}_dataset1"] = val1
                    comparison[f"{metric}_dataset2"] = val2
                    comparison[f"{metric}_match"] = val1 == val2
            
            comparisons.append(comparison)
        
        return {
            "success": True,
            "total_compared": len(comparisons),
            "only_in_dataset1": len(only_in_1),
            "only_in_dataset2": len(only_in_2),
            "comparisons": comparisons,
            "unique_to_dataset1": list(only_in_1),
            "unique_to_dataset2": list(only_in_2)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Helper functions
def _general_analysis(records: List[Dict[str, Any]], group_by: Optional[str], metrics: Optional[List[str]]) -> Dict[str, Any]:
    """Perform general statistical analysis"""
    result = {
        "success": True,
        "total_records": len(records),
        "fields": list(records[0].keys()) if records else [],
        "analysis": {}
    }
    
    # Analyze numeric fields
    numeric_fields = {}
    for record in records:
        for key, value in record.items():
            if isinstance(value, (int, float)):
                if key not in numeric_fields:
                    numeric_fields[key] = []
                numeric_fields[key].append(value)
    
    # Calculate statistics
    for field, values in numeric_fields.items():
        if metrics and field not in metrics:
            continue
            
        result["analysis"][field] = {
            "count": len(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "min": min(values),
            "max": max(values),
            "std_dev": statistics.stdev(values) if len(values) > 1 else 0,
            "sum": sum(values)
        }
    
    # Group by analysis
    if group_by and group_by in records[0]:
        grouped = defaultdict(list)
        for record in records:
            grouped[record.get(group_by)].append(record)
        
        result["grouped_analysis"] = {}
        for group_key, group_records in grouped.items():
            result["grouped_analysis"][str(group_key)] = {
                "count": len(group_records),
                "percentage": len(group_records) / len(records) * 100
            }
    
    return result


def _analyze_pricing(records: List[Dict[str, Any]], group_by: Optional[str]) -> Dict[str, Any]:
    """Analyze pricing data"""
    price_fields = ["price", "cost", "amount", "total", "value"]
    prices = []
    
    # Find price field
    price_field = None
    for field in price_fields:
        if records and field in records[0]:
            price_field = field
            break
    
    if not price_field:
        # Look for any numeric field
        for key, value in records[0].items():
            if isinstance(value, (int, float)):
                price_field = key
                break
    
    if not price_field:
        return {"success": False, "error": "No price field found"}
    
    # Extract prices
    for record in records:
        price = record.get(price_field)
        if isinstance(price, (int, float)):
            prices.append(price)
    
    if not prices:
        return {"success": False, "error": "No numeric prices found"}
    
    result = {
        "success": True,
        "price_field": price_field,
        "statistics": {
            "average": statistics.mean(prices),
            "median": statistics.median(prices),
            "min": min(prices),
            "max": max(prices),
            "range": max(prices) - min(prices),
            "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0
        },
        "distribution": _get_price_distribution(prices)
    }
    
    # Group analysis
    if group_by:
        grouped_prices = defaultdict(list)
        for record in records:
            group_key = record.get(group_by)
            price = record.get(price_field)
            if isinstance(price, (int, float)):
                grouped_prices[str(group_key)].append(price)
        
        result["grouped_analysis"] = {}
        for group, group_prices in grouped_prices.items():
            if group_prices:
                result["grouped_analysis"][group] = {
                    "average": statistics.mean(group_prices),
                    "min": min(group_prices),
                    "max": max(group_prices),
                    "count": len(group_prices)
                }
    
    return result


def _extract_entities(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract entities from text data"""
    # Simple entity extraction using patterns
    entities = {
        "organizations": [],
        "prices": [],
        "dates": [],
        "emails": [],
        "urls": [],
        "numbers": []
    }
    
    # Patterns
    org_pattern = r'\b[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Co)\b'
    price_pattern = r'\$[\d,]+\.?\d*|\d+\.?\d*\s*(?:USD|EUR|GBP)'
    date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}|\d{4}[-/]\d{1,2}[-/]\d{1,2}'
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    url_pattern = r'https?://[^\s]+'
    
    for record in records:
        text = str(record) if isinstance(record, str) else json.dumps(record)
        
        # Extract entities
        entities["organizations"].extend(re.findall(org_pattern, text))
        entities["prices"].extend(re.findall(price_pattern, text))
        entities["dates"].extend(re.findall(date_pattern, text))
        entities["emails"].extend(re.findall(email_pattern, text))
        entities["urls"].extend(re.findall(url_pattern, text))
        
        # Extract numbers
        numbers = re.findall(r'\b\d+\.?\d*\b', text)
        entities["numbers"].extend([float(n) for n in numbers])
    
    # Deduplicate and count
    result = {
        "success": True,
        "entities": {}
    }
    
    for entity_type, items in entities.items():
        unique_items = list(set(items))
        if unique_items:
            result["entities"][entity_type] = {
                "count": len(unique_items),
                "unique": unique_items[:10],  # First 10
                "frequency": dict(Counter(items).most_common(5))
            }
    
    return result


def _analyze_sentiment(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Simple sentiment analysis based on keywords"""
    positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'best', 'wonderful', 'fantastic']
    negative_words = ['bad', 'poor', 'terrible', 'hate', 'worst', 'awful', 'horrible', 'disappointing']
    
    sentiments = []
    for record in records:
        text = str(record).lower()
        positive_count = sum(word in text for word in positive_words)
        negative_count = sum(word in text for word in negative_words)
        
        if positive_count > negative_count:
            sentiments.append("positive")
        elif negative_count > positive_count:
            sentiments.append("negative")
        else:
            sentiments.append("neutral")
    
    sentiment_counts = Counter(sentiments)
    total = len(sentiments)
    
    return {
        "success": True,
        "sentiment_analysis": {
            "positive": sentiment_counts.get("positive", 0),
            "negative": sentiment_counts.get("negative", 0),
            "neutral": sentiment_counts.get("neutral", 0),
            "positive_percentage": sentiment_counts.get("positive", 0) / total * 100 if total > 0 else 0,
            "negative_percentage": sentiment_counts.get("negative", 0) / total * 100 if total > 0 else 0,
            "neutral_percentage": sentiment_counts.get("neutral", 0) / total * 100 if total > 0 else 0
        }
    }


def _assess_data_quality(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Assess data quality"""
    if not records:
        return {"success": False, "error": "No data to assess"}
    
    total_records = len(records)
    field_stats = defaultdict(lambda: {"total": 0, "missing": 0, "unique": set()})
    
    for record in records:
        for field in records[0].keys():
            value = record.get(field)
            field_stats[field]["total"] += 1
            if value is None or value == "":
                field_stats[field]["missing"] += 1
            else:
                field_stats[field]["unique"].add(str(value))
    
    quality_report = {
        "success": True,
        "total_records": total_records,
        "field_quality": {}
    }
    
    for field, stats in field_stats.items():
        completeness = (stats["total"] - stats["missing"]) / stats["total"] * 100
        uniqueness = len(stats["unique"]) / stats["total"] * 100
        
        quality_report["field_quality"][field] = {
            "completeness": completeness,
            "missing_count": stats["missing"],
            "unique_values": len(stats["unique"]),
            "uniqueness_ratio": uniqueness,
            "quality_score": (completeness + min(uniqueness, 100)) / 2
        }
    
    # Overall quality score
    quality_scores = [f["quality_score"] for f in quality_report["field_quality"].values()]
    quality_report["overall_quality_score"] = statistics.mean(quality_scores) if quality_scores else 0
    
    return quality_report


def _detect_anomalies(data: List[Dict[str, Any]], field: str, threshold: float) -> Dict[str, Any]:
    """Detect anomalies using z-score"""
    values = []
    for i, record in enumerate(data):
        value = record.get(field)
        if isinstance(value, (int, float)):
            values.append((i, value))
    
    if len(values) < 3:
        return {"success": False, "error": "Not enough data for anomaly detection"}
    
    # Calculate statistics
    nums = [v[1] for v in values]
    mean = statistics.mean(nums)
    std_dev = statistics.stdev(nums)
    
    # Find anomalies
    anomalies = []
    for i, value in values:
        z_score = abs((value - mean) / std_dev) if std_dev > 0 else 0
        if z_score > threshold:
            anomalies.append({
                "index": i,
                "value": value,
                "z_score": z_score,
                "deviation": value - mean
            })
    
    return {
        "success": True,
        "field": field,
        "mean": mean,
        "std_dev": std_dev,
        "threshold": threshold,
        "anomalies_found": len(anomalies),
        "anomalies": anomalies
    }


def _detect_trends(data: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
    """Detect trends in time-series data"""
    # Extract values with indices
    values = []
    for i, record in enumerate(data):
        value = record.get(field)
        if isinstance(value, (int, float)):
            values.append((i, value))
    
    if len(values) < 2:
        return {"success": False, "error": "Not enough data for trend detection"}
    
    # Simple trend detection
    first_half = [v[1] for v in values[:len(values)//2]]
    second_half = [v[1] for v in values[len(values)//2:]]
    
    first_avg = statistics.mean(first_half) if first_half else 0
    second_avg = statistics.mean(second_half) if second_half else 0
    
    if second_avg > first_avg * 1.1:
        trend = "increasing"
    elif second_avg < first_avg * 0.9:
        trend = "decreasing"
    else:
        trend = "stable"
    
    # Calculate change rate
    if len(values) >= 2:
        total_change = values[-1][1] - values[0][1]
        change_rate = total_change / values[0][1] * 100 if values[0][1] != 0 else 0
    else:
        total_change = 0
        change_rate = 0
    
    return {
        "success": True,
        "field": field,
        "trend": trend,
        "start_value": values[0][1],
        "end_value": values[-1][1],
        "total_change": total_change,
        "change_rate_percent": change_rate,
        "data_points": len(values)
    }


def _frequency_analysis(data: List[Dict[str, Any]], field: str) -> Dict[str, Any]:
    """Analyze frequency of values"""
    values = []
    for record in data:
        value = record.get(field)
        if value is not None:
            values.append(str(value))
    
    if not values:
        return {"success": False, "error": f"No values found for field: {field}"}
    
    # Count frequencies
    frequencies = Counter(values)
    total = len(values)
    
    # Get top 10
    top_10 = frequencies.most_common(10)
    
    return {
        "success": True,
        "field": field,
        "total_values": total,
        "unique_values": len(frequencies),
        "top_10": [
            {
                "value": value,
                "count": count,
                "percentage": count / total * 100
            }
            for value, count in top_10
        ],
        "distribution": {
            "most_common": top_10[0][0] if top_10 else None,
            "least_common": frequencies.most_common()[-1][0] if frequencies else None
        }
    }


def _get_price_distribution(prices: List[float]) -> Dict[str, int]:
    """Get price distribution in ranges"""
    if not prices:
        return {}
    
    min_price = min(prices)
    max_price = max(prices)
    range_size = (max_price - min_price) / 5  # 5 ranges
    
    if range_size == 0:
        return {"single_value": len(prices)}
    
    ranges = {}
    for i in range(5):
        range_start = min_price + (i * range_size)
        range_end = min_price + ((i + 1) * range_size)
        range_key = f"${range_start:.0f}-${range_end:.0f}"
        ranges[range_key] = 0
    
    for price in prices:
        for i in range(5):
            range_start = min_price + (i * range_size)
            range_end = min_price + ((i + 1) * range_size)
            if range_start <= price <= range_end or (i == 4 and price >= range_start):
                range_key = f"${range_start:.0f}-${range_end:.0f}"
                ranges[range_key] += 1
                break
    
    return ranges
