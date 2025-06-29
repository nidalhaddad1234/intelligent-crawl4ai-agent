# 🤖 Intelligent Crawl4AI Agent - Complete System

## System Overview

This is a **production-ready AI-powered web scraping system** that processes natural language requests to extract data from websites at massive scale.

## ✅ What I've Set Up

### 1. **Full Docker Compose Configuration**
Located at: `docker/compose/docker-compose.local-full.yml`

### 2. **All Core Services**
- **Web UI** (8888): Natural language interface
- **High-Volume Workers**: AI-powered scraping engine (2 replicas)
- **Intelligent Analyzer**: Website analysis service
- **MCP Server** (8811): Model Context Protocol server
- **Browser Pools** (3001-3002): 2x headless Chrome instances
- **Data Storage**: PostgreSQL + ChromaDB + Redis
- **Monitoring**: Prometheus + Grafana
- **Load Balancer**: Nginx

### 3. **Automatic Database Setup**
- DB migration service creates tables on first run
- No manual SQL needed

### 4. **Complete Integration**
- All workers use the `src/` directory from your GitHub
- Proper Python paths configured
- Dependencies installed automatically

## 🚀 How to Run Everything

### Option 1: Quick Start Script
```bash
./start.sh
```

### Option 2: Manual Docker Compose
```bash
# Make sure Ollama is running with DeepSeek
ollama serve
ollama pull deepseek-coder:1.3b

# Start all services
docker-compose -f docker/compose/docker-compose.local-full.yml up -d

# View logs
docker-compose -f docker/compose/docker-compose.local-full.yml logs -f
```

## 📊 What Happens When You Run It

1. **Database Setup**: Migration service creates all required tables
2. **Services Start**: All 11 services spin up
3. **Workers Initialize**: 
   - High-volume workers connect to Redis queue
   - Intelligent analyzer prepares for website analysis
   - MCP server starts listening
4. **Web UI Ready**: Access at http://localhost:8888
5. **System Ready**: Can process natural language scraping requests

## 💬 Example Usage

Once running, go to http://localhost:8888 and try:

```
"Extract all product information from these 1000 e-commerce URLs"
"Get contact details from these 500 business websites"
"Monitor these 100 pages daily for price changes"
```

The AI will:
- Understand your request
- Analyze the websites
- Choose extraction strategies
- Process URLs in parallel
- Store results in database
- Return formatted data

## 📋 Service Details

| Service | Purpose | Port | Container Name |
|---------|---------|------|----------------|
| web-ui | Natural language interface | 8888 | intelligent_crawl4ai_web_ui |
| high-volume-workers | Bulk scraping engine | - | (2 replicas) |
| intelligent-analyzer | Website analysis | - | intelligent_crawl4ai_analyzer |
| mcp-server | Model Context Protocol | 8811 | intelligent_crawl4ai_mcp |
| chromadb | Vector embeddings | 8000 | intelligent_crawl4ai_chromadb |
| postgres | Main database | 5432 | intelligent_crawl4ai_postgres |
| redis | Queue & cache | 6379 | intelligent_crawl4ai_redis |
| browser-pool-1/2 | Web automation | 3001-3002 | intelligent_crawl4ai_browser_1/2 |
| prometheus | Metrics | 9090 | intelligent_crawl4ai_prometheus |
| grafana | Dashboards | 3000 | intelligent_crawl4ai_grafana |
| nginx | Load balancer | 8080 | intelligent_crawl4ai_nginx |

## 🔍 Monitoring

### Logs
```bash
# All services
docker-compose -f docker/compose/docker-compose.local-full.yml logs -f

# Specific service
docker-compose -f docker/compose/docker-compose.local-full.yml logs -f web-ui

# Workers only
docker-compose -f docker/compose/docker-compose.local-full.yml logs -f high-volume-workers
```

### Metrics
- Grafana: http://localhost:3000 (admin/admin123)
- Prometheus: http://localhost:9090

## 🛠️ Troubleshooting

### Check Service Health
```bash
docker-compose -f docker/compose/docker-compose.local-full.yml ps
```

### Individual Service Logs
```bash
docker logs intelligent_crawl4ai_web_ui
docker logs intelligent_crawl4ai_chromadb
```

### Restart Services
```bash
docker-compose -f docker/compose/docker-compose.local-full.yml restart web-ui
```

### Complete Reset
```bash
docker-compose -f docker/compose/docker-compose.local-full.yml down -v
./start.sh
```

## 🏗️ Architecture

```
┌─────────────────────┐
│   Web UI (8888)     │ ← Natural Language Input
└──────────┬──────────┘
           │
    ┌──────▼──────┐
    │   Ollama    │ ← DeepSeek AI Processing
    │  (Local)    │
    └──────┬──────┘
           │
┌──────────▼──────────────────────────────┐
│        High-Volume Workers              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │Analyzer │  │Selector │  │Executor │ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
└───────┼────────────┼────────────┼──────┘
        │            │            │
   ┌────▼────┐  ┌───▼────┐  ┌───▼────┐
   │ChromaDB │  │ Redis  │  │Postgres│
   └─────────┘  └────────┘  └────────┘
        │            │            │
    ┌───▼────────────▼────────────▼───┐
    │        Browser Pools            │
    │    (Chrome 1)    (Chrome 2)     │
    └─────────────────────────────────┘
```

## 🎯 Key Features

1. **Natural Language Processing**: Just describe what you want
2. **Intelligent Analysis**: AI understands website structures
3. **Massive Scale**: Process thousands of URLs concurrently
4. **Smart Strategies**: Automatically adapts to different site types
5. **Complete Pipeline**: From request to structured data
6. **Monitoring**: Real-time metrics and logs

## 📝 Files Created

- `docker/compose/docker-compose.local-full.yml` - Complete docker configuration
- `QUICK_START.md` - This guide
- `start.sh` - One-command launcher

The system is now ready to use! Just run `./start.sh` and start scraping with natural language commands! 🚀
