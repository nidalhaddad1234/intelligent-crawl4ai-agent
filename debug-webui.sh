#!/bin/bash
# Debug Web UI container

echo "🔍 Checking Web UI status..."

# Check if container exists
CONTAINER_STATUS=$(docker ps -a --filter name=intelligent_crawl4ai_web_ui --format "{{.Status}}")
echo "Container status: $CONTAINER_STATUS"

# Show last 50 lines of logs
echo ""
echo "📋 Web UI logs:"
echo "============================================"
docker logs --tail 50 intelligent_crawl4ai_web_ui
echo "============================================"

# Check if port 8888 is being used
echo ""
echo "🔌 Checking port 8888..."
netstat -tlnp 2>/dev/null | grep 8888 || echo "Port 8888 not in use"

# Try to curl the endpoint
echo ""
echo "🌐 Testing connection..."
curl -s http://localhost:8888/health || echo "❌ Cannot connect to Web UI"

# Check running processes in container
echo ""
echo "📊 Processes in container:"
docker exec intelligent_crawl4ai_web_ui ps aux 2>/dev/null || echo "Cannot check processes"
