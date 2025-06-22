#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Intelligent Crawl4AI MCP Server Setup${NC}"
echo "=================================================="

# Check if running on macOS or Linux
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${GREEN}✅ Detected macOS${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo -e "${GREEN}✅ Detected Linux${NC}"
else
    echo -e "${RED}❌ Unsupported operating system${NC}"
    exit 1
fi

# Check Python version
echo -e "${BLUE}🐍 Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✅ Python ${PYTHON_VERSION} found${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Install MCP Server dependencies
echo -e "${BLUE}📦 Installing MCP Server dependencies...${NC}"
pip3 install -r requirements-mcp.txt

# Setup environment configuration
echo -e "${BLUE}⚙️ Setting up environment configuration...${NC}"
if [ ! -f .env ]; then
    cp config/.env.template .env
    echo -e "${GREEN}✅ Created .env file from template${NC}"
    echo -e "${YELLOW}⚠️ Please edit .env file with your specific configuration${NC}"
else
    echo -e "${YELLOW}⚠️ .env file already exists, skipping...${NC}"
fi

# Check for required services
echo -e "${BLUE}🔍 Checking required services...${NC}"

# Check Ollama
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama CLI found${NC}"
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo -e "${GREEN}✅ Ollama server is running${NC}"
    else
        echo -e "${YELLOW}⚠️ Ollama server not running. Start with: ollama serve${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Ollama not found. Install from: https://ollama.ai${NC}"
fi

# Check ChromaDB
if python3 -c "import chromadb" &> /dev/null; then
    echo -e "${GREEN}✅ ChromaDB Python package found${NC}"
else
    echo -e "${YELLOW}⚠️ ChromaDB not found. Installing...${NC}"
    pip3 install chromadb
fi

# Check Redis
if command -v redis-server &> /dev/null; then
    echo -e "${GREEN}✅ Redis server found${NC}"
else
    echo -e "${YELLOW}⚠️ Redis not found. Install with:${NC}"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "  brew install redis"
    else
        echo "  sudo apt-get install redis-server"
    fi
fi

# Create logs directory
echo -e "${BLUE}📁 Creating logs directory...${NC}"
mkdir -p logs
echo -e "${GREEN}✅ Logs directory created${NC}"

# Test MCP Server
echo -e "${BLUE}🧪 Testing MCP Server...${NC}"
if python3 -c "from src.mcp_servers.intelligent_orchestrator import config; print('✅ MCP Server imports successfully')" 2>/dev/null; then
    echo -e "${GREEN}✅ MCP Server syntax check passed${NC}"
else
    echo -e "${YELLOW}⚠️ MCP Server syntax check failed. Please check dependencies.${NC}"
fi

# Setup Claude Desktop integration
echo -e "${BLUE}🔧 Setting up Claude Desktop integration...${NC}"
CLAUDE_CONFIG_DIR=""

if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/.config/Claude"
fi

if [ -n "$CLAUDE_CONFIG_DIR" ]; then
    mkdir -p "$CLAUDE_CONFIG_DIR"
    
    if [ -f "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" ]; then
        echo -e "${YELLOW}⚠️ Claude Desktop config exists. Backup created.${NC}"
        cp "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" "$CLAUDE_CONFIG_DIR/claude_desktop_config.json.backup"
    fi
    
    # Update the path in the config file to use absolute path
    CURRENT_DIR=$(pwd)
    sed "s|/Users/stm2/Desktop/site-web/private/intelligent-crawl4ai-agent|$CURRENT_DIR|g" config/claude_desktop_mcp.json > "$CLAUDE_CONFIG_DIR/claude_desktop_config.json"
    
    echo -e "${GREEN}✅ Claude Desktop configuration updated${NC}"
else
    echo -e "${YELLOW}⚠️ Could not determine Claude Desktop config directory${NC}"
    echo -e "${BLUE}📋 Manual setup required:${NC}"
    echo "1. Locate your Claude Desktop config file"
    echo "2. Merge contents from config/claude_desktop_mcp.json"
fi

echo ""
echo -e "${GREEN}🎉 Setup completed successfully!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Edit .env file with your specific configuration"
echo "2. Start required services (Ollama, ChromaDB, Redis)"
echo "3. Test the MCP server: ./scripts/test_mcp_server.sh"
echo "4. Restart Claude Desktop to load the new MCP server"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "- MCP Server logs: logs/mcp_server.log"
echo "- Configuration: .env"
echo "- Claude Desktop config: $CLAUDE_CONFIG_DIR/claude_desktop_config.json"
echo ""
echo -e "${GREEN}Happy scraping! 🕷️✨${NC}"
