#!/bin/bash
# Check Grafana on port 3000

echo "🔍 Checking Grafana on port 3000..."

# Check if it's running
if curl -s http://localhost:3000 > /dev/null; then
    echo "✅ Grafana is running on port 3000"
else
    echo "❌ Grafana not responding on port 3000"
fi

# Try to get dashboards (with both anonymous and auth)
echo -e "\n📊 Checking for dashboards..."

# Try anonymous first
DASHBOARDS=$(curl -s http://localhost:3000/api/search 2>/dev/null)

if [ $? -eq 0 ] && [ ! -z "$DASHBOARDS" ]; then
    echo "Found dashboards:"
    echo "$DASHBOARDS" | jq -r '.[] | "  - \(.title)"' 2>/dev/null || echo "$DASHBOARDS"
else
    # Try with default credentials
    echo "Trying with authentication..."
    curl -s -u admin:admin123 http://localhost:3000/api/search | jq -r '.[] | "  - \(.title)"' 2>/dev/null || echo "No dashboards found or authentication required"
fi

echo -e "\n📌 Access Grafana at: http://localhost:3000"
echo "   Login: admin / admin123"
