# Troubleshooting Guide - AI-First System

## Overview

This guide helps you resolve common issues with the AI-first web scraping system. Most problems have simple solutions!

## 🚀 Startup Issues

### Ollama Not Found
**Error**: `Ollama AI is not available`

**Solutions**:
1. Install Ollama:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```

2. Start Ollama service:
   ```bash
   ollama serve
   ```

3. Verify installation:
   ```bash
   ollama list
   ```

### Model Not Found
**Error**: `model 'deepseek-coder:1.3b' not found`

**Solution**:
```bash
# Download the model (one-time, ~600MB)
ollama pull deepseek-coder:1.3b

# Or try alternative models:
ollama pull phi3:mini       # Smallest (2GB)
ollama pull llama3.2:3b     # Medium (2GB)
ollama pull mistral:7b      # Best (4GB)
```

### Port Already in Use
**Error**: `[Errno 48] Address already in use`

**Solutions**:
1. Change port in `.env`:
   ```bash
   WEB_PORT=8889
   ```

2. Or kill existing process:
   ```bash
   # Find process
   lsof -i :8888
   
   # Kill it
   kill -9 <PID>
   ```

## 💬 AI Understanding Issues

### "I don't understand your request"
**Problem**: AI confidence too low to create a plan

**Solutions**:
1. **Be more descriptive**:
   ```
   Bad: "scrape site"
   Good: "Extract product names and prices from this e-commerce website"
   ```

2. **Provide context**:
   ```
   Bad: "get data"
   Good: "I'm researching smartphones - please extract model names, prices, and specifications"
   ```

3. **Break into steps**:
   ```
   Instead of: "Analyze competitors and create report"
   Try: 
   - "First, extract product data from these competitor sites"
   - "Now analyze the pricing patterns"
   - "Create a comparison report"
   ```

### AI Makes Wrong Assumptions
**Problem**: AI misunderstands intent

**Solution**: Provide corrections and let it learn:
```
You: Extract business info from this site
AI: [Extracts wrong data]
You: I meant contact information like emails and phone numbers
AI: I understand now. Let me extract contact details instead.
[AI learns this preference]
```

## ⚡ Performance Issues

### Slow Response Times
**Problem**: AI takes too long to respond

**Solutions**:

1. **Use faster model**:
   ```bash
   # In .env
   AI_MODEL=phi3:mini  # Fastest
   ```

2. **Enable caching**:
   ```bash
   PLAN_CACHE_SIZE=1000
   ```

3. **Check system resources**:
   ```bash
   # CPU usage
   top
   
   # Memory usage
   free -h
   ```

4. **Reduce parallel operations**:
   ```bash
   MAX_WORKERS=5  # Instead of default 10
   ```

### Out of Memory
**Problem**: System runs out of RAM

**Solutions**:

1. **Use smaller model**:
   ```bash
   AI_MODEL=phi3:mini
   ```

2. **Process in smaller batches**:
   ```
   Instead of: "Process these 1000 URLs"
   Try: "Process the first 100 URLs"
   ```

3. **Clear learning memory**:
   ```bash
   # Restart to clear memory
   docker-compose restart
   ```

## 🕷️ Scraping Failures

### "Failed to extract data"
**Common Causes & Solutions**:

1. **Dynamic JavaScript Content**
   ```
   Tell AI: "This site loads content dynamically with JavaScript"
   AI will use browser automation
   ```

2. **Login Required**
   ```
   You: "This site needs login - username: X, password: Y"
   AI handles authentication
   ```

3. **Anti-Bot Protection**
   ```
   AI automatically detects and handles:
   - Rate limiting (slows down)
   - CAPTCHAs (reports to you)
   - User-agent detection (rotates)
   ```

### Incomplete Data Extraction
**Problem**: Missing some data fields

**Solutions**:
1. **Be specific about requirements**:
   ```
   "Make sure to get product SKUs, even if they're in small text"
   ```

2. **Provide examples**:
   ```
   "The phone numbers might be formatted like (555) 123-4567"
   ```

3. **Request re-extraction**:
   ```
   "Please try again and look for prices in the sidebar too"
   ```

## 📚 Learning System Issues

### Learning Not Improving
**Problem**: AI doesn't seem to learn from usage

**Solutions**:

1. **Enable learning**:
   ```bash
   LEARNING_ENABLED=true
   ```

2. **Check ChromaDB**:
   ```bash
   # Start ChromaDB
   docker run -d -p 8000:8000 chromadb/chroma
   ```

3. **Manual learning trigger**:
   ```bash
   curl -X POST http://localhost:8888/api/learning/train
   ```

### Forgetting Patterns
**Problem**: AI forgets learned patterns

**Solution**: Increase retention:
```bash
PATTERN_RETENTION_DAYS=180  # Keep patterns longer
LEARNING_THRESHOLD=0.6      # Learn from more attempts
```

## 🔧 Tool Errors

### "Tool execution failed"
**Common Tool Issues**:

1. **Database Tool**
   - Check SQLite file permissions
   - Ensure directory exists: `mkdir -p data`

2. **Export Tool**
   - Check write permissions
   - Ensure export directory exists

3. **Crawler Tool**
   - Verify Playwright installation:
     ```bash
     playwright install chromium
     ```

### Tools Not Found
**Problem**: AI can't find tools

**Solution**: Check tool registration:
```python
# In Python console
from ai_core.registry import tool_registry
print(tool_registry.list_tools())
# Should show: ['crawler', 'database', 'analyzer', ...]
```

## 🌐 Network Issues

### Connection Timeouts
**Problem**: Websites timing out

**Solutions**:
1. **Increase timeout**:
   ```bash
   TOOL_TIMEOUT=60  # 60 seconds
   ```

2. **Tell AI about slow sites**:
   ```
   "This site is slow, please wait for it to fully load"
   ```

### SSL/Certificate Errors
**Problem**: HTTPS certificate issues

**Solution**: For development only:
```bash
# In .env
VERIFY_SSL=false
```

## 🐛 Debugging

### Enable Debug Mode
```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

### View AI Planning
Watch AI decision making:
```bash
# Check logs
tail -f logs/web_ui.log

# You'll see:
# AI Plan created with 3 steps, confidence: 0.85
# Step 1: crawler.extract_content(...)
```

### Check Component Health
```bash
# System status
curl http://localhost:8888/api/system/status

# Tool performance
curl http://localhost:8888/api/tools/insights

# Learning stats
curl http://localhost:8888/api/learning/stats
```

## 💾 Data Issues

### Lost Session Data
**Problem**: Chat history disappeared

**Solution**: Sessions are temporary. To persist:
```
You: "Save our conversation"
AI: "I'll save this session data for you"
```

### Database Errors
**Problem**: Can't save/retrieve data

**Solutions**:
1. **Check database file**:
   ```bash
   ls -la data/scraping.db
   ```

2. **Reset database**:
   ```bash
   rm data/scraping.db
   # Will recreate on next use
   ```

## 🆘 Getting Help

### Self-Diagnosis
Ask the AI for help:
```
"Why did the last extraction fail?"
"Show me system status"
"What tools are available?"
"Check my learning statistics"
```

### Logs Location
- Web UI logs: `logs/web_ui.log`
- Tool logs: `logs/tools.log`
- Learning logs: `logs/learning.log`

### Community Support
- GitHub Issues: [Report bugs](https://github.com/yourusername/intelligent-crawl4ai-agent/issues)
- Discussions: [Ask questions](https://github.com/yourusername/intelligent-crawl4ai-agent/discussions)

## 🔄 Recovery Procedures

### Full System Reset
```bash
# Stop everything
docker-compose down

# Clear data
rm -rf data/
rm -rf logs/

# Restart fresh
docker-compose up -d
```

### Keep Learning Data
```bash
# Backup learning patterns
cp -r chromadb_data/ chromadb_backup/

# Reset other components
rm data/scraping.db
rm -rf logs/

# Restore learning
cp -r chromadb_backup/ chromadb_data/
```

## 🎯 Prevention Tips

1. **Regular Updates**:
   ```bash
   git pull
   pip install -r requirements.txt --upgrade
   ```

2. **Monitor Resources**:
   - Keep 4GB RAM free
   - Monitor disk space
   - Check CPU usage

3. **Best Practices**:
   - Be descriptive in requests
   - Let AI learn from mistakes
   - Provide feedback
   - Start with small batches

## 📋 Common Error Reference

| Error | Cause | Quick Fix |
|-------|-------|-----------|
| "AI not available" | Ollama not running | `ollama serve` |
| "Low confidence" | Unclear request | Add more detail |
| "Tool failed" | Missing dependency | Check tool requirements |
| "Out of memory" | Large operation | Use smaller batches |
| "Timeout" | Slow website | Increase timeout |
| "No data extracted" | Wrong assumptions | Provide examples |

Remember: The AI-first system is designed to handle errors gracefully and learn from them. Most issues resolve themselves as the system learns your preferences!
