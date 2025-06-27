# Using Local Ollama with DeepSeek

## Quick Start

```bash
# 1. Make sure your local Ollama is running with DeepSeek model:
ollama pull deepseek-coder:1.3b
ollama serve

# 2. Use the local compose file:
docker-compose -f docker-compose.local.yml up -d

# 3. Access the Web UI:
open http://localhost:8888
```

## Containers Running

- **ChromaDB** (port 8000) - Vector database for pattern storage
- **Redis** (port 6379) - Session management and caching
- **Browser Pool** (port 3001) - Chrome browser for web scraping
- **Web UI** (port 8888) - ChatGPT-like interface

## What's Different

The `docker-compose.local.yml` file:
- ✅ Uses your LOCAL Ollama at `http://host.docker.internal:11434`
- ✅ No Ollama container (uses your machine's Ollama)
- ✅ Mounts `web_ui_server.py` for live updates
- ✅ Uses SQLite instead of PostgreSQL
- ✅ Includes browser pool for actual web scraping
- ✅ Runs essential services: ChromaDB, Redis, Browser Pool, Web UI

## Test URL Extraction

Try these in the Web UI:
- "Analyze https://paris-change.com"
- "Scrape contact info from https://example.com"
- "Check these sites: site1.com, site2.org"

## View Logs

```bash
docker-compose -f docker-compose.local.yml logs -f web-ui
```

## Stop Services

```bash
docker-compose -f docker-compose.local.yml down
```
