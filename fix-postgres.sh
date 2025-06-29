#!/bin/bash
# Quick fix for PostgreSQL issues

echo "🧹 Cleaning up and restarting..."

# Stop all containers
echo "🛑 Stopping containers..."
docker compose -f docker/compose/docker-compose.local-full.yml down

# Remove postgres volume
echo "🗑️ Removing PostgreSQL volume..."
docker volume rm intelligent-crawl4ai-agent_postgres_data 2>/dev/null || true

# Remove postgres container completely
docker rm -f intelligent_crawl4ai_postgres 2>/dev/null || true

# Start just the core services first
echo "🚀 Starting core services..."
docker compose -f docker/compose/docker-compose.debug.yml up -d

# Wait for postgres to be ready
echo "⏳ Waiting for PostgreSQL to initialize..."
sleep 10

# Check postgres status
echo "🔍 Checking PostgreSQL status..."
docker logs intelligent_crawl4ai_postgres --tail 20

# Test connection
echo "🔌 Testing connection..."
docker exec intelligent_crawl4ai_postgres pg_isready -U scraper_user -d intelligent_scraping

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL is ready!"
    echo ""
    echo "Now you can access:"
    echo "  - Web UI: http://localhost:8888"
    echo "  - PostgreSQL: localhost:5432"
else
    echo "❌ PostgreSQL is still not ready. Check logs with:"
    echo "  docker logs intelligent_crawl4ai_postgres"
fi
