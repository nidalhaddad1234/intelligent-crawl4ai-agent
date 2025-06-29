# 🚀 Intelligent Crawl4AI Agent - Complete Setup Guide

## What This System Does

This is an **AI-powered web scraping system** that understands natural language requests and automatically extracts data from websites at scale.

### Key Features:
- 🤖 **Natural Language Interface**: Just describe what you want in plain English
- 🧠 **AI-Powered Analysis**: Uses DeepSeek to understand websites and extract data
- ⚡ **High-Volume Processing**: Handles thousands of URLs concurrently
- 🎯 **Smart Strategy Selection**: Automatically chooses the best extraction method
- 📊 **Complete Data Pipeline**: From scraping to storage with monitoring

## Prerequisites

1. **Install Docker & Docker Compose v2**
2. **Install Ollama**:
   ```bash
   curl -fsSL https://ollama.com/install.sh | sh
   ```
3. **Start Ollama and get DeepSeek**:
   ```bash
   ollama serve
   # In another terminal:
   ollama pull deepseek-coder:1.3b
   ```

## Quick Start

```bash
# From project root
cd /home/nidal/claude-projects/documents/intelligent-crawl4ai-agent

# Start everything
docker compose -f docker/compose/docker-compose.local-full.yml up -d

# Watch the logs
docker compose -f docker/compose/docker-compose.local-full.yml logs -f
```

## System Components

### 🌐 **Web Interface (port 8888)**
- ChatGPT-like interface for natural language requests
- Example: "Extract all product prices from these 1000 URLs"

### 🔧 **High-Volume Workers**
- Process thousands of URLs concurrently
- Intelligent batching and parallelization
- Automatic retry and error handling

### 🤖 **Intelligent Analyzer**
- Analyzes website structure
- Detects content types (e-commerce, directory, blog)
- Chooses optimal extraction strategies

### 🗄️ **Data Storage**
- **PostgreSQL**: Structured extracted data
- **ChromaDB**: AI embeddings for semantic search
- **Redis**: Job queuing and caching

### 🌍 **Browser Pools (ports 3001-3002)**
- Headless Chrome instances
- Handles JavaScript-heavy sites
- Stealth mode to avoid detection

### 📊 **Monitoring**
- **Prometheus** (port 9090): Metrics collection
- **Grafana** (port 3000): Visual dashboards

## How to Use

### 1. Access the Web UI
Open http://localhost:8888 in your browser

### 2. Natural Language Requests
Simply type what you want:
- "Extract all email addresses from these company websites"
- "Get product details from this e-commerce site"
- "Monitor these pages daily for price changes"

### 3. The AI Does Everything
- Analyzes the websites
- Chooses extraction methods
- Processes in parallel
- Stores results in database

## Example Workflows

### Bulk Directory Scraping
```
You: Extract business info from these 5000 Yellow Pages URLs

AI: I'll extract business information from 5,000 Yellow Pages listings.
    - Detected: Directory format
    - Extracting: Name, phone, address, hours
    - Processing in batches of 250
    
Progress: [████████----] 70% complete
```

### E-commerce Monitoring
```
You: Track prices daily for these 500 products

AI: Setting up daily price monitoring for 500 products.
    - Schedule: Every day at 9 AM
    - Tracking price changes > 1%
    - Will alert on significant drops
```

## Viewing Logs

### All Services
```bash
docker compose -f docker/compose/docker-compose.local-full.yml logs -f
```

### Specific Service
```bash
# Web UI logs
docker compose -f docker/compose/docker-compose.local-full.yml logs -f web-ui

# Worker logs
docker compose -f docker/compose/docker-compose.local-full.yml logs -f high-volume-workers

# Error filtering
docker compose -f docker/compose/docker-compose.local-full.yml logs -f | grep ERROR
```

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Web UI | http://localhost:8888 | - |
| Grafana | http://localhost:3000 | admin / admin123 |
| ChromaDB | http://localhost:8000 | - |
| Prometheus | http://localhost:9090 | - |
| PostgreSQL | localhost:5432 | scraper_user / secure_password_123 |
| Redis | localhost:6379 | - |

## Troubleshooting

### If services fail to start:
```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check individual service logs
docker logs intelligent_crawl4ai_web_ui

# Restart everything
docker compose -f docker/compose/docker-compose.local-full.yml down
docker compose -f docker/compose/docker-compose.local-full.yml up -d
```

### Database Issues:
The `db-migrate` service automatically creates tables on first run.

### Port Conflicts:
Make sure ports 8888, 8000, 6379, 5432, 3000-3002, 9090 are free.

## Stop Everything

```bash
# Stop all services
docker compose -f docker/compose/docker-compose.local-full.yml down

# Stop and remove all data
docker compose -f docker/compose/docker-compose.local-full.yml down -v
```

## Architecture Flow

```
User Request (Natural Language)
         ↓
   Web UI (8888)
         ↓
 Ollama/DeepSeek AI
         ↓
High-Volume Workers ←→ Redis Queue
         ↓
 Browser Pools + AI Analysis
         ↓
    Data Storage
   ├── PostgreSQL (structured)
   ├── ChromaDB (embeddings)
   └── Redis (cache)
         ↓
   Results to User
```

The system is designed to handle everything from simple single-page extractions to massive bulk operations with thousands of URLs, all through natural language commands!
