#!/bin/bash
# Quick log checker for Intelligent Crawl4AI

echo "🔍 Checking Container Status..."
echo "================================"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "intelligent_crawl4ai|grafana_test"

echo -e "\n📋 Recent Web UI Logs:"
echo "====================="
docker logs --tail 10 intelligent_crawl4ai_web_ui

echo -e "\n❌ Recent Errors (if any):"
echo "========================="
docker logs intelligent_crawl4ai_web_ui 2>&1 | grep -i error | tail -5 || echo "No errors found!"

echo -e "\n🌐 Service Health:"
echo "=================="
curl -s http://localhost:8888/health | jq . || echo "Web UI not responding"

echo -e "\n💡 Tip: Use 'docker logs -f <container_name>' to follow logs in real-time"
