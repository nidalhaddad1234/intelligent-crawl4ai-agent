#!/bin/bash
# PostgreSQL troubleshooting script

echo "🔍 Checking PostgreSQL container..."

# Check if container exists
if docker ps -a | grep -q intelligent_crawl4ai_postgres; then
    echo "✅ Container exists"
    
    # Check container status
    STATUS=$(docker inspect intelligent_crawl4ai_postgres --format='{{.State.Status}}')
    echo "📊 Status: $STATUS"
    
    # Show last 20 lines of logs
    echo ""
    echo "📋 Last 20 lines of PostgreSQL logs:"
    echo "===================================="
    docker logs --tail 20 intelligent_crawl4ai_postgres
    echo "===================================="
    
    # Try to connect
    echo ""
    echo "🔌 Testing connection..."
    docker exec intelligent_crawl4ai_postgres pg_isready -U scraper_user -d intelligent_scraping || echo "❌ Connection failed"
    
else
    echo "❌ Container not found"
fi

echo ""
echo "🛠️ Suggested fixes:"
echo "1. Remove old data: docker volume rm intelligent-crawl4ai-agent_postgres_data"
echo "2. Use debug compose: docker compose -f docker/compose/docker-compose.debug.yml up -d"
echo "3. Check port 5432: netstat -tlnp | grep 5432"
