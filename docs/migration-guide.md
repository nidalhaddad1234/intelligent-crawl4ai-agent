# Migration Guide: From Rule-Based to AI-First

This guide helps you migrate from traditional rule-based scrapers to the AI-first architecture.

## What's Changed?

### ❌ Removed Components
- **All Strategy Classes** - No more strategy selection
- **Keyword Routing** - No more if/else chains
- **Manual Handlers** - No more specific handler methods
- **MCP Servers** - Integrated into main system

### ✅ New Components
- **AI Planner** - Handles all decision making
- **Tool Registry** - Self-discovering capabilities
- **Learning System** - Continuous improvement
- **Natural Language** - Plain English interface

## Migration Steps

### 1. Update Your Requests

**OLD WAY - Specific Keywords Required:**
```python
# Had to use specific keywords
"scrape product data from URL"
"extract contact information"
"use css strategy for extraction"
```

**NEW WAY - Natural Language:**
```python
# Just ask naturally!
"I need pricing information from these competitor websites"
"Can you find all email addresses on this site?"
"Get me a list of products with their descriptions and prices"
```

### 2. API Changes

**OLD Endpoints:**
```python
POST /api/analyze-website
POST /api/scrape-single
POST /api/submit-job
GET /api/job-status/{job_id}
```

**NEW Unified Endpoint:**
```python
POST /api/chat
{
    "message": "Your natural language request",
    "urls": ["optional", "url", "list"],
    "session_id": "optional-session-id"
}
```

### 3. Configuration Changes

**OLD Configuration (.env):**
```bash
# Strategy configurations
CSS_STRATEGY_TIMEOUT=30
LLM_STRATEGY_MODEL=gpt-3.5
PLATFORM_STRATEGY_WORKERS=10
STRATEGY_SELECTION_MODE=auto
```

**NEW Configuration (.env):**
```bash
# Simple AI configuration
AI_MODEL=deepseek-coder:1.3b
LEARNING_ENABLED=true
# That's it!
```

### 4. Database Schema

The database schema remains compatible, but the AI system adds metadata:
- `_stored_at` - Timestamp for learning
- `_plan_id` - Associated execution plan
- `_confidence` - AI confidence score

### 5. High-Volume Processing

**OLD Approach:**
```python
executor = HighVolumeExecutor()
job_id = await executor.submit_job(
    urls=urls,
    strategy="DirectoryCSSStrategy",
    batch_size=100
)
```

**NEW Approach:**
```python
# Just ask!
"Process these 10,000 URLs in batches and extract business information"
# AI handles batching, parallelization, and optimization
```

## Code Migration Examples

### Example 1: Simple Scraping

**OLD:**
```python
from src.strategies import DirectoryCSSStrategy
from src.agents import StrategySelector

strategy = StrategySelector.select_strategy(url, "company_info")
result = await strategy.extract(url)
```

**NEW:**
```python
response = requests.post("http://localhost:8888/api/chat", json={
    "message": f"Extract company information from {url}"
})
```

### Example 2: Bulk Processing

**OLD:**
```python
from src.agents import HighVolumeExecutor

executor = HighVolumeExecutor()
await executor.initialize()

job_id = await executor.submit_job(
    urls=url_list,
    purpose="contact_discovery",
    strategy="ContactCSSStrategy",
    priority=1,
    batch_size=50
)

# Poll for status
while True:
    status = await executor.get_job_status(job_id)
    if status['status'] == 'completed':
        break
```

**NEW:**
```python
response = requests.post("http://localhost:8888/api/chat", json={
    "message": f"Extract contact information from these {len(url_list)} URLs",
    "urls": url_list
})
# AI handles everything - batching, strategy, optimization
```

### Example 3: Custom Extraction

**OLD:**
```python
# Had to create custom strategy
class MyCustomStrategy(BaseStrategy):
    def extract(self, soup):
        # Complex extraction logic
        return data

# Register and use
strategy_selector.register_strategy(MyCustomStrategy)
```

**NEW:**
```python
# Just describe what you want
response = requests.post("http://localhost:8888/api/chat", json={
    "message": "Extract product SKUs, prices in EUR, and availability status. Also check if there's a discount percentage shown."
})
# AI figures out how to extract exactly what you need
```

## WebSocket Migration

**OLD WebSocket Events:**
```javascript
ws.send(JSON.stringify({
    action: "analyze",
    url: "https://example.com",
    strategy: "auto"
}));
```

**NEW WebSocket Events:**
```javascript
ws.send(JSON.stringify({
    message: "Analyze https://example.com for e-commerce data",
    urls: ["https://example.com"]
}));
```

## Docker Compose Changes

**OLD services removed:**
- `strategy-selector`
- `high-volume-executor`
- `mcp-server`

**NEW unified service:**
- `web-ui` - Handles everything with AI

## Data Export Changes

**OLD:**
```python
from src.exporters import CSVExporter
exporter = CSVExporter()
exporter.export(data, "output.csv")
```

**NEW:**
```python
response = requests.post("http://localhost:8888/api/chat", json={
    "message": "Export my last scraping results as CSV"
})
# AI handles export with intelligent formatting
```

## Common Migration Issues

### 1. "AI doesn't understand my request"
**Solution:** Use more natural language. Instead of keywords, describe what you want.

### 2. "Where did strategies go?"
**Answer:** AI automatically chooses the best approach. You don't need to specify strategies.

### 3. "How do I customize extraction?"
**Answer:** Describe your requirements in detail. AI adapts to extract exactly what you need.

### 4. "Is it slower than before?"
**Answer:** Initial planning takes 1-2 seconds, but execution is often faster due to optimization.

## Learning System Benefits

The new system learns from your usage:

1. **Pattern Recognition** - Common requests execute faster
2. **Failure Recovery** - Learns from errors automatically
3. **Optimization** - Improves tool selection over time
4. **Custom Patterns** - Adapts to your specific needs

## Rollback Option

If needed, the old version is tagged:
```bash
git checkout v1.0-pre-ai-cleanup
```

But we recommend embracing the AI-first approach for:
- Simpler code maintenance
- Better extraction results
- Automatic improvements
- Natural interaction

## Getting Help

1. **Check AI Understanding:**
   ```
   GET /api/learning/stats
   ```

2. **View Tool Performance:**
   ```
   GET /api/tools/insights
   ```

3. **See AI Recommendations:**
   ```
   GET /api/tools/recommendations
   ```

## Best Practices for AI-First

1. **Be Descriptive** - More context helps AI understand
2. **Let It Learn** - Don't restart frequently, let patterns build
3. **Natural Language** - Write like you're talking to a colleague
4. **Trust the AI** - It often finds better solutions than hardcoded logic

## Conclusion

The migration to AI-first architecture simplifies your code and improves results. Instead of maintaining complex strategy selection logic, you now have an intelligent system that understands your needs and continuously improves.

Welcome to the future of web scraping! 🚀
