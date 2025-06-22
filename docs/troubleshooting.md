# Troubleshooting Guide

## Overview

This guide covers common issues, error messages, and solutions for the Intelligent Crawl4AI Agent. Use this as your first resource when encountering problems.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Installation Issues](#installation-issues)
- [Service Connection Problems](#service-connection-problems)
- [Claude Desktop Integration](#claude-desktop-integration)
- [Performance Issues](#performance-issues)
- [Memory and Resource Problems](#memory-and-resource-problems)
- [Strategy and Extraction Issues](#strategy-and-extraction-issues)
- [Database Issues](#database-issues)
- [Network and Connectivity](#network-and-connectivity)
- [Error Reference](#error-reference)
- [Monitoring and Debugging](#monitoring-and-debugging)

## Quick Diagnostics

### Health Check Script
Run the comprehensive health check:
```bash
python scripts/health_check.py --verbose

# Expected output for healthy system:
✅ Python dependencies: OK
✅ Ollama service: OK (llama3.1, nomic-embed-text)
✅ ChromaDB: OK (4 collections)
✅ Redis: OK
✅ PostgreSQL: OK
✅ Browser pools: OK (2 pools, 40 sessions)
✅ MCP server: OK
```

### Quick Service Status
```bash
# Check all Docker services
docker-compose ps

# Check individual services
curl http://localhost:11434/api/tags        # Ollama
curl http://localhost:8000/api/v1/heartbeat # ChromaDB
redis-cli ping                              # Redis
docker logs intelligent_crawl4ai_agent     # Agent logs
```

### System Resource Check
```bash
# Check system resources
free -h                    # Memory usage
df -h                     # Disk space
docker system df          # Docker space usage
docker stats --no-stream # Container resource usage
```

## Installation Issues

### Python Dependencies

**Issue**: `pip install` fails with compilation errors
```bash
# Solution 1: Update build tools
sudo apt-get update
sudo apt-get install build-essential python3-dev libpq-dev

# Solution 2: Use binary packages
pip install --only-binary=all -r requirements.txt

# Solution 3: Use conda for problematic packages
conda install psycopg2 chromadb sentence-transformers
```

**Issue**: Playwright browser installation fails
```bash
# Solution: Manual installation with explicit dependencies
playwright install --with-deps chromium
playwright install --with-deps firefox

# For Ubuntu/Debian systems:
sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libgtk-3-0 libgbm1
```

**Issue**: ChromaDB installation fails
```bash
# Solution: Install specific version
pip install chromadb==0.4.24
# Or use conda
conda install -c conda-forge chromadb
```

### Docker Issues

**Issue**: Docker Compose services won't start
```bash
# Check Docker daemon
sudo systemctl status docker
sudo systemctl start docker

# Rebuild containers
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d

# Check for port conflicts
sudo netstat -tulpn | grep :8000  # ChromaDB
sudo netstat -tulpn | grep :11434 # Ollama
```

**Issue**: Permission denied errors
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
chmod +x scripts/*.sh
chmod +x docker/*.sh

# Fix Docker permissions
sudo usermod -aG docker $USER
# Logout and login again
```

### Ollama Setup Issues

**Issue**: Ollama models not downloading
```bash
# Check Ollama service
curl http://localhost:11434/api/tags

# Manually pull models
ollama pull llama3.1
ollama pull nomic-embed-text

# Check available models
ollama list

# If Ollama not responding:
ollama serve --host 0.0.0.0
```

**Issue**: GPU not detected by Ollama
```bash
# Check NVIDIA setup
nvidia-smi

# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

echo "deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container-list" | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

## Service Connection Problems

### ChromaDB Connection Issues

**Error**: `Connection refused to ChromaDB`
```bash
# Check ChromaDB container
docker logs intelligent_crawl4ai_chromadb

# Restart ChromaDB
docker-compose restart chromadb

# Check authentication
curl -H "X-Chroma-Token: test-token" http://localhost:8000/api/v1/heartbeat

# Test collection creation
python -c "
import chromadb
client = chromadb.HttpClient(host='localhost', port=8000)
print(client.heartbeat())
"
```

**Error**: `Authentication failed`
```bash
# Check token configuration
echo $CHROMADB_TOKEN

# Update docker-compose.yml with correct token
CHROMA_SERVER_AUTH_CREDENTIALS=your-token-here

# Restart services
docker-compose restart
```

### Ollama Connection Issues

**Error**: `Ollama API not responding`
```bash
# Check Ollama container
docker logs intelligent_crawl4ai_ollama

# Test API directly
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Hello",
  "stream": false
}'

# Check model availability
curl http://localhost:11434/api/tags
```

**Error**: `Model not found: llama3.1`
```bash
# Pull missing models
docker exec intelligent_crawl4ai_ollama ollama pull llama3.1
docker exec intelligent_crawl4ai_ollama ollama pull nomic-embed-text

# Verify models
docker exec intelligent_crawl4ai_ollama ollama list
```

### Redis Connection Issues

**Error**: `Redis connection failed`
```bash
# Check Redis container
docker logs intelligent_crawl4ai_redis

# Test Redis connection
redis-cli ping

# Check Redis configuration
redis-cli CONFIG GET maxmemory
redis-cli INFO memory

# Clear Redis if corrupted
redis-cli FLUSHALL
```

### PostgreSQL Connection Issues

**Error**: `PostgreSQL connection refused`
```bash
# Check PostgreSQL container
docker logs intelligent_crawl4ai_postgres

# Test database connection
psql -h localhost -U scraper_user -d intelligent_scraping -c "SELECT 1;"

# Check database initialization
docker exec intelligent_crawl4ai_postgres psql -U scraper_user -d intelligent_scraping -c "\dt"

# Recreate database if needed
docker-compose down
docker volume rm intelligent-crawl4ai-agent_postgres_data
docker-compose up -d postgres
```

## Claude Desktop Integration

### Configuration Issues

**Issue**: Claude Desktop doesn't recognize MCP server
```bash
# Check configuration file location
# macOS: ~/.config/Claude\ Desktop/claude_desktop_config.json
# Windows: %APPDATA%/Claude Desktop/claude_desktop_config.json

# Verify configuration syntax
python -m json.tool ~/.config/Claude\ Desktop/claude_desktop_config.json

# Check Python path in config
which python  # Use this path in config

# Test MCP server manually
python src/mcp_servers/intelligent_orchestrator.py
```

**Error**: `MCP server failed to start`
```bash
# Check MCP server logs
tail -f logs/mcp_server.log

# Test dependencies
python -c "
import sys
sys.path.append('src')
from mcp_servers.intelligent_orchestrator import IntelligentOrchestrator
print('MCP imports successful')
"

# Check environment variables
python -c "
import os
print('OLLAMA_URL:', os.getenv('OLLAMA_URL'))
print('CHROMADB_URL:', os.getenv('CHROMADB_URL'))
"
```

### Communication Issues

**Error**: `Tool execution timeout`
```bash
# Increase timeout in Claude Desktop config
{
  "timeout": 300000,  # 5 minutes
  "retries": 3
}

# Check system load
top
htop

# Reduce concurrent workers
MAX_WORKERS=10
MAX_CONCURRENT_PER_WORKER=5
```

**Error**: `Invalid tool response format`
```bash
# Check MCP server output format
python scripts/test_mcp_tools.py --tool intelligent_scrape --debug

# Validate JSON responses
python -c "
import json
response = '{\"test\": \"response\"}'
json.loads(response)  # Should not raise exception
"
```

## Performance Issues

### Slow Extraction Performance

**Issue**: Extractions taking too long
```bash
# Check strategy selection
grep "strategy_used" logs/agent.log | tail -20

# Enable fast mode
ENABLE_REGEX_FAST_MODE=true
STRATEGY_CONFIDENCE_THRESHOLD=0.6  # Lower threshold

# Optimize browser settings
BROWSER_TIMEOUT=15000  # Reduce timeout
MAX_BROWSER_INSTANCES=30  # Increase browsers
```

**Issue**: High CPU usage
```bash
# Check resource usage
docker stats

# Reduce worker count
MAX_WORKERS=25
MAX_CONCURRENT_PER_WORKER=5

# Enable resource monitoring
ENABLE_MEMORY_MONITORING=true
CPU_THRESHOLD=80
```

### Network Performance

**Issue**: Slow website loading
```bash
# Check network connectivity
ping google.com
traceroute target-website.com

# Adjust timeouts
BROWSER_TIMEOUT=30000
HTTP_TIMEOUT=30
CONNECTION_TIMEOUT=10

# Use faster DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

**Issue**: Rate limiting issues
```bash
# Increase delays between requests
DEFAULT_REQUEST_DELAY=2.0  # 2 seconds
RATE_LIMIT_PER_MINUTE=30   # 30 requests/minute

# Use proxy rotation
ENABLE_PROXY_ROTATION=true
PROXY_LIST="proxy1:port,proxy2:port"
```

## Memory and Resource Problems

### Memory Issues

**Error**: `Out of memory` or container killed
```bash
# Check memory usage
free -h
docker stats --no-stream

# Reduce memory usage
MAX_WORKERS=10
BROWSER_POOL_SIZE=10
CACHE_MAX_SIZE=500

# Enable garbage collection
ENABLE_AGGRESSIVE_GC=true
GC_FREQUENCY=50  # Every 50 operations

# Increase system memory limits
echo 'vm.overcommit_memory=1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

**Issue**: Browser memory leaks
```bash
# Restart browser pools regularly
BROWSER_RESTART_INTERVAL=100  # Every 100 uses

# Use headless mode
BROWSER_HEADLESS=true
DISABLE_IMAGES=true
DISABLE_CSS=true

# Monitor browser memory
docker exec intelligent_crawl4ai_browser_1 ps aux
```

### Disk Space Issues

**Error**: `No space left on device`
```bash
# Check disk usage
df -h
docker system df

# Clean up Docker
docker system prune -f
docker volume prune -f
docker image prune -a -f

# Clean logs
truncate -s 0 logs/*.log
find . -name "*.log" -type f -size +100M -delete

# Configure log rotation
LOG_MAX_SIZE=50MB
LOG_ROTATE_COUNT=5
```

## Strategy and Extraction Issues

### Strategy Selection Problems

**Issue**: Wrong strategy selected
```bash
# Check strategy confidence scores
grep "strategy_confidence" logs/strategy_selection.log

# Force specific strategy for testing
USE_STRATEGY=DirectoryCSSStrategy

# Adjust confidence thresholds
STRATEGY_CONFIDENCE_THRESHOLD=0.8

# Enable strategy debugging
STRATEGY_DEBUG=true
LOG_LEVEL=DEBUG
```

**Issue**: Low extraction quality
```bash
# Check extraction results
grep "confidence_score" logs/extraction.log | tail -20

# Adjust strategy priorities
PREFER_LLM_STRATEGIES=true
LLM_CONFIDENCE_BOOST=0.1

# Enable result validation
ENABLE_RESULT_VALIDATION=true
MIN_FIELDS_REQUIRED=3
```

### CSS Selector Issues

**Error**: `No elements found with selector`
```bash
# Test selectors manually
python scripts/test_selectors.py --url "https://example.com" --selector ".business-name"

# Enable selector debugging
CSS_SELECTOR_DEBUG=true

# Use more generic selectors
FALLBACK_TO_GENERIC=true
GENERIC_SELECTORS="h1,h2,h3,.title,.name"
```

### LLM Strategy Issues

**Error**: `LLM extraction failed`
```bash
# Check Ollama model status
curl http://localhost:11434/api/tags

# Test LLM directly
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.1",
  "prompt": "Extract company information from: <html>...</html>",
  "stream": false
}'

# Increase LLM timeout
LLM_TIMEOUT=120
LLM_MAX_RETRIES=5

# Reduce content size for LLM
LLM_MAX_CONTENT_LENGTH=8000
```

## Database Issues

### SQLite Issues

**Error**: `Database locked`
```bash
# Check for multiple connections
lsof /app/data/sqlite/intelligent_agent.db

# Increase timeout
SQLITE_TIMEOUT=60

# Use WAL mode
sqlite3 /app/data/sqlite/intelligent_agent.db "PRAGMA journal_mode=WAL;"
```

**Error**: `Disk I/O error`
```bash
# Check disk space and permissions
df -h
ls -la /app/data/sqlite/

# Check database integrity
sqlite3 /app/data/sqlite/intelligent_agent.db "PRAGMA integrity_check;"

# Rebuild database if corrupted
mv /app/data/sqlite/intelligent_agent.db /app/data/sqlite/backup.db
python scripts/init_database.py
```

### PostgreSQL Issues

**Error**: `Too many connections`
```bash
# Check current connections
psql -h localhost -U scraper_user -d intelligent_scraping -c "SELECT count(*) FROM pg_stat_activity;"

# Increase connection limit
POSTGRES_POOL_MAX=20
POSTGRES_MAX_CONNECTIONS=200

# Kill idle connections
psql -h localhost -U scraper_user -d intelligent_scraping -c "
SELECT pg_terminate_backend(pid) 
FROM pg_stat_activity 
WHERE state = 'idle' AND state_change < now() - interval '5 minutes';
"
```

## Network and Connectivity

### Browser Pool Issues

**Error**: `Browser session failed`
```bash
# Check browser pool status
curl http://localhost:3001/json/version
curl http://localhost:3002/json/version

# Restart browser pools
docker-compose restart browser-pool-1 browser-pool-2

# Check browser logs
docker logs intelligent_crawl4ai_browser_1
```

**Issue**: Websites blocking requests
```bash
# Enable stealth mode
BROWSER_STEALTH_MODE=true
ROTATE_USER_AGENTS=true

# Use different browser pools
BROWSER_POOL_ROTATION=true

# Add delays
RANDOM_DELAY_MIN=1
RANDOM_DELAY_MAX=5
```

### Proxy and Anti-Detection

**Issue**: IP blocked or rate limited
```bash
# Enable proxy rotation
ENABLE_PROXY_ROTATION=true
PROXY_LIST="proxy1:8080,proxy2:8080"

# Use residential proxies
PROXY_TYPE=residential
PROXY_ROTATION_INTERVAL=10

# Randomize request patterns
RANDOMIZE_DELAYS=true
RANDOMIZE_USER_AGENTS=true
```

## Error Reference

### Common Error Codes

#### E001: Service Connection Failed
**Cause**: Service unreachable or not running
**Solution**: Check service status and restart if needed

#### E002: Authentication Failed
**Cause**: Invalid credentials or tokens
**Solution**: Verify configuration and regenerate tokens

#### E003: Strategy Selection Failed
**Cause**: No suitable strategy found
**Solution**: Lower confidence threshold or add fallback

#### E004: Extraction Timeout
**Cause**: Operation took too long
**Solution**: Increase timeouts or optimize content

#### E005: Resource Exhausted
**Cause**: Out of memory, disk space, or connections
**Solution**: Scale down operations or add resources

#### E006: Invalid Configuration
**Cause**: Configuration error or missing values
**Solution**: Validate configuration and fix errors

### Error Log Patterns

```bash
# Find specific errors
grep "ERROR" logs/agent.log | tail -20
grep "TIMEOUT" logs/agent.log | tail -10
grep "MEMORY" logs/agent.log | tail -5

# Check error frequencies
grep "ERROR" logs/agent.log | cut -d' ' -f4- | sort | uniq -c | sort -nr

# Monitor error rates
tail -f logs/agent.log | grep --line-buffered "ERROR\|WARNING"
```

## Monitoring and Debugging

### Debug Mode Setup

```bash
# Enable comprehensive debugging
DEBUG_MODE=true
LOG_LEVEL=DEBUG
STRATEGY_DEBUG=true
MCP_DEBUG=true
BROWSER_DEBUG=true

# Start in debug mode
docker-compose -f docker-compose.yml -f docker-compose.debug.yml up
```

### Performance Monitoring

```bash
# Check Grafana dashboards
http://localhost:3000

# Key metrics to monitor:
# - Requests per minute
# - Success rates
# - Average response times
# - Error rates
# - Resource usage

# Custom metrics queries (Prometheus)
# Success rate: rate(extraction_success_total[5m])
# Error rate: rate(extraction_errors_total[5m])
# Response time: histogram_quantile(0.95, rate(extraction_duration_bucket[5m]))
```

### Log Analysis

```bash
# Analyze extraction performance
python scripts/analyze_logs.py --file logs/agent.log --metric response_time

# Check strategy effectiveness
python scripts/strategy_analysis.py --days 7

# Generate performance report
python scripts/performance_report.py --output report.html
```

### Real-time Monitoring

```bash
# Monitor system resources
watch -n 1 'docker stats --no-stream'

# Monitor service health
watch -n 5 'python scripts/health_check.py --brief'

# Monitor extraction queue
watch -n 2 'redis-cli LLEN high_volume_jobs'

# Monitor database connections
watch -n 5 'psql -h localhost -U scraper_user -d intelligent_scraping -c "SELECT count(*) FROM pg_stat_activity;"'
```

## Prevention and Best Practices

### Regular Maintenance

```bash
# Daily maintenance script
#!/bin/bash
# Check disk space
df -h | awk '$5 > 80 {print "WARNING: " $0}'

# Clean old logs
find logs/ -name "*.log" -mtime +7 -delete

# Database maintenance
python scripts/db_maintenance.py --vacuum --analyze

# Check service health
python scripts/health_check.py --email-alerts
```

### Monitoring Setup

```bash
# Set up log rotation
cat > /etc/logrotate.d/intelligent-crawl4ai << EOF
/app/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 appuser appuser
}
EOF
```

### Backup Strategy

```bash
# Backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)

# Backup databases
pg_dump -h localhost -U scraper_user intelligent_scraping > backup_${DATE}.sql
cp /app/data/sqlite/intelligent_agent.db backup_sqlite_${DATE}.db

# Backup configuration
tar -czf config_backup_${DATE}.tar.gz config/ .env

# Backup ChromaDB
docker exec intelligent_crawl4ai_chromadb tar -czf - /chroma/chroma > chromadb_backup_${DATE}.tar.gz
```

## Getting Additional Help

### Debug Information Collection

When reporting issues, collect this information:

```bash
# System information
uname -a
docker --version
docker-compose --version
python --version

# Service status
docker-compose ps
python scripts/health_check.py --verbose

# Recent logs
tail -100 logs/agent.log
tail -50 logs/mcp_server.log
tail -50 logs/strategy_selection.log

# Configuration
cat .env | grep -v PASSWORD | grep -v TOKEN
cat config/claude_desktop_mcp.json
```

### Support Channels

1. **Documentation**: Check other guides in [docs/](.)
2. **GitHub Issues**: Report bugs with debug information
3. **Discussions**: Ask questions in GitHub Discussions
4. **Performance Issues**: See [high_volume.md](high_volume.md)
5. **Configuration Help**: Review [configuration.md](configuration.md)

### Emergency Recovery

```bash
# Complete system reset (nuclear option)
docker-compose down -v
docker system prune -a -f
docker volume prune -f
rm -rf logs/* data/*
git checkout -- .
./scripts/setup.sh
```

This troubleshooting guide should help you resolve most common issues. For persistent problems, gather the debug information above and report the issue with as much detail as possible.