# Configuration Guide

## Overview

The Intelligent Crawl4AI Agent is highly configurable to support various deployment scenarios, from local development to high-volume production environments. This guide covers all configuration options and best practices.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Claude Desktop Configuration](#claude-desktop-configuration)
- [Docker Configuration](#docker-configuration)
- [Database Configuration](#database-configuration)
- [AI Services Configuration](#ai-services-configuration)
- [Strategy Configuration](#strategy-configuration)
- [Performance Tuning](#performance-tuning)
- [Security Configuration](#security-configuration)
- [Monitoring Configuration](#monitoring-configuration)

## Environment Variables

### Core Application Settings

```bash
# Application Environment
APP_ENV=production                    # production, development, testing
LOG_LEVEL=INFO                       # DEBUG, INFO, WARNING, ERROR
DEBUG_MODE=false                     # Enable debug features
PYTHONUNBUFFERED=1                   # Python output buffering

# Server Configuration
MCP_SERVER_HOST=0.0.0.0             # MCP server bind address
MCP_SERVER_PORT=8811                # MCP server port
MCP_TIMEOUT=300                     # Request timeout in seconds
MAX_CONCURRENT_REQUESTS=100         # Max concurrent requests
RATE_LIMIT_PER_MINUTE=1000         # Rate limiting
```

### Database Configuration

#### SQLite (Default for Standalone)
```bash
DATABASE_TYPE=sqlite                 # sqlite, postgresql, auto
SQLITE_PATH=/app/data/sqlite/intelligent_agent.db
SQLITE_POOL_SIZE=20                 # Connection pool size
SQLITE_TIMEOUT=30                   # Query timeout
```

#### PostgreSQL (Recommended for Production)
```bash
DATABASE_TYPE=postgresql
POSTGRES_URL=postgresql://scraper_user:secure_password_123@postgres:5432/intelligent_scraping
POSTGRES_POOL_MIN=5                 # Minimum connections
POSTGRES_POOL_MAX=50                # Maximum connections
POSTGRES_TIMEOUT=60                 # Connection timeout
```

### AI Services Configuration

#### Ollama Settings
```bash
OLLAMA_URL=http://localhost:11434    # Ollama API endpoint
OLLAMA_MODEL_LLM=llama3.1           # Primary LLM model
OLLAMA_MODEL_EMBEDDING=nomic-embed-text  # Embedding model
OLLAMA_TIMEOUT=120                  # Request timeout
OLLAMA_MAX_RETRIES=3                # Retry attempts
OLLAMA_CONCURRENT_REQUESTS=10       # Max concurrent requests
```

#### ChromaDB Settings
```bash
CHROMADB_URL=http://localhost:8000   # ChromaDB endpoint
CHROMADB_TOKEN=test-token           # Authentication token
CHROMADB_COLLECTION_PREFIX=intelligent_agent  # Collection naming
CHROMADB_MAX_BATCH_SIZE=100         # Batch insert size
CHROMADB_TIMEOUT=60                 # Query timeout
```

### Browser and Scraping Configuration

```bash
# Browser Settings
BROWSER_HEADLESS=true               # Run browsers headless
BROWSER_TIMEOUT=30000              # Page load timeout (ms)
MAX_BROWSER_INSTANCES=20           # Max concurrent browsers
BROWSER_POOL_URLS=http://browser-pool-1:3000,http://browser-pool-2:3000

# Scraping Limits
MAX_WORKERS=50                     # High-volume workers
MAX_CONCURRENT_PER_WORKER=10       # URLs per worker
DEFAULT_REQUEST_DELAY=1.0          # Delay between requests
MAX_RETRIES=3                      # Failed request retries
```

### Cache and Queue Configuration

```bash
# Redis Configuration
REDIS_URL=redis://localhost:6379    # Redis connection
REDIS_MAX_CONNECTIONS=100          # Connection pool size
CACHE_TTL=3600                     # Cache time-to-live
QUEUE_BATCH_SIZE=100               # Job batch size

# Session Management
SESSION_TIMEOUT=1800               # Session timeout (seconds)
SESSION_CLEANUP_INTERVAL=300      # Cleanup interval
```

## Claude Desktop Configuration

### Basic Configuration

Create or update `~/.config/Claude Desktop/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "intelligent_crawl4ai_agent": {
      "command": "python",
      "args": ["/path/to/intelligent-crawl4ai-agent/src/mcp_servers/intelligent_orchestrator.py"],
      "env": {
        "OLLAMA_URL": "http://localhost:11434",
        "CHROMADB_URL": "http://localhost:8000",
        "REDIS_URL": "redis://localhost:6379",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Advanced Configuration

For production deployments with custom settings:

```json
{
  "mcpServers": {
    "intelligent_crawl4ai_agent": {
      "command": "python",
      "args": ["/path/to/intelligent-crawl4ai-agent/src/mcp_servers/intelligent_orchestrator.py"],
      "env": {
        "OLLAMA_URL": "http://localhost:11434",
        "CHROMADB_URL": "http://localhost:8000",
        "REDIS_URL": "redis://localhost:6379",
        "POSTGRES_URL": "postgresql://user:pass@localhost:5432/scraping",
        "LOG_LEVEL": "INFO",
        "MAX_CONCURRENT_REQUESTS": "50",
        "RATE_LIMIT_PER_MINUTE": "500",
        "ENABLE_METRICS": "true",
        "BROWSER_POOL_URLS": "http://localhost:3001,http://localhost:3002"
      },
      "timeout": 300000,
      "retries": 3
    }
  }
}
```

## Docker Configuration

### Environment File Setup

Create `.env` file in project root:

```bash
# Copy from template
cp .env.example .env

# Edit with your settings
nano .env
```

### Docker Compose Overrides

For custom deployments, create `docker-compose.override.yml`:

```yaml
version: '3.9'

services:
  intelligent-agent:
    environment:
      - MAX_WORKERS=100
      - LOG_LEVEL=DEBUG
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4.0'

  ollama:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### Production Docker Settings

```yaml
# Production optimizations
services:
  intelligent-agent:
    restart: always
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

## Strategy Configuration

### Default Strategy Settings

```bash
# Strategy Selection
DEFAULT_STRATEGY=smart_hybrid        # Default extraction strategy
STRATEGY_CONFIDENCE_THRESHOLD=0.7   # Minimum confidence required
ENABLE_STRATEGY_LEARNING=true       # Learn from results
ENABLE_REGEX_FAST_MODE=true         # Fast regex extraction

# Strategy Timeouts
CSS_STRATEGY_TIMEOUT=15             # CSS extraction timeout
LLM_STRATEGY_TIMEOUT=60             # LLM extraction timeout
HYBRID_STRATEGY_TIMEOUT=45          # Hybrid strategy timeout
```

### Custom Strategy Configuration

Create `config/strategies.json`:

```json
{
  "custom_strategies": {
    "linkedin_profile": {
      "strategy_type": "css",
      "selectors": {
        "name": "h1.text-heading-xlarge",
        "title": ".text-body-medium.break-words",
        "company": ".inline-show-more-text"
      },
      "confidence_threshold": 0.8
    },
    "ecommerce_products": {
      "strategy_type": "hybrid",
      "css_selectors": {
        "title": ".product-title, h1",
        "price": ".price, .cost"
      },
      "llm_fallback": true,
      "confidence_threshold": 0.7
    }
  }
}
```

## Performance Tuning

### High-Volume Configuration

For processing thousands of URLs:

```bash
# Worker Configuration
MAX_WORKERS=100                     # Increase workers
MAX_CONCURRENT_PER_WORKER=20       # URLs per worker
WORKER_BATCH_SIZE=200              # Batch size

# Database Optimization
POSTGRES_POOL_MAX=100              # Increase DB pool
REDIS_MAX_CONNECTIONS=200          # Increase Redis pool

# Browser Optimization
MAX_BROWSER_INSTANCES=50           # More browsers
BROWSER_TIMEOUT=20000              # Faster timeout
```

### Memory Optimization

```bash
# Memory Limits
MAX_MEMORY_PER_WORKER=512M         # Worker memory limit
GARBAGE_COLLECTION_INTERVAL=100    # GC frequency
CACHE_MAX_SIZE=1000                # Cache size limit

# Database Connection Pooling
DB_POOL_RECYCLE=3600              # Recycle connections
DB_POOL_PRE_PING=true             # Validate connections
```

### Network Optimization

```bash
# Connection Settings
HTTP_TIMEOUT=30                    # HTTP request timeout
HTTP_MAX_CONNECTIONS=100           # Max HTTP connections
HTTP_KEEPALIVE=true               # Keep connections alive

# Rate Limiting
GLOBAL_RATE_LIMIT=1000            # Global requests/minute
PER_DOMAIN_RATE_LIMIT=60          # Per domain limit
RATE_LIMIT_BURST=20               # Burst allowance
```

## Security Configuration

### Authentication Settings

```bash
# API Security
API_KEY_REQUIRED=true              # Require API keys
API_KEY_HEADER=X-API-Key           # Header name
JWT_SECRET_KEY=your-secret-key     # JWT signing key
JWT_EXPIRATION=3600                # Token expiration

# CORS Configuration
CORS_ORIGINS=["http://localhost:3000"]  # Allowed origins
CORS_CREDENTIALS=true              # Allow credentials
```

### Data Protection

```bash
# Encryption
ENCRYPT_SENSITIVE_DATA=true        # Encrypt credentials
ENCRYPTION_KEY=your-encryption-key # Data encryption key

# Data Retention
DATA_RETENTION_DAYS=30             # Keep data for days
AUTO_CLEANUP_ENABLED=true          # Automatic cleanup
ANONYMIZE_LOGS=true                # Remove sensitive info
```

## Monitoring Configuration

### Metrics and Logging

```bash
# Metrics
ENABLE_METRICS=true                # Enable Prometheus metrics
METRICS_PORT=8812                  # Metrics endpoint port
METRICS_PATH=/metrics              # Metrics URL path

# Logging
LOG_FORMAT=json                    # Log format (json, text)
LOG_FILE=/app/logs/agent.log       # Log file path
LOG_ROTATION=true                  # Enable log rotation
LOG_MAX_SIZE=100MB                 # Max log file size
```

### Health Checks

```bash
# Health Check Configuration
HEALTH_CHECK_ENABLED=true          # Enable health checks
HEALTH_CHECK_INTERVAL=30           # Check interval (seconds)
HEALTH_CHECK_TIMEOUT=10            # Check timeout
HEALTH_CHECK_ENDPOINT=/health      # Health check URL
```

### Monitoring Integrations

```bash
# Prometheus
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
PROMETHEUS_RETENTION=15d

# Grafana
GRAFANA_ENABLED=true
GRAFANA_PORT=3000
GRAFANA_ADMIN_PASSWORD=secure_password

# Alerting
ALERT_WEBHOOK_URL=https://hooks.slack.com/...
ALERT_ON_ERROR_RATE=0.1           # Alert if error rate > 10%
ALERT_ON_MEMORY_USAGE=0.8         # Alert if memory > 80%
```

## Configuration Examples

### Development Environment

```bash
# .env.development
APP_ENV=development
LOG_LEVEL=DEBUG
DEBUG_MODE=true
MAX_WORKERS=5
ENABLE_METRICS=false
BROWSER_HEADLESS=false
```

### Testing Environment

```bash
# .env.testing
APP_ENV=testing
LOG_LEVEL=WARNING
DATABASE_TYPE=sqlite
SQLITE_PATH=:memory:
ENABLE_STRATEGY_LEARNING=false
```

### Production Environment

```bash
# .env.production
APP_ENV=production
LOG_LEVEL=INFO
DATABASE_TYPE=postgresql
MAX_WORKERS=100
ENABLE_METRICS=true
HEALTH_CHECK_ENABLED=true
ENCRYPT_SENSITIVE_DATA=true
```

## Configuration Validation

### Validation Script

Use the included validation script:

```bash
python scripts/validate_config.py --env-file .env
```

### Required Settings Check

Minimum required configuration:

```bash
# Essential settings that must be configured
OLLAMA_URL          # AI service endpoint
CHROMADB_URL        # Vector database
DATABASE_TYPE       # Database choice
```

## Best Practices

### Security Best Practices

1. **Never commit secrets** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate API keys** regularly
4. **Enable encryption** for production
5. **Use least privilege** access

### Performance Best Practices

1. **Monitor resource usage** regularly
2. **Tune worker counts** based on load
3. **Use database pooling** for high volume
4. **Enable caching** where appropriate
5. **Set appropriate timeouts**

### Operational Best Practices

1. **Use configuration management** tools
2. **Validate configuration** before deployment
3. **Monitor configuration drift**
4. **Document custom settings**
5. **Test configuration changes**

## Troubleshooting Configuration

### Common Issues

**Service Connection Failures**
```bash
# Check service connectivity
curl http://localhost:11434/api/tags        # Ollama
curl http://localhost:8000/api/v1/heartbeat # ChromaDB
redis-cli ping                              # Redis
```

**Performance Issues**
```bash
# Check resource usage
docker stats
htop
df -h

# Adjust worker settings
MAX_WORKERS=25  # Reduce if high CPU
MAX_CONCURRENT_PER_WORKER=5  # Reduce if high memory
```

**Memory Issues**
```bash
# Enable memory monitoring
ENABLE_MEMORY_MONITORING=true
MEMORY_WARNING_THRESHOLD=0.8
MEMORY_CRITICAL_THRESHOLD=0.9
```

## Getting Help

- **Configuration Issues**: Check [troubleshooting.md](troubleshooting.md)
- **Performance Tuning**: See [high_volume.md](high_volume.md)
- **Strategy Configuration**: Read [strategies.md](strategies.md)
- **API Documentation**: Review [api.md](api.md)