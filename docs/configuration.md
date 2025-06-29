# Configuration Guide - AI-First System

## Overview

The AI-First system requires minimal configuration. Most settings are automatically optimized by the AI based on your usage patterns.

## Basic Configuration

### Minimal Setup (.env)
Create a `.env` file with just these essentials:

```bash
# AI Model Selection
AI_MODEL=deepseek-coder:1.3b

# Web Interface Port
WEB_PORT=8888
```

That's it! The system handles everything else automatically.

## Configuration Options

### AI Settings

```bash
# Model Selection (choose based on your hardware)
AI_MODEL=phi3:mini              # Fastest, 2GB RAM
AI_MODEL=deepseek-coder:1.3b    # Balanced (default), 3GB RAM
AI_MODEL=llama3.2:3b            # Better understanding, 4GB RAM
AI_MODEL=mistral:7b             # Best quality, 8GB RAM

# AI Server
OLLAMA_URL=http://localhost:11434  # Default Ollama location

# Planning
PLAN_CONFIDENCE_THRESHOLD=0.3   # Minimum confidence to execute (0.0-1.0)
PLAN_CACHE_SIZE=1000           # Cache frequent plans for speed
```

### Learning System

```bash
# Enable/Disable Learning
LEARNING_ENABLED=true          # Let AI learn from usage

# Learning Parameters
LEARNING_THRESHOLD=0.7         # Minimum confidence to learn pattern
PATTERN_RETENTION_DAYS=90      # How long to keep patterns
TEACHER_MODE=false            # Enable Claude teacher for improvements

# Vector Database
CHROMADB_URL=http://localhost:8000  # ChromaDB for pattern storage
```

### Performance Tuning

```bash
# Execution
MAX_WORKERS=10                 # Parallel tool executions
TOOL_TIMEOUT=30               # Seconds before tool timeout
BATCH_SIZE=50                 # Default batch size for bulk ops

# Resource Limits
MAX_MEMORY_MB=4096            # Memory limit for operations
MAX_URLS_PER_REQUEST=1000     # Safety limit
```

### Web Interface

```bash
# Server Settings
WEB_HOST=0.0.0.0             # Listen on all interfaces
WEB_PORT=8888                # Port number
WEB_WORKERS=4                # Async workers

# Session Management
SESSION_TIMEOUT_MINUTES=60    # Session expiry
MAX_SESSIONS=100             # Concurrent sessions
```

### Database

```bash
# Database Selection (auto-configured)
DATABASE_TYPE=sqlite          # Default, no setup needed
DATABASE_URL=sqlite:///data/scraping.db

# Or for production:
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
```

### Development/Debug

```bash
# Debug Mode
DEBUG=false                   # Production mode
LOG_LEVEL=INFO               # INFO, DEBUG, WARNING, ERROR

# Development Features
HOT_RELOAD=true              # Auto-reload on code changes
PROFILE_TOOLS=true           # Performance profiling
```

## Model Selection Guide

### Hardware Requirements

| Model | RAM | GPU | Speed | Quality |
|-------|-----|-----|-------|---------|
| phi3:mini | 2GB | Optional | ⚡⚡⚡⚡⚡ | ⭐⭐⭐ |
| deepseek-coder:1.3b | 3GB | Optional | ⚡⚡⚡⚡ | ⭐⭐⭐⭐ |
| llama3.2:3b | 4GB | Recommended | ⚡⚡⚡ | ⭐⭐⭐⭐ |
| mistral:7b | 8GB | Recommended | ⚡⚡ | ⭐⭐⭐⭐⭐ |

### Choosing the Right Model

**For Fast Responses (phi3:mini)**:
- Quick extractions
- Simple requests
- High-volume processing
- Limited hardware

**For Balanced Performance (deepseek-coder:1.3b)**:
- General web scraping
- Most use cases
- Good accuracy
- **Recommended default**

**For Complex Understanding (llama3.2:3b)**:
- Complex websites
- Nuanced requests
- Better context understanding
- Multi-step operations

**For Best Quality (mistral:7b)**:
- Mission-critical data
- Complex analysis
- Best understanding
- Requires good hardware

## Environment-Specific Configs

### Development
```bash
# .env.development
AI_MODEL=phi3:mini           # Fast iteration
DEBUG=true
LOG_LEVEL=DEBUG
LEARNING_ENABLED=false       # Disable for testing
HOT_RELOAD=true
```

### Production
```bash
# .env.production
AI_MODEL=deepseek-coder:1.3b
DEBUG=false
LOG_LEVEL=WARNING
LEARNING_ENABLED=true
DATABASE_TYPE=postgresql
MAX_WORKERS=50
```

### Testing
```bash
# .env.test
AI_MODEL=phi3:mini          # Fast tests
DATABASE_URL=sqlite:///:memory:
LEARNING_ENABLED=false
MAX_WORKERS=2
```

## Docker Configuration

### docker-compose.yml Override
```yaml
version: '3.8'
services:
  web-ui:
    environment:
      - AI_MODEL=deepseek-coder:1.3b
      - LEARNING_ENABLED=true
      - MAX_WORKERS=20
```

### Resource Limits
```yaml
services:
  web-ui:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

## Advanced Configuration

### Custom Tool Timeout
```python
# In your .env
TOOL_TIMEOUTS_JSON={"crawler": 60, "analyzer": 30, "exporter": 10}
```

### GPU Acceleration
```bash
# For NVIDIA GPUs
OLLAMA_NUM_GPU=1            # Number of GPUs to use
CUDA_VISIBLE_DEVICES=0      # Which GPU to use
```

### Proxy Configuration
```bash
# For web scraping through proxy
HTTP_PROXY=http://proxy.example.com:8080
HTTPS_PROXY=http://proxy.example.com:8080
NO_PROXY=localhost,127.0.0.1
```

## Configuration Best Practices

### 1. Start Simple
Begin with minimal configuration and add settings only when needed.

### 2. Monitor Performance
```bash
# Check system stats
curl http://localhost:8888/api/system/status

# View tool performance
curl http://localhost:8888/api/tools/insights
```

### 3. Adjust Based on Usage
Let the system run for a few days, then optimize based on:
- Response times
- Memory usage
- Success rates
- Common request types

### 4. Use Environment Files
```bash
# Load different configs
python web_ui_server.py --env production
python web_ui_server.py --env development
```

## Configuration Validation

### Check Configuration
```python
# validate_config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Required settings
required = ['AI_MODEL', 'WEB_PORT']
for setting in required:
    if not os.getenv(setting):
        print(f"ERROR: {setting} not set")

# Validate model
model = os.getenv('AI_MODEL')
valid_models = ['phi3:mini', 'deepseek-coder:1.3b', 'llama3.2:3b', 'mistral:7b']
if model not in valid_models:
    print(f"WARNING: Unknown model {model}")

print("Configuration valid!")
```

## Dynamic Configuration

The AI system can suggest configuration changes:

```
You: The system seems slow

AI: I notice average response time is 5.2 seconds. I recommend:
1. Switch to AI_MODEL=phi3:mini for 3x faster responses
2. Increase PLAN_CACHE_SIZE=5000 to cache more plans
3. Set MAX_WORKERS=20 for better parallelization

Would you like me to show you how to update these settings?
```

## Security Configuration

### API Security (Future)
```bash
# API Authentication
API_KEY_REQUIRED=true
API_KEY=your-secret-key-here

# Rate Limiting
RATE_LIMIT_PER_MINUTE=100
RATE_LIMIT_PER_HOUR=1000
```

### Data Security
```bash
# Encryption
ENCRYPT_DATABASE=true
ENCRYPTION_KEY=your-encryption-key

# Data Retention
AUTO_DELETE_AFTER_DAYS=30
ANONYMIZE_LOGS=true
```

## Monitoring Configuration

### Metrics Export
```bash
# Prometheus metrics
ENABLE_METRICS=true
METRICS_PORT=9090

# Grafana
GRAFANA_URL=http://localhost:3000
GRAFANA_API_KEY=your-key
```

## Migration from v1.0

If migrating from the old system, remove these obsolete settings:
- ❌ `STRATEGY_SELECTION_MODE`
- ❌ `CSS_STRATEGY_TIMEOUT`
- ❌ `LLM_STRATEGY_MODEL`
- ❌ `PLATFORM_STRATEGY_*`
- ❌ `MCP_SERVER_*`

## Troubleshooting Config Issues

### Config Not Loading
```bash
# Check .env file location
ls -la .env

# Validate syntax
python -c "from dotenv import load_dotenv; load_dotenv(); print('OK')"
```

### Wrong Model Loading
```bash
# List available models
ollama list

# Pull correct model
ollama pull deepseek-coder:1.3b
```

## Summary

The AI-First system is designed to work with minimal configuration. Start with just:
- `AI_MODEL` - Choose based on your hardware
- `WEB_PORT` - Where to access the UI

Everything else is optional and can be tuned based on your specific needs. The AI will help optimize settings over time!
