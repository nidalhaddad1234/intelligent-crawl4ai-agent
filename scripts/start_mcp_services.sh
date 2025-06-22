#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Intelligent Crawl4AI MCP Server Services${NC}"
echo "=================================================="

# Function to check if a service is running
check_service() {
    local service_name=$1
    local check_command=$2
    
    if eval $check_command &> /dev/null; then
        echo -e "${GREEN}✅ $service_name is already running${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ $service_name is not running${NC}"
        return 1
    fi
}

# Function to start a service
start_service() {
    local service_name=$1
    local start_command=$2
    local check_command=$3
    
    echo -e "${BLUE}🔄 Starting $service_name...${NC}"
    
    # Start the service in the background
    eval $start_command &
    local service_pid=$!
    
    # Wait a bit for the service to start
    sleep 3
    
    # Check if service is now running
    if eval $check_command &> /dev/null; then
        echo -e "${GREEN}✅ $service_name started successfully (PID: $service_pid)${NC}"
        echo $service_pid > "/tmp/${service_name,,}_pid"
        return 0
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        return 1
    fi
}

# Check and start Ollama
echo -e "${BLUE}🧠 Checking Ollama...${NC}"
if ! check_service "Ollama" "curl -s http://localhost:11434/api/tags"; then
    if command -v ollama &> /dev/null; then
        start_service "Ollama" "ollama serve" "curl -s http://localhost:11434/api/tags"
    else
        echo -e "${RED}❌ Ollama not installed. Please install from: https://ollama.ai${NC}"
    fi
fi

# Check and start Redis
echo -e "${BLUE}💾 Checking Redis...${NC}"
if ! check_service "Redis" "redis-cli ping"; then
    if command -v redis-server &> /dev/null; then
        start_service "Redis" "redis-server --daemonize yes" "redis-cli ping"
    else
        echo -e "${RED}❌ Redis not installed.${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "Install with: brew install redis"
        else
            echo "Install with: sudo apt-get install redis-server"
        fi
    fi
fi

# Check and start ChromaDB
echo -e "${BLUE}🗄️ Checking ChromaDB...${NC}"
if ! check_service "ChromaDB" "curl -s http://localhost:8000/api/v1/heartbeat"; then
    if command -v docker &> /dev/null; then
        echo -e "${BLUE}🔄 Starting ChromaDB with Docker...${NC}"
        docker run -d --name chromadb -p 8000:8000 chromadb/chroma 2>/dev/null
        
        # Wait for ChromaDB to be ready
        echo -e "${BLUE}⏳ Waiting for ChromaDB to be ready...${NC}"
        for i in {1..30}; do
            if curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
                echo -e "${GREEN}✅ ChromaDB started successfully${NC}"
                break
            fi
            sleep 2
        done
        
        if ! curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
            echo -e "${RED}❌ ChromaDB failed to start${NC}"
        fi
    else
        echo -e "${RED}❌ Docker not available. Install Docker to run ChromaDB${NC}"
        echo -e "${BLUE}💡 Alternative: Install ChromaDB locally with: pip install chromadb${NC}"
    fi
fi

# Check if Python dependencies are installed
echo -e "${BLUE}🐍 Checking Python dependencies...${NC}"
if python3 -c "import mcp" &> /dev/null; then
    echo -e "${GREEN}✅ MCP dependencies available${NC}"
else
    echo -e "${YELLOW}⚠️ Installing MCP dependencies...${NC}"
    pip3 install -r requirements-mcp.txt
fi

# Verify MCP Server
echo -e "${BLUE}🔧 Verifying MCP Server...${NC}"
if python3 -c "
import sys
sys.path.append('src')
from mcp_servers.intelligent_orchestrator import config
print(f'Server: {config.server_name} v{config.server_version}')
" 2>/dev/null; then
    echo -e "${GREEN}✅ MCP Server ready${NC}"
else
    echo -e "${RED}❌ MCP Server verification failed${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Service startup completed!${NC}"
echo ""
echo -e "${BLUE}📋 Service Status:${NC}"

# Final status check
echo -n "  Ollama: "
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}Running${NC}"
else
    echo -e "${RED}Not running${NC}"
fi

echo -n "  Redis: "
if redis-cli ping &> /dev/null; then
    echo -e "${GREEN}Running${NC}"
else
    echo -e "${RED}Not running${NC}"
fi

echo -n "  ChromaDB: "
if curl -s http://localhost:8000/api/v1/heartbeat &> /dev/null; then
    echo -e "${GREEN}Running${NC}"
else
    echo -e "${RED}Not running${NC}"
fi

echo ""
echo -e "${BLUE}📚 Next Steps:${NC}"
echo "1. Test the MCP server: ./scripts/test_mcp_server.sh"
echo "2. Restart Claude Desktop"
echo "3. Use MCP tools in Claude Desktop"
echo ""
echo -e "${BLUE}🛑 To stop services:${NC}"
echo "./scripts/stop_mcp_services.sh"
echo ""
echo -e "${GREEN}All systems ready for intelligent web scraping! 🕷️✨${NC}"
