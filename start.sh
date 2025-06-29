#!/bin/bash
# Quick start script for Intelligent Crawl4AI Agent

echo "🚀 Starting Intelligent Crawl4AI Agent..."

# Check if Ollama is running
if ! curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo "⚠️  Ollama is not running. Please start it first:"
    echo "    ollama serve"
    echo "    ollama pull deepseek-coder:1.3b"
    exit 1
fi

# Start all services
echo "📦 Starting all services..."
docker compose -f docker/compose/docker-compose.local-full.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to initialize..."
sleep 20

# Check status
echo "📊 Service Status:"
docker compose -f docker/compose/docker-compose.local-full.yml ps

echo ""
echo "✅ Intelligent Crawl4AI Agent is ready!"
echo ""
echo "🌐 Access the Web UI at: http://localhost:8888"
echo "📊 View metrics at: http://localhost:3000 (admin/admin123)"
echo ""
echo "📋 To view logs: docker compose -f docker/compose/docker-compose.local-full.yml logs -f"
echo "🛑 To stop: docker compose -f docker/compose/docker-compose.local-full.yml down"
