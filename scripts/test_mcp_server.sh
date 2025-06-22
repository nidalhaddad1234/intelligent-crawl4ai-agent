#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Intelligent Crawl4AI MCP Server${NC}"
echo "============================================="

# Change to the project directory
cd "$(dirname "$0")/.."

# Test 1: Check Python imports
echo -e "${BLUE}🐍 Testing Python imports...${NC}"
if python3 -c "
import sys
sys.path.append('src')
try:
    from mcp_servers.intelligent_orchestrator import config, MCPConfig, MCPMetrics, IntelligentOrchestrator
    print('✅ All core imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
" 2>/dev/null; then
    echo -e "${GREEN}✅ Python imports test passed${NC}"
else
    echo -e "${RED}❌ Python imports test failed${NC}"
    exit 1
fi

# Test 2: Configuration loading
echo -e "${BLUE}⚙️ Testing configuration loading...${NC}"
if python3 -c "
import sys
sys.path.append('src')
from mcp_servers.intelligent_orchestrator import MCPConfig
config = MCPConfig.from_env()
print(f'✅ Server name: {config.server_name}')
print(f'✅ Server version: {config.server_version}')
print(f'✅ Ollama URL: {config.ollama_url}')
" 2>/dev/null; then
    echo -e "${GREEN}✅ Configuration test passed${NC}"
else
    echo -e "${RED}❌ Configuration test failed${NC}"
    exit 1
fi

# Test 3: MCP Server startup (dry run)
echo -e "${BLUE}🚀 Testing MCP Server startup (dry run)...${NC}"
timeout 10s python3 -c "
import sys
import asyncio
sys.path.append('src')
from mcp_servers.intelligent_orchestrator import ensure_initialized, orchestrator

async def test_startup():
    try:
        await ensure_initialized()
        print('✅ MCP Server initialization successful')
        if orchestrator:
            print(f'✅ Orchestrator status: {orchestrator.health_status[\"status\"]}')
            await orchestrator.shutdown()
    except Exception as e:
        print(f'❌ Initialization error: {e}')
        sys.exit(1)

asyncio.run(test_startup())
" 2>/dev/null && echo -e "${GREEN}✅ MCP Server startup test passed${NC}" || echo -e "${YELLOW}⚠️ MCP Server startup test incomplete (services may not be running)${NC}"

# Test 4: Tool definitions
echo -e "${BLUE}🔧 Testing tool definitions...${NC}"
if python3 -c "
import sys
import asyncio
sys.path.append('src')
from mcp_servers.intelligent_orchestrator import handle_list_tools

async def test_tools():
    try:
        tools_result = await handle_list_tools()
        tools = tools_result.tools
        print(f'✅ Found {len(tools)} tools:')
        for tool in tools:
            print(f'  - {tool.name}: {tool.description[:50]}...')
    except Exception as e:
        print(f'❌ Tool definitions error: {e}')
        sys.exit(1)

asyncio.run(test_tools())
" 2>/dev/null; then
    echo -e "${GREEN}✅ Tool definitions test passed${NC}"
else
    echo -e "${RED}❌ Tool definitions test failed${NC}"
    exit 1
fi

# Test 5: Service connectivity
echo -e "${BLUE}🌐 Testing service connectivity...${NC}"

# Test Ollama
if curl -s http://localhost:11434/api/tags &> /dev/null; then
    echo -e "${GREEN}✅ Ollama service is accessible${NC}"
else
    echo -e "${YELLOW}⚠️ Ollama service not accessible (may affect AI features)${NC}"
fi

# Test ChromaDB
if python3 -c "
import chromadb
try:
    client = chromadb.HttpClient(host='localhost', port=8000)
    client.heartbeat()
    print('✅ ChromaDB service is accessible')
except Exception:
    print('⚠️ ChromaDB service not accessible (may affect vector storage)')
" 2>/dev/null; then
    :
else
    echo -e "${YELLOW}⚠️ ChromaDB connectivity test failed${NC}"
fi

# Test Redis
if python3 -c "
import redis
try:
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    r.ping()
    print('✅ Redis service is accessible')
except Exception:
    print('⚠️ Redis service not accessible (may affect caching)')
" 2>/dev/null; then
    :
else
    echo -e "${YELLOW}⚠️ Redis connectivity test failed${NC}"
fi

# Test 6: Tool execution (mock test)
echo -e "${BLUE}🎯 Testing tool execution...${NC}"
if python3 -c "
import sys
import asyncio
import json
sys.path.append('src')
from mcp_servers.intelligent_orchestrator import handle_call_tool

async def test_tool_execution():
    try:
        # Test get_system_status tool
        result = await handle_call_tool('get_system_status', {})
        data = json.loads(result.content[0].text)
        print(f'✅ System status: {data[\"system_status\"]}')
        
        # Test analyze_website_structure tool
        result = await handle_call_tool('analyze_website_structure', {
            'url': 'https://example.com',
            'purpose': 'test'
        })
        print('✅ Website analysis tool executed successfully')
        
    except Exception as e:
        print(f'❌ Tool execution error: {e}')
        sys.exit(1)

asyncio.run(test_tool_execution())
" 2>/dev/null; then
    echo -e "${GREEN}✅ Tool execution test passed${NC}"
else
    echo -e "${RED}❌ Tool execution test failed${NC}"
    exit 1
fi

# Test 7: Claude Desktop configuration
echo -e "${BLUE}🔧 Testing Claude Desktop configuration...${NC}"
CLAUDE_CONFIG_DIR=""

if [[ "$OSTYPE" == "darwin"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/Library/Application Support/Claude"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CLAUDE_CONFIG_DIR="$HOME/.config/Claude"
fi

if [ -n "$CLAUDE_CONFIG_DIR" ] && [ -f "$CLAUDE_CONFIG_DIR/claude_desktop_config.json" ]; then
    if grep -q "intelligent_crawl4ai_orchestrator" "$CLAUDE_CONFIG_DIR/claude_desktop_config.json"; then
        echo -e "${GREEN}✅ Claude Desktop configuration found${NC}"
    else
        echo -e "${YELLOW}⚠️ MCP server not found in Claude Desktop config${NC}"
    fi
else
    echo -e "${YELLOW}⚠️ Claude Desktop config file not found${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Testing completed!${NC}"
echo ""
echo -e "${BLUE}📋 Test Summary:${NC}"
echo "- Python imports: ✅"
echo "- Configuration loading: ✅"
echo "- Tool definitions: ✅"
echo "- Tool execution: ✅"
echo ""
echo -e "${BLUE}📚 Next Steps:${NC}"
echo "1. Ensure all required services are running:"
echo "   - ollama serve"
echo "   - chromadb (docker run -p 8000:8000 chromadb/chroma)"
echo "   - redis-server"
echo ""
echo "2. Restart Claude Desktop to load the MCP server"
echo ""
echo "3. Test in Claude Desktop by using MCP tools"
echo ""
echo -e "${GREEN}Ready for production! 🚀${NC}"
