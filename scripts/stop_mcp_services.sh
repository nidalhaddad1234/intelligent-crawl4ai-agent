#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping Intelligent Crawl4AI MCP Server Services${NC}"
echo "=============================================="

# Function to stop a service
stop_service() {
    local service_name=$1
    local stop_command=$2
    local pid_file="/tmp/${service_name,,}_pid"
    
    echo -e "${BLUE}🔄 Stopping $service_name...${NC}"
    
    # Try to stop using the provided command
    if eval $stop_command &> /dev/null; then
        echo -e "${GREEN}✅ $service_name stopped successfully${NC}"
    else
        echo -e "${YELLOW}⚠️ Could not stop $service_name with command${NC}"
        
        # Try to stop using PID file
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if kill -0 "$pid" 2>/dev/null; then
                kill "$pid" 2>/dev/null
                sleep 2
                if ! kill -0 "$pid" 2>/dev/null; then
                    echo -e "${GREEN}✅ $service_name stopped (PID: $pid)${NC}"
                    rm -f "$pid_file"
                else
                    kill -9 "$pid" 2>/dev/null
                    echo -e "${YELLOW}⚠️ $service_name force-killed (PID: $pid)${NC}"
                    rm -f "$pid_file"
                fi
            else
                echo -e "${GREEN}✅ $service_name was not running${NC}"
                rm -f "$pid_file"
            fi
        else
            echo -e "${GREEN}✅ $service_name appears to be stopped${NC}"
        fi
    fi
}

# Stop ChromaDB (Docker)
echo -e "${BLUE}🗄️ Stopping ChromaDB...${NC}"
if docker ps --format "table {{.Names}}" | grep -q chromadb; then
    docker stop chromadb &> /dev/null
    docker rm chromadb &> /dev/null
    echo -e "${GREEN}✅ ChromaDB container stopped and removed${NC}"
else
    echo -e "${GREEN}✅ ChromaDB container was not running${NC}"
fi

# Stop Redis
echo -e "${BLUE}💾 Stopping Redis...${NC}"
if command -v redis-cli &> /dev/null; then
    stop_service "Redis" "redis-cli shutdown"
else
    echo -e "${YELLOW}⚠️ Redis CLI not available${NC}"
fi

# Stop Ollama (if started by us)
echo -e "${BLUE}🧠 Checking Ollama...${NC}"
if [ -f "/tmp/ollama_pid" ]; then
    stop_service "Ollama" "false"  # We'll use PID file approach
else
    echo -e "${BLUE}💡 Ollama may be running independently. Use 'pkill ollama' if needed${NC}"
fi

# Clean up any remaining processes
echo -e "${BLUE}🧹 Cleaning up...${NC}"

# Remove PID files
rm -f /tmp/ollama_pid /tmp/redis_pid /tmp/chromadb_pid

# Check if any services are still running
echo ""
echo -e "${BLUE}📋 Final Service Status:${NC}"

echo -n "  Ollama: "
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${YELLOW}Still running${NC}"
else
    echo -e "${GREEN}Stopped${NC}"
fi

echo -n "  Redis: "
if redis-cli ping &> /dev/null; then
    echo -e "${YELLOW}Still running${NC}"
else
    echo -e "${GREEN}Stopped${NC}"
fi

echo -n "  ChromaDB: "
if curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
    echo -e "${YELLOW}Still running${NC}"
else
    echo -e "${GREEN}Stopped${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Service shutdown completed!${NC}"
echo ""
echo -e "${BLUE}💡 Note:${NC}"
echo "Some services may be running independently and were not stopped."
echo "Use system tools if you need to stop them manually:"
echo "  - Ollama: pkill ollama"
echo "  - Redis: sudo systemctl stop redis (Linux) or brew services stop redis (macOS)"
echo "  - ChromaDB: docker stop chromadb (if running in Docker)"
echo ""
echo -e "${GREEN}MCP Server services shutdown complete! 🛑${NC}"
