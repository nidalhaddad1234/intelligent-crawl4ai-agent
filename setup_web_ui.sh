#!/bin/bash

# Web UI Setup Script for Intelligent Crawl4AI Agent
# This script sets up the ChatGPT-like web interface

set -e  # Exit on any error

echo "🌐 Setting up Web UI for Intelligent Crawl4AI Agent..."
echo "=================================================="

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: Please run this script from the intelligent-crawl4ai-agent root directory"
    exit 1
fi

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p static
mkdir -p docker
mkdir -p logs

echo "✅ Directory structure created"

# Create the Dockerfile for Web UI
echo "🐳 Creating Dockerfile for Web UI..."
cat > docker/Dockerfile.web-ui << 'EOF'
# Dockerfile for Web UI Server
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-webui.txt /app/
RUN pip install --no-cache-dir -r requirements-webui.txt

# Copy application code
COPY src/ /app/src/
COPY web_ui_server.py /app/
COPY static/ /app/static/

# Create necessary directories
RUN mkdir -p /app/logs /app/data

# Set environment variables
ENV PYTHONPATH="/app:/app/src"
ENV PYTHONUNBUFFERED=1
ENV WEB_HOST=0.0.0.0
ENV WEB_PORT=8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Run the web UI server
CMD ["python", "web_ui_server.py"]
EOF

echo "✅ Dockerfile created"

# Create requirements file for Web UI
echo "📦 Creating requirements-webui.txt..."
cat > requirements-webui.txt << 'EOF'
# Web UI Server Requirements
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0

# Core dependencies (shared with main agent)
pydantic>=2.5.0
python-dotenv>=1.0.0

# Database support (shared)
aiosqlite>=0.19.0
asyncpg>=0.29.0

# AI and ML (shared)
ollama>=0.1.0
chromadb>=0.4.0

# Utilities
loguru>=0.7.0
psutil>=5.9.0

# Optional for development
pytest>=7.4.0
pytest-asyncio>=0.21.0
EOF

echo "✅ Web UI requirements created"

# Backup existing docker-compose.yml
echo "💾 Backing up existing docker-compose.yml..."
cp docker-compose.yml docker-compose.yml.backup
echo "✅ Backup created as docker-compose.yml.backup"

echo ""
echo "📝 NEXT STEPS:"
echo "============="
echo "1. Copy web_ui_server.py from the artifacts"
echo "2. Copy static/index.html from the artifacts"
echo "3. Add web-ui service to docker-compose.yml"
echo "4. Run: docker-compose up -d"
echo "5. Access: http://localhost:8888"
echo ""
echo "🎉 Web UI setup files created successfully!"
