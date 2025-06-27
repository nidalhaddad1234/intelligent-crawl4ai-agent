# 🔄 Intelligent Crawler Flow Documentation

## How the System Should Work

### 🎯 **Expected User Flow**

#### **1. Website Analysis Flow**
```
User: "Analyze https://paris-change.com"
         ↓
System: Extracts URL from message
         ↓
System: Runs IntelligentWebsiteAnalyzer
         ↓
System: Returns detailed analysis:
        - Framework detection
        - API availability
        - Anti-bot measures
        - Recommended strategy
        - Extraction capabilities
```

#### **2. Data Scraping Flow**
```
User: "Scrape contact info from https://paris-change.com"
         ↓
System: Extracts URL and intent
         ↓
System: Selects appropriate strategy (ContactCSSStrategy)
         ↓
System: Executes scraping
         ↓
System: Returns extracted data
```

### 🐛 **Current Issue**

The Web UI is not extracting URLs from the message text. It expects URLs in a separate input field.

### ✅ **Solution Applied**

1. **Created URL Extractor** (`src/utils/url_extractor.py`)
   - Extracts URLs with multiple patterns
   - Handles URLs with/without protocols
   - Cleans message text for better intent detection

2. **Updated Message Processing** (patches/web_ui_improvements.py)
   - Automatically extracts URLs from messages
   - Combines URLs from both sources (message + input field)
   - Improved intent detection
   - Better error messages

### 📝 **How to Apply the Fix**

1. **Stop the current services**:
   ```bash
   docker-compose down
   ```

2. **Apply the patch to web_ui_server.py**:
   
   Add this import at the top:
   ```python
   from src.utils.url_extractor import parse_message_with_urls, extract_urls_from_text
   ```
   
   Replace the `process_chat_message` method with the improved version from `patches/web_ui_improvements.py`

3. **Rebuild and restart**:
   ```bash
   docker-compose build web-ui
   docker-compose up -d
   ```

### 🧪 **Testing the Fix**

Run the test script:
```bash
python tests/test_url_extraction.py
```

Then test in the Web UI:
- "Analyze https://paris-change.com"
- "Scrape data from example.com and test.org"
- "Check the structure of www.mysite.com"

### 🏗️ **System Architecture Flow**

```
Web UI (Browser)
    ↓ (WebSocket/HTTP)
FastAPI Server
    ↓ (Extract URLs + Detect Intent)
IntelligentScrapingAgent
    ↓ (Route to appropriate handler)
    ├── Website Analyzer (Ollama + Patterns)
    ├── Strategy Selector (ChromaDB lookup)
    └── High Volume Executor (Redis + Workers)
    ↓
Results returned to UI
```

### 🔍 **Intent Detection Keywords**

- **Analysis**: analyze, analyse, check, examine, inspect, review
- **Scraping**: scrape, extract, get data, crawl, fetch, pull, collect
- **Job Status**: job, status, progress
- **Search**: search, find, look for, query
- **Export**: export, download, save, csv, excel, json
- **Help**: help, what can you do, capabilities, guide

### 💡 **Best Practices for Users**

1. **Clear Commands**:
   - ✅ "Analyze https://example.com"
   - ✅ "Scrape contact info from https://site.com"
   - ❌ "Check this out: site.com" (ambiguous)

2. **Multiple URLs**:
   - "Analyze these sites: url1.com, url2.com, url3.com"
   - "Scrape products from [list of URLs]"

3. **Specific Requests**:
   - "Extract pricing information from https://shop.com"
   - "Get business hours and contact details from https://restaurant.com"

### 🚀 **Advanced Features**

1. **Batch Processing**: URLs > 50 trigger high-volume mode
2. **Smart Strategy Selection**: AI picks optimal extraction method
3. **Learning System**: ChromaDB stores successful patterns
4. **Real-time Updates**: WebSocket for live progress

### 📊 **Monitoring the System**

- **Grafana Dashboard**: http://localhost:3000
- **System Status**: "Show me system status"
- **Job Monitoring**: "What's the status of job [ID]"
- **Logs**: `docker-compose logs -f web-ui`

### 🆘 **Troubleshooting**

If analysis still doesn't work after applying the fix:

1. **Check Ollama is running**:
   ```bash
   docker-compose ps ollama
   curl http://localhost:11434/api/tags
   ```

2. **Verify ChromaDB**:
   ```bash
   curl http://localhost:8000/api/v1/heartbeat
   ```

3. **Check logs**:
   ```bash
   docker-compose logs web-ui | grep ERROR
   docker-compose logs intelligent-agent
   ```

4. **Test components individually**:
   ```bash
   # Test URL extraction
   python tests/test_url_extraction.py
   
   # Test Ollama
   curl http://localhost:11434/api/generate -d '{
     "model": "llama3.1",
     "prompt": "Hello"
   }'
   ```
