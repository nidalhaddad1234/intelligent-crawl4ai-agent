#!/bin/bash
# Check Grafana dashboards

echo "🔍 Checking Grafana Dashboards..."

# For test Grafana on port 3003
echo -e "\n📊 Test Grafana (port 3003):"
curl -s http://localhost:3003/api/dashboards/db 2>/dev/null | grep -q "message" && echo "No dashboards found" || echo "Dashboards available"

# Try to list dashboards
echo -e "\n📋 Available Dashboards:"
curl -s http://localhost:3003/api/search | jq -r '.[] | "\(.title) - \(.url)"' 2>/dev/null || echo "No dashboards or API not accessible"

echo -e "\n💡 To add dashboards:"
echo "1. Go to http://localhost:3003"
echo "2. Click + → Import"
echo "3. Upload the JSON file from: docker/grafana/dashboards/crawl4ai-dashboard.json"
echo ""
echo "Or run a complete Grafana with dashboards:"
echo "docker compose -f docker/compose/grafana-complete.yml up -d"
