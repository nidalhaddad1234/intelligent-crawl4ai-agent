# AI-Discoverable Tools Documentation

## Overview

In the AI-first architecture, all capabilities are implemented as self-discovering tools. The AI planner automatically finds and uses these tools based on your natural language requests.

## Core Concept

### Traditional Approach (Removed)
```python
# Old way - hardcoded strategies
if website_type == "directory":
    strategy = DirectoryCSSStrategy()
elif website_type == "ecommerce":
    strategy = EcommerceCSSStrategy()
```

### AI-First Approach (Current)
```python
# New way - AI discovers and uses tools
@ai_tool(name="extract_business_data")
async def extract_business_data(url: str):
    # Tool implementation
    pass

# AI automatically finds and uses this tool when needed
```

## Available Tools

### 1. CrawlTool
**Purpose**: Web scraping and content extraction  
**Location**: `ai_core/tools/crawler.py`

**Key Functions**:
- `crawl_webpage(url)` - Basic page fetching
- `extract_content(urls, extraction_type)` - Smart content extraction
- `extract_structured_data(url, schema)` - Schema-based extraction
- `handle_dynamic_content(url, wait_for)` - JavaScript rendering

**AI Usage Examples**:
```
"Extract data from this website"
"Scrape product information from these URLs"
"Get content from this JavaScript-heavy site"
```

### 2. DatabaseTool
**Purpose**: Data storage and retrieval  
**Location**: `ai_core/tools/database.py`

**Key Functions**:
- `store_data(table_name, data)` - Auto-schema storage
- `query_data(table_name, filters)` - Flexible queries
- `aggregate_data(table_name, aggregations)` - Analytics

**AI Usage Examples**:
```
"Save this data for later"
"Show me all products under $50"
"What's the average price by category?"
```

### 3. AnalyzerTool
**Purpose**: Data analysis and pattern recognition  
**Location**: `ai_core/tools/analyzer.py`

**Key Functions**:
- `analyze_website(url)` - Website structure analysis
- `extract_patterns(data, pattern_type)` - Pattern finding
- `compare_data(dataset1, dataset2)` - Comparisons
- `detect_changes(old_data, new_data)` - Change detection

**AI Usage Examples**:
```
"Analyze this website's structure"
"Find patterns in the pricing data"
"Compare these two datasets"
```

### 4. ExporterTool
**Purpose**: Export data in various formats  
**Location**: `ai_core/tools/exporter.py`

**Key Functions**:
- `export_csv(data, filename)` - CSV export
- `export_json(data, filename)` - JSON export
- `export_excel(data, filename)` - Excel with formatting
- `export_xml(data, filename)` - XML export
- `export_html(data, filename)` - HTML tables

**AI Usage Examples**:
```
"Export this as CSV"
"Create an Excel report with charts"
"Generate an HTML table"
```

### 5. ExtractorTool
**Purpose**: Advanced content extraction  
**Location**: `ai_core/tools/extractor.py`

**Key Functions**:
- `extract_contact_info(html)` - Email, phone extraction
- `extract_social_links(html)` - Social media links
- `extract_business_hours(html)` - Operating hours
- `extract_addresses(html)` - Physical addresses

**AI Usage Examples**:
```
"Find all contact information"
"Extract social media links"
"Get business hours"
```

### 6. WebSearchTool
**Purpose**: Semantic search capabilities  
**Location**: `ai_core/tools/websearch.py`

**Key Functions**:
- `search_extracted_data(query)` - Search stored data
- `find_similar(content)` - Similarity search
- `semantic_filter(data, criteria)` - Smart filtering

**AI Usage Examples**:
```
"Find similar products"
"Search for restaurants with parking"
"Filter by semantic criteria"
```

## Creating New Tools

### Basic Tool Structure
```python
from ai_core.registry import ai_tool, create_example

@ai_tool(
    name="tool_name",
    description="What this tool does",
    category="category_name",
    examples=[
        create_example(
            "Example description",
            param1="value1",
            param2="value2"
        )
    ],
    capabilities=[
        "List of things this tool can do",
        "Another capability"
    ],
    performance={
        "speed": "high|medium|low",
        "reliability": "high|medium|low",
        "cost": "high|medium|low"
    }
)
async def tool_function(param1: str, param2: int = 10):
    """
    Tool implementation
    
    Args:
        param1: Description
        param2: Description with default
        
    Returns:
        Dict with results
    """
    try:
        # Tool logic here
        result = do_something(param1, param2)
        
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
```

### Best Practices

1. **Single Responsibility**: Each tool should do one thing well
2. **Clear Descriptions**: Help AI understand when to use the tool
3. **Good Examples**: Provide realistic usage examples
4. **Error Handling**: Always return success/error status
5. **Type Hints**: Use proper type annotations
6. **Async First**: Make tools async for better performance

### Advanced Tool Features

#### Dynamic Parameters
```python
@ai_tool(name="flexible_extractor")
async def flexible_extractor(url: str, **kwargs):
    """Tool that accepts dynamic parameters from AI"""
    fields = kwargs.get('fields', [])
    format = kwargs.get('format', 'json')
    # AI can pass any parameters it thinks necessary
```

#### Tool Composition
```python
@ai_tool(name="analyze_and_export")
async def analyze_and_export(urls: List[str]):
    """Tool that uses other tools internally"""
    # Get other tools
    crawler = tool_registry.get_tool('crawler')
    analyzer = tool_registry.get_tool('analyzer')
    exporter = tool_registry.get_tool('exporter')
    
    # Compose functionality
    data = await crawler['functions']['extract_content'](urls)
    analysis = await analyzer['functions']['analyze_data'](data)
    result = await exporter['functions']['export_excel'](analysis)
    
    return result
```

#### Performance Hints
```python
@ai_tool(
    name="batch_processor",
    performance_hints={
        "batch_size": 100,
        "parallelism": True,
        "cache_friendly": True
    }
)
async def batch_processor(items: List[Any]):
    """Tool with performance hints for AI optimizer"""
    # Process in batches as suggested
```

## Tool Discovery

### How AI Discovers Tools

1. **Registration**: Tools register on import
2. **Manifest**: AI reads tool descriptions and examples
3. **Matching**: AI matches user intent to tool capabilities
4. **Planning**: AI creates execution plan using tools
5. **Execution**: Tools are called with AI-determined parameters

### Tool Manifest
View all registered tools:
```python
from ai_core.registry import tool_registry

tools = tool_registry.list_tools()
for tool_name in tools:
    info = tool_registry.get_tool(tool_name)
    print(f"{tool_name}: {info['description']}")
```

## Tool Enhancement System

### Phase 6 Enhancements

1. **DynamicParameterDiscovery**
   - AI suggests parameters based on context
   - Learns optimal parameters from usage

2. **ToolCombinationEngine**
   - Finds optimal tool execution order
   - Identifies reusable patterns

3. **PerformanceProfiler**
   - Tracks execution times
   - Monitors success rates
   - Identifies bottlenecks

4. **CapabilityMatcher**
   - Semantic understanding of tool capabilities
   - Suggests alternative tools
   - Identifies capability gaps

5. **ToolRecommendationEngine**
   - Suggests new tools to implement
   - Based on failed requests
   - Learns from user needs

## Debugging Tools

### Tool Execution Logs
```python
# Enable detailed logging
import logging
logging.getLogger("ai_core.tools").setLevel(logging.DEBUG)
```

### Tool Performance Metrics
```bash
GET /api/tools/insights

# Returns:
{
    "crawler": {
        "calls": 1523,
        "avg_time": 2.3,
        "success_rate": 0.96
    }
}
```

### Tool Testing
```python
# Test a tool directly
from ai_core.tools import crawler

result = await crawler.crawl_webpage("https://example.com")
print(result)
```

## Common Patterns

### 1. Data Pipeline
```
User: "Scrape these sites, analyze trends, and export a report"

AI Plan:
1. crawler.extract_content() → get data
2. database.store_data() → save raw data  
3. analyzer.find_patterns() → analyze
4. exporter.export_excel() → create report
```

### 2. Monitoring
```
User: "Check this site daily for price changes"

AI Plan:
1. crawler.extract_content() → get current prices
2. database.query_data() → get yesterday's prices
3. analyzer.detect_changes() → find differences
4. exporter.export_json() → save changes
```

### 3. Bulk Operations
```
User: "Process 1000 URLs and find contact information"

AI Plan:
1. crawler.batch_crawl() → fetch pages in parallel
2. extractor.extract_contact_info() → find contacts
3. database.store_data() → save results
4. analyzer.summarize() → create summary
```

## Contributing New Tools

1. **Identify Need**: Look at failed requests or suggestions
2. **Design Tool**: Single purpose, clear interface
3. **Implement**: Follow the template above
4. **Test**: Unit tests and integration tests
5. **Document**: Add examples and capabilities
6. **Submit**: Create PR with your new tool

## Tool Roadmap

### Implemented ✅
- Web scraping (crawler)
- Data storage (database)
- Analysis (analyzer)
- Export formats (exporter)
- Content extraction (extractor)
- Search (websearch)

### Planned 🚧
- Scheduler (recurring tasks)
- Notification (alerts)
- Transform (data manipulation)
- Validate (data quality)
- Monitor (change detection)
- Aggregate (data combination)

### Community Requested 💡
- PDF extraction
- Image analysis
- Translation
- Authentication handler
- API integration
- Cloud storage

## Summary

The AI-discoverable tools system replaces hundreds of hardcoded strategies with a flexible, extensible architecture. Tools are:

- **Self-describing**: AI understands their purpose
- **Composable**: Can be combined in any order
- **Learning**: Improve through usage
- **Simple**: Easy to create and maintain

This approach means adding new capabilities is as simple as writing a new function with the `@ai_tool` decorator!
