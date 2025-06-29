# Running Intelligent Crawl4AI with Docker Compose v2

## Prerequisites

1. **Install Ollama locally**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

2. **Start Ollama**:
```bash
ollama serve
```

3. **Pull DeepSeek model**:
```bash
ollama pull deepseek-coder:1.3b
```

## Running the Full Stack

```bash
# Navigate to the project directory
cd /home/nidal/claude-projects/documents/intelligent-crawl4ai-agent

# Start all services
docker compose -f docker/compose/docker-compose.local-full.yml up -d

# View logs (all services)
docker compose -f docker/compose/docker-compose.local-full.yml logs -f

# View specific service logs
docker compose -f docker/compose/docker-compose.local-full.yml logs -f web-ui
```

## Service URLs

- **Web UI**: http://localhost:8888
- **ChromaDB**: http://localhost:8000
- **Redis**: localhost:6379
- **PostgreSQL**: localhost:5432 (user: scraper_user, password: secure_password_123)
- **Browser Pool 1**: http://localhost:3001
- **Browser Pool 2**: http://localhost:3002
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (user: admin, password: admin123)
- **Nginx Load Balancer**: http://localhost:8080

## Common Commands

### Stop all services
```bash
docker compose -f docker/compose/docker-compose.local-full.yml down
```

### Stop and remove volumes
```bash
docker compose -f docker/compose/docker-compose.local-full.yml down -v
```

### View service status
```bash
docker compose -f docker/compose/docker-compose.local-full.yml ps
```

### Restart a specific service
```bash
docker compose -f docker/compose/docker-compose.local-full.yml restart web-ui
```

### View logs with timestamps
```bash
docker compose -f docker/compose/docker-compose.local-full.yml logs -f --timestamps
```

### Filter logs for errors
```bash
docker compose -f docker/compose/docker-compose.local-full.yml logs -f | grep -E "ERROR|error"
```

### View resource usage
```bash
docker stats
```

## Troubleshooting

If the web UI fails to start, check:
1. Ollama is running: `curl http://localhost:11434/api/tags`
2. All ports are free: `netstat -tlnp | grep -E "8888|8000|6379|5432"`
3. View specific logs: `docker logs intelligent_crawl4ai_web_ui`
