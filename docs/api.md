# API Reference - AI-First Web Scraping

## Overview

The AI-First API uses natural language processing to understand your requests. There's one main endpoint for all interactions, with additional endpoints for monitoring and insights.

## Base URL
```
http://localhost:8888
```

## Authentication
Currently no authentication required for local deployment. Production deployments should implement API keys.

## Main Endpoints

### Chat Endpoint (Primary Interface)

**POST** `/api/chat`

Send natural language requests to the AI scraping agent.

**Request Body:**
```json
{
    "message": "string - Your request in plain English",
    "urls": ["array", "of", "urls"] // optional
    "session_id": "string", // optional, for conversation continuity
    "options": {} // optional, additional parameters
}
```

**Response:**
```json
{
    "response": "AI agent's response with results",
    "session_id": "session-uuid",
    "timestamp": "2024-01-15T10:30:00Z",
    "metadata": {
        "message_count": 5,
        "plan_confidence": 0.92
    },
    "success": true,
    "extracted_data": {} // optional, structured data
}
```

**Examples:**

1. **Simple Scraping:**
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Extract product information from https://example.com/products"
  }'
```

2. **Bulk Processing:**
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Process these electronics sites and compare prices",
    "urls": [
      "https://store1.com/laptop",
      "https://store2.com/laptop",
      "https://store3.com/laptop"
    ]
  }'
```

3. **Data Analysis:**
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze my scraped data for pricing trends"
  }'
```

### Session Management

**POST** `/api/sessions`

Create a new chat session.

**Response:**
```json
{
    "session_id": "uuid-string"
}
```

**GET** `/api/sessions/{session_id}/messages`

Retrieve conversation history.

**Response:**
```json
[
    {
        "id": "message-id",
        "role": "user|assistant",
        "content": "message content",
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {}
    }
]
```

### System Status

**GET** `/api/system/status`

Get system health and metrics.

**Response:**
```json
{
    "status": "operational",
    "uptime_seconds": 3600,
    "total_requests": 150,
    "active_sessions": 5,
    "components_health": {
        "ollama": "healthy",
        "chromadb": "healthy",
        "database": "healthy"
    },
    "performance_metrics": {
        "avg_response_time_ms": 150,
        "success_rate": 0.95
    }
}
```

### Learning System Endpoints

**GET** `/api/learning/stats`

View learning system statistics.

**Response:**
```json
{
    "total_patterns": 1247,
    "success_rate": 0.943,
    "tools_used": {
        "crawler": 567,
        "analyzer": 234,
        "exporter": 189
    },
    "improvement_rate": 0.08,
    "last_learning": "2024-01-15T09:00:00Z"
}
```

**POST** `/api/learning/train`

Trigger manual learning routine.

**Response:**
```json
{
    "status": "completed",
    "report": "Analyzed 50 failures, created 12 new patterns, optimized 5 tool combinations"
}
```

### Tool Insights (Phase 6 Features)

**GET** `/api/tools/insights`

Get comprehensive tool usage insights.

**Response:**
```json
{
    "tool_performance": {
        "crawler": {
            "avg_time": 2.3,
            "success_rate": 0.96,
            "usage_count": 1234
        }
    },
    "common_combinations": [
        ["crawler", "analyzer", "exporter"]
    ],
    "bottlenecks": ["analyzer tool slower on large datasets"]
}
```

**GET** `/api/tools/recommendations`

Get AI recommendations for new tools.

**Response:**
```json
{
    "missing_tools": [
        {
            "intent": "schedule recurring scrapes",
            "example_request": "Monitor this site daily",
            "suggested_name": "scheduler",
            "priority": "high"
        }
    ],
    "optimization_suggestions": [
        "Consider caching for repeated URL patterns"
    ]
}
```

**POST** `/api/tools/optimize-pipeline`

Optimize a tool execution pipeline.

**Request:**
```json
{
    "tools": [
        {"tool": "crawler", "function": "extract_content"},
        {"tool": "analyzer", "function": "find_patterns"},
        {"tool": "exporter", "function": "export_csv"}
    ]
}
```

**Response:**
```json
{
    "optimized_pipeline": [
        {"tool": "crawler", "function": "extract_content"},
        {"tool": "exporter", "function": "export_csv"},
        {"tool": "analyzer", "function": "find_patterns"}
    ],
    "optimization": "Moved export before analysis for better memory usage"
}
```

### WebSocket Interface

**WebSocket** `/ws/{session_id}`

Real-time bidirectional communication.

**Client → Server:**
```json
{
    "message": "Your request",
    "urls": ["optional", "urls"]
}
```

**Server → Client:**
```json
{
    "type": "response|status|error",
    "content": "Response content",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

**WebSocket Events:**
- `response` - AI response to query
- `status` - Execution status updates
- `error` - Error notifications

## Common Use Cases

### 1. Product Price Monitoring
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Monitor iPhone 15 prices across major retailers and alert me if any drop below $800"
  }'
```

### 2. Business Data Extraction
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Extract business information from these Yellow Pages results",
    "urls": ["https://yellowpages.com/search?..."]
  }'
```

### 3. Content Analysis
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze sentiment in customer reviews from this product page"
  }'
```

### 4. Data Export
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Export all restaurant data I scraped today as an Excel file with charts"
  }'
```

## Error Handling

All endpoints return consistent error responses:

```json
{
    "success": false,
    "error": "Error description",
    "code": "ERROR_CODE",
    "details": {} // optional additional context
}
```

**Common Error Codes:**
- `AI_PLANNING_FAILED` - AI couldn't understand request
- `TOOL_EXECUTION_ERROR` - Tool failed during execution
- `INVALID_REQUEST` - Malformed request
- `SESSION_NOT_FOUND` - Invalid session ID
- `SYSTEM_OVERLOAD` - Too many concurrent requests

## Rate Limiting

Local deployment has no rate limits. Production deployments should implement:
- 100 requests/minute per IP
- 10 concurrent WebSocket connections
- 1000 requests/hour per session

## Best Practices

1. **Use Sessions** - Maintain context across requests
2. **Be Descriptive** - More detail helps AI understand
3. **Batch URLs** - Send multiple URLs in one request
4. **Monitor Learning** - Check stats periodically
5. **Handle Errors** - Implement retry logic

## SDK Examples

### Python
```python
import requests

class IntelligentScraper:
    def __init__(self, base_url="http://localhost:8888"):
        self.base_url = base_url
        self.session_id = self._create_session()
    
    def _create_session(self):
        resp = requests.post(f"{self.base_url}/api/sessions")
        return resp.json()["session_id"]
    
    def chat(self, message, urls=None):
        resp = requests.post(
            f"{self.base_url}/api/chat",
            json={
                "message": message,
                "urls": urls,
                "session_id": self.session_id
            }
        )
        return resp.json()

# Usage
scraper = IntelligentScraper()
result = scraper.chat("Extract product data from https://example.com")
print(result["response"])
```

### JavaScript
```javascript
class IntelligentScraper {
    constructor(baseUrl = 'http://localhost:8888') {
        this.baseUrl = baseUrl;
        this.sessionId = null;
        this.init();
    }
    
    async init() {
        const resp = await fetch(`${this.baseUrl}/api/sessions`, {
            method: 'POST'
        });
        const data = await resp.json();
        this.sessionId = data.session_id;
    }
    
    async chat(message, urls = null) {
        const resp = await fetch(`${this.baseUrl}/api/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message,
                urls,
                session_id: this.sessionId
            })
        });
        return await resp.json();
    }
}

// Usage
const scraper = new IntelligentScraper();
const result = await scraper.chat('Extract contact info from https://example.com');
console.log(result.response);
```

## Deprecation Notice

The following endpoints from v1.0 are **REMOVED**:
- `/api/analyze-website` - Use natural language via `/api/chat`
- `/api/scrape-single` - Use natural language via `/api/chat`
- `/api/submit-job` - Use natural language via `/api/chat`
- `/api/strategies` - No longer needed, AI selects approach
- All strategy-specific endpoints

## Support

For issues or questions:
- GitHub Issues: [Project Issues](https://github.com/yourusername/intelligent-crawl4ai-agent/issues)
- Documentation: [Full Docs](https://github.com/yourusername/intelligent-crawl4ai-agent/docs)
