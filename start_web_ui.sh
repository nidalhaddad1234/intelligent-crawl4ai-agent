#!/bin/bash

# Startup script for Intelligent Crawl4AI Agent with Web UI
# This script starts all services including the new ChatGPT-like web interface

set -e  # Exit on any error

echo "🚀 Starting Intelligent Crawl4AI Agent with Web UI"
echo "=================================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

echo "🔧 Checking configuration..."

# Check if required files exist
if [ ! -f "web_ui_server.py" ]; then
    echo "❌ web_ui_server.py not found. Please make sure it's in the project root."
    exit 1
fi

if [ ! -f "static/index.html" ]; then
    echo "❌ static/index.html not found. Please make sure the static directory exists."
    exit 1
fi

if [ ! -f "docker/Dockerfile.web-ui" ]; then
    echo "❌ docker/Dockerfile.web-ui not found. Please run setup_web_ui.sh first."
    exit 1
fi

echo "✅ Configuration looks good"

# Build and start all services
echo "🏗️  Building and starting services..."
docker-compose up -d --build

echo ""
echo "⏳ Waiting for services to start..."
sleep 15

# Check service health
echo "🔍 Checking service health..."
echo ""

# Function to check service health
check_service() {
    local service=$1
    local port=$2
    local name=$3
    
    if curl -s -f "http://localhost:$port/health" > /dev/null 2>&1 || \
       curl -s -f "http://localhost:$port" > /dev/null 2>&1 || \
       docker-compose ps $service | grep "Up" > /dev/null; then
        echo "✅ $name is running"
        return 0
    else
        echo "⚠️  $name may not be ready yet"
        return 1
    fi
}

# Check each service
check_service "web-ui" "8888" "Web UI"
check_service "chromadb" "8000" "ChromaDB"
check_service "ollama" "11434" "Ollama"
check_service "redis" "6379" "Redis"
check_service "postgres" "5432" "PostgreSQL"
check_service "grafana" "3000" "Grafana"

echo ""
echo "📊 Service Status:"
docker-compose ps

echo ""
echo "🎉 Intelligent Crawl4AI Agent is now running!"
echo "============================================="
echo ""
echo "🌐 **Web UI (ChatGPT-like Interface)**: http://localhost:8888"
echo "   • Chat with your AI scraping assistant"
echo "   • Submit scraping jobs through conversation"
echo "   • Real-time WebSocket communication"
echo ""
echo "📊 **Monitoring & Management:**"
echo "   • Grafana Dashboard: http://localhost:3000 (admin/admin123)"
echo "   • Prometheus Metrics: http://localhost:9090"
echo "   • ChromaDB: http://localhost:8000"
echo ""
echo "🤖 **Backend Services:**"
echo "   • MCP Server: localhost:8811"
echo "   • Ollama AI: http://localhost:11434"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo ""
echo "🧪 **Test the Web UI:**"
echo "   python test_web_ui.py"
echo ""
echo "📝 **Example Usage:**"
echo "   1. Open http://localhost:8888"
echo "   2. Ask: 'What can you help me with?'"
echo "   3. Try: 'Scrape data from https://example.com'"
echo "   4. Check: 'Show me the system status'"
echo ""
echo "🛑 **To stop all services:**"
echo "   docker-compose down"
echo ""
echo "📋 **To view logs:**"
echo "   docker-compose logs -f web-ui       # Web UI logs"
echo "   docker-compose logs -f intelligent-agent  # Agent logs"
echo "   docker-compose logs                 # All logs"
echo ""
echo "🔧 **Architecture:**"
echo "   Browser → Web UI (FastAPI) → AI Agent → Ollama/ChromaDB"
echo "           ↳ Claude Desktop → MCP Server → AI Agent"
echo ""

# Optional: Run a quick test
read -p "🧪 Would you like to run a quick test of the Web UI? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🧪 Running Web UI tests..."
    python test_web_ui.py
fi

echo ""
echo "🎯 **Your intelligent scraping agent is ready!**"
echo "   Visit http://localhost:8888 to start chatting with your AI assistant."
