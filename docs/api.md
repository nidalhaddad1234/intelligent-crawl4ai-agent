# API Reference

## MCP Tools Available in Claude Desktop

The Intelligent Crawl4AI Agent provides several tools through the Model Context Protocol (MCP) that can be used directly from Claude Desktop.

### Core Tools

#### `analyze_and_scrape`

Analyze websites and execute intelligent scraping with optimal strategy selection.

**Parameters:**
- `urls` (array of strings, required): List of URLs to scrape
- `purpose` (string, required): Type of data to extract
  - `"company_info"`: Business information, contact details
  - `"contact_discovery"`: Email addresses, phone numbers, social links  
  - `"product_data"`: Product information, pricing, descriptions
  - `"profile_info"`: Professional profiles, bios
  - `"news_content"`: Articles, headlines, content
  - `"general_data"`: Generic data extraction
- `execution_mode` (string, optional): Processing mode
  - `"intelligent_single"`: Real-time processing (default)
  - `"high_volume"`: Batch processing for large URL lists
  - `"authenticated"`: Handle login/authentication
- `credentials` (object, optional): Login credentials for authenticated sites
  - `username` (string): Username or email
  - `password` (string): Password
  - `two_factor_code` (string): 2FA code if required
- `additional_context` (string, optional): Extra context about extraction goals

**Example Usage:**
```
Analyze and scrape these business directory URLs for company information:
- https://www.yellowpages.com/new-york-ny/restaurants
- https://www.yelp.com/chicago-il/dentists

Focus on extracting business names, addresses, phone numbers, and websites.
```

**Response Format:**
```json
{
  "execution_mode": "intelligent_single",
  "total_urls": 2,
  "processed_urls": 2,
  "successful_extractions": 2,
  "strategy_distribution": {
    "css_extraction": 2
  },
  "results": [
    {
      "success": true,
      "url": "https://example.com",
      "strategy_used": "css_extraction",
      "extracted_data": { ... },
      "confidence_score": 0.85
    }
  ]
}
```

#### `analyze_website_structure`

Analyze website structure and recommend optimal extraction strategy without performing extraction.

**Parameters:**
- `url` (string, required): URL to analyze
- `purpose` (string, required): Intended data extraction purpose

**Example Usage:**
```
Analyze the structure of https://www.linkedin.com/company/openai for extracting company information
```

**Response Format:**
```json
{
  "url": "https://example.com",
  "analysis": {
    "website_type": "social_media",
    "complexity": "high",
    "has_javascript": true,
    "detected_frameworks": ["React"],
    "anti_bot_measures": ["Cloudflare"]
  },
  "recommended_strategy": {
    "primary": "llm_extraction",
    "confidence": 0.75,
    "reasoning": "Social media requires AI understanding"
  }
}
```

#### `submit_high_volume_job`

Submit high-volume scraping job for processing thousands of URLs.

**Parameters:**
- `urls` (array of strings, required): Large list of URLs to process
- `purpose` (string, required): Extraction purpose
- `priority` (number, optional): Job priority (1-10, default: 1)
- `batch_size` (number, optional): URLs per batch (default: 100)
- `max_workers` (number, optional): Maximum concurrent workers (default: 50)

**Example Usage:**
```
Submit a high-volume job to scrape 5,000 restaurant listings from Yelp for business information with priority 5 and batch size 50
```

**Response Format:**
```json
{
  "job_id": "hvol_1703123456_abc12345",
  "status": "submitted",
  "urls_count": 5000,
  "estimated_batches": 100
}
```

#### `get_job_status`

Get comprehensive status and progress of high-volume scraping jobs.

**Parameters:**
- `job_id` (string, required): Job ID from submit_high_volume_job

**Example Usage:**
```
Check the status of job hvol_1703123456_abc12345
```

**Response Format:**
```json
{
  "job_id": "hvol_1703123456_abc12345",
  "status": "in_progress",
  "progress": {
    "total_urls": 5000,
    "processed_urls": 1247,
    "completion_percentage": 24.9
  },
  "performance": {
    "processing_rate": "156.3 URLs/minute",
    "estimated_completion": "2024-01-15T15:30:00Z"
  }
}
```

#### `query_extracted_data`

Query previously extracted data using semantic search.

**Parameters:**
- `query` (string, required): Search query in natural language
- `data_type` (string, optional): Filter by extraction purpose
- `limit` (number, optional): Maximum results (default: 10)

**Example Usage:**
```
Find restaurants in Manhattan with high ratings and delivery options from previously scraped data
```

**Response Format:**
```json
{
  "query": "restaurants in Manhattan with delivery",
  "results_count": 10,
  "results": [
    {
      "content": "Joe's Pizza - Manhattan, 4.8 stars, delivery available",
      "metadata": {
        "url": "https://example.com",
        "extraction_date": "2024-01-15"
      },
      "similarity": 0.92
    }
  ]
}
```

#### `get_system_stats`

Get real-time system performance and worker statistics.

**Parameters:** None

**Example Usage:**
```
Show me the current system performance and worker status
```

**Response Format:**
```json
{
  "workers": {
    "total_workers": 50,
    "active_workers": 23,
    "idle_workers": 27
  },
  "performance": {
    "urls_processed_last_hour": 8640,
    "current_throughput": "144.0 URLs/minute"
  },
  "queue": {
    "pending_batches": 15
  }
}
```

## Advanced Usage Patterns

### Chaining Operations

You can chain multiple operations for complex workflows:

```
1. First, analyze the website structure:
   analyze_website_structure with url="https://example.com" and purpose="company_info"

2. Then scrape based on the analysis:
   analyze_and_scrape with the recommended settings

3. Finally, search the results:
   query_extracted_data to find specific companies
```

### High-Volume Workflows

For processing large datasets:

```
1. Submit the job:
   submit_high_volume_job with 10,000 URLs

2. Monitor progress:
   get_job_status every few minutes

3. Query results when complete:
   query_extracted_data to analyze the scraped data

4. Check system performance:
   get_system_stats to ensure optimal performance
```

### Authentication Workflows

For sites requiring login:

```
analyze_and_scrape with:
- urls: ["https://linkedin.com/company/example"]
- purpose: "company_info"
- execution_mode: "authenticated"
- credentials: {"username": "your-email", "password": "your-password"}
```

## Error Handling

All tools return structured error information when failures occur:

```json
{
  "success": false,
  "error": "Authentication failed",
  "error_code": "AUTH_ERROR",
  "retry_suggested": true,
  "fallback_available": true
}
```

## Rate Limits and Performance

- **Real-time processing**: Up to 10 URLs per request
- **High-volume processing**: 500-2000 URLs per minute
- **Concurrent requests**: System automatically manages load
- **Retry logic**: Automatic retries with exponential backoff

## Best Practices

### Optimize Your Prompts

**Good:**
```
Scrape these 5 restaurant websites for business information including name, address, phone, and hours of operation
```

**Better:**
```
analyze_and_scrape with:
- urls: [list of 5 restaurant URLs]
- purpose: "company_info"
- additional_context: "Focus on business hours, delivery options, and contact methods"
```

### Use Appropriate Execution Modes

- **intelligent_single**: 1-50 URLs, need immediate results
- **high_volume**: 100+ URLs, can wait for batch processing
- **authenticated**: Sites requiring login/registration

### Monitor Long-Running Jobs

For high-volume jobs, check status periodically:
```
get_job_status with job_id every 5 minutes until completion
```

### Leverage Semantic Search

After scraping, use natural language queries:
```
query_extracted_data: "tech companies in San Francisco with AI focus and 100+ employees"
```

This is more effective than trying to filter during initial scraping.
