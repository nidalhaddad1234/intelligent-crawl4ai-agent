#!/bin/bash
# Fix for Web UI out of memory issue

echo "🔧 Fixing Web UI startup issues..."

# Stop everything
echo "🛑 Stopping all containers..."
docker compose -f docker/compose/docker-compose.local-full.yml down

# Remove the problematic web UI container
docker rm -f intelligent_crawl4ai_web_ui 2>/dev/null

# Start with minimal setup
echo "🚀 Starting with minimal configuration..."
docker compose -f docker/compose/docker-compose.minimal.yml up -d

echo "⏳ Waiting for services to start..."
sleep 10

# Check status
echo ""
echo "📊 Service Status:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "🔍 Checking Web UI..."
curl -s http://localhost:8888/health && echo "✅ Web UI is responding!" || echo "❌ Web UI not ready yet"

echo ""
echo "📋 To view logs: docker logs -f intelligent_crawl4ai_web_ui"
echo "🌐 Access Web UI at: http://localhost:8888"
