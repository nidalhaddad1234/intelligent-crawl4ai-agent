#!/bin/bash
# =============================================================================
# Intelligent Crawl4AI Agent - Docker Entrypoint Script
# =============================================================================
# Handles initialization, health checks, and graceful startup/shutdown

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

# =============================================================================
# Pre-flight Checks
# =============================================================================

log "🚀 Starting Intelligent Crawl4AI Agent"
log "📦 Environment: ${APP_ENV:-production}"
log "🔧 Working directory: $(pwd)"
log "👤 Running as: $(whoami)"

# Check if running as root (security warning)
if [ "$(id -u)" = "0" ]; then
    log_warning "Running as root user. Consider using a non-root user for security."
fi

# Validate required environment variables
check_env_vars() {
    local required_vars=(
        "MCP_SERVER_HOST"
        "MCP_SERVER_PORT"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
}

# =============================================================================
# Database Initialization
# =============================================================================

init_database() {
    log "📊 Initializing database..."
    
    # Auto-detect database type
    if [ "${DATABASE_TYPE}" = "auto" ]; then
        if [ -n "${POSTGRES_URL}" ] && [ "${POSTGRES_URL}" != "" ]; then
            log "🐘 PostgreSQL detected - using distributed mode"
            export DATABASE_TYPE="postgresql"
        else
            log "🗄️  Using SQLite - standalone mode"
            export DATABASE_TYPE="sqlite"
        fi
    fi
    
    # Create SQLite directory if needed
    if [ "${DATABASE_TYPE}" = "sqlite" ]; then
        local sqlite_dir=$(dirname "${SQLITE_PATH}")
        mkdir -p "${sqlite_dir}"
        log "✅ SQLite directory ready: ${sqlite_dir}"
    fi
    
    # Wait for PostgreSQL if using distributed mode
    if [ "${DATABASE_TYPE}" = "postgresql" ] && [ -n "${POSTGRES_URL}" ]; then
        log "⏳ Waiting for PostgreSQL to be ready..."
        python -c "
import asyncio
import asyncpg
import os
import sys
from urllib.parse import urlparse

async def wait_for_postgres():
    url = os.environ.get('POSTGRES_URL')
    if not url:
        return True
        
    parsed = urlparse(url)
    max_attempts = 30
    
    for attempt in range(max_attempts):
        try:
            conn = await asyncpg.connect(
                host=parsed.hostname,
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path[1:] if parsed.path else 'postgres',
                timeout=5
            )
            await conn.close()
            print(f'✅ PostgreSQL connection successful (attempt {attempt + 1})')
            return True
        except Exception as e:
            if attempt < max_attempts - 1:
                print(f'⏳ PostgreSQL not ready (attempt {attempt + 1}/{max_attempts}): {e}')
                await asyncio.sleep(2)
            else:
                print(f'❌ PostgreSQL connection failed after {max_attempts} attempts: {e}')
                return False
    return False

if not asyncio.run(wait_for_postgres()):
    sys.exit(1)
"
        if [ $? -ne 0 ]; then
            log_error "Failed to connect to PostgreSQL"
            exit 1
        fi
    fi
}

# =============================================================================
# AI Services Initialization
# =============================================================================

init_ai_services() {
    log "🤖 Initializing AI services..."
    
    # Wait for Ollama
    if [ -n "${OLLAMA_URL}" ]; then
        log "⏳ Waiting for Ollama to be ready..."
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if curl -s "${OLLAMA_URL}/api/tags" > /dev/null 2>&1; then
                log_success "Ollama is ready"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                log_warning "Ollama not available after ${max_attempts} attempts. Continuing anyway..."
                break
            fi
            
            log "⏳ Ollama not ready (attempt ${attempt}/${max_attempts})"
            sleep 2
            ((attempt++))
        done
    fi
    
    # Wait for ChromaDB
    if [ -n "${CHROMADB_URL}" ]; then
        log "⏳ Waiting for ChromaDB to be ready..."
        local max_attempts=30
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            local headers=""
            if [ -n "${CHROMADB_TOKEN}" ]; then
                headers="-H X-Chroma-Token:${CHROMADB_TOKEN}"
            fi
            
            if curl -s $headers "${CHROMADB_URL}/api/v1/heartbeat" > /dev/null 2>&1; then
                log_success "ChromaDB is ready"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                log_warning "ChromaDB not available after ${max_attempts} attempts. Continuing anyway..."
                break
            fi
            
            log "⏳ ChromaDB not ready (attempt ${attempt}/${max_attempts})"
            sleep 2
            ((attempt++))
        done
    fi
    
    # Wait for Redis (optional)
    if [ -n "${REDIS_URL}" ]; then
        log "⏳ Waiting for Redis to be ready..."
        local max_attempts=15
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if python -c "
import redis
import sys
from urllib.parse import urlparse

try:
    r = redis.from_url('${REDIS_URL}', decode_responses=True, socket_timeout=5)
    r.ping()
    print('✅ Redis connection successful')
    sys.exit(0)
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; then
                log_success "Redis is ready"
                break
            fi
            
            if [ $attempt -eq $max_attempts ]; then
                log_warning "Redis not available after ${max_attempts} attempts. Continuing without Redis..."
                break
            fi
            
            log "⏳ Redis not ready (attempt ${attempt}/${max_attempts})"
            sleep 1
            ((attempt++))
        done
    fi
}

# =============================================================================
# Graceful Shutdown Handler
# =============================================================================

shutdown_handler() {
    log "🛑 Received shutdown signal"
    log "🧹 Cleaning up resources..."
    
    # Kill background processes
    jobs -p | xargs -r kill
    
    # Clean up temporary files
    find /tmp -name "intelligent_crawl4ai_*" -type f -delete 2>/dev/null || true
    
    log_success "Cleanup completed"
    exit 0
}

# Set up signal handlers
trap shutdown_handler SIGTERM SIGINT

# =============================================================================
# Main Application Startup
# =============================================================================

start_application() {
    local mode="${1:-mcp-server}"
    
    log "🎯 Starting application in mode: ${mode}"
    
    case "${mode}" in
        "mcp-server")
            log "🔌 Starting MCP Server..."
            exec python -m src.mcp_servers.intelligent_orchestrator \
                --host "${MCP_SERVER_HOST}" \
                --port "${MCP_SERVER_PORT}" \
                ${APP_ENV:+--env "${APP_ENV}"} \
                ${LOG_LEVEL:+--log-level "${LOG_LEVEL}"}
            ;;
            
        "high-volume-worker")
            log "⚡ Starting High-Volume Worker..."
            exec python -m src.agents.high_volume_executor \
                --max-workers "${MAX_WORKERS:-10}" \
                --redis-url "${REDIS_URL}" \
                ${LOG_LEVEL:+--log-level "${LOG_LEVEL}"}
            ;;
            
        "strategy-test")
            log "🧪 Running Strategy Tests..."
            exec python -m pytest src/tests/ -v \
                ${LOG_LEVEL:+--log-cli-level="${LOG_LEVEL}"}
            ;;
            
        "model-setup")
            log "📥 Setting up AI models..."
            exec python scripts/model_setup.py \
                --ollama-url "${OLLAMA_URL}"
            ;;
            
        "shell")
            log "🐚 Starting interactive shell..."
            exec /bin/bash
            ;;
            
        "debug")
            log "🐛 Starting in debug mode..."
            python -m debugpy --listen 0.0.0.0:5678 --wait-for-client \
                -m src.mcp_servers.intelligent_orchestrator \
                --host "${MCP_SERVER_HOST}" \
                --port "${MCP_SERVER_PORT}" \
                --debug
            ;;
            
        *)
            log_error "Unknown mode: ${mode}"
            log "Available modes: mcp-server, high-volume-worker, strategy-test, model-setup, shell, debug"
            exit 1
            ;;
    esac
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Validate environment
    check_env_vars
    
    # Initialize components
    init_database
    init_ai_services
    
    log_success "🎉 Initialization completed successfully!"
    log "🎯 Starting main application..."
    
    # Start the application
    start_application "$@"
}

# Execute main function with all arguments
main "$@"
