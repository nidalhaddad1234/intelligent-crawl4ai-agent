#!/bin/bash
# Enhanced start script for Intelligent Crawl4AI Agent

echo "🚀 Starting Intelligent Crawl4AI Agent..."
echo "=" * 60

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/docker/compose"

print_status $BLUE "📂 Working directory: $SCRIPT_DIR"
print_status $BLUE "🐳 Docker compose directory: $DOCKER_DIR"
echo ""

# Function to check if Ollama is running
check_ollama() {
    print_status $YELLOW "🔍 Checking Ollama status..."
    
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        print_status $GREEN "✅ Ollama is running"
        
        # Check if DeepSeek model is available
        if curl -s http://localhost:11434/api/tags | grep -q "deepseek-coder:1.3b"; then
            print_status $GREEN "✅ DeepSeek model is available"
        else
            print_status $YELLOW "⚠️  DeepSeek model not found. Installing..."
            echo "📦 Running: ollama pull deepseek-coder:1.3b"
            ollama pull deepseek-coder:1.3b
        fi
    else
        print_status $RED "❌ Ollama is not running!"
        echo ""
        print_status $YELLOW "Please start Ollama first:"
        echo "    ollama serve"
        echo "    ollama pull deepseek-coder:1.3b"
        echo ""
        read -p "Do you want to continue without Ollama? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status $RED "Exiting. Please start Ollama and try again."
            exit 1
        fi
        print_status $YELLOW "⚠️  Continuing without Ollama (fallback mode)"
    fi
    echo ""
}

# Function to select compose file
select_compose_file() {
    local default_file="$DOCKER_DIR/docker-compose.local-full-debug.yml"
    
    # Check available compose files
    local files=()
    local descriptions=()
    
    if [ -f "$DOCKER_DIR/docker-compose.local-full-debug.yml" ]; then
        files+=("$DOCKER_DIR/docker-compose.local-full-debug.yml")
        descriptions+=("🐛 Debug Version (Enhanced logging & Python 3)")
    fi
    
    if [ -f "$DOCKER_DIR/docker-compose.local-full-fixed.yml" ]; then
        files+=("$DOCKER_DIR/docker-compose.local-full-fixed.yml") 
        descriptions+=("🔧 Fixed Version (Working directories fixed)")
    fi
    
    if [ -f "$DOCKER_DIR/docker-compose.local-full.yml" ]; then
        files+=("$DOCKER_DIR/docker-compose.local-full.yml")
        descriptions+=("📦 Original Version")
    fi
    
    if [ ${#files[@]} -eq 0 ]; then
        print_status $RED "❌ No compose files found in $DOCKER_DIR"
        exit 1
    fi
    
    # Default to debug version if available
    if [ -f "$default_file" ]; then
        COMPOSE_FILE="$default_file"
        COMPOSE_DESC="Debug Version"
    else
        COMPOSE_FILE="${files[0]}"
        COMPOSE_DESC="${descriptions[0]}"
    fi
    
    # Allow override via command line
    case "${1:-}" in
        --debug|-d)
            if [ -f "$DOCKER_DIR/docker-compose.local-full-debug.yml" ]; then
                COMPOSE_FILE="$DOCKER_DIR/docker-compose.local-full-debug.yml"
                COMPOSE_DESC="Debug Version"
            else
                print_status $RED "❌ Debug compose file not found"
                exit 1
            fi
            ;;
        --fixed|-f)
            if [ -f "$DOCKER_DIR/docker-compose.local-full-fixed.yml" ]; then
                COMPOSE_FILE="$DOCKER_DIR/docker-compose.local-full-fixed.yml"
                COMPOSE_DESC="Fixed Version"
            else
                print_status $RED "❌ Fixed compose file not found"
                exit 1
            fi
            ;;
        --original|-o)
            if [ -f "$DOCKER_DIR/docker-compose.local-full.yml" ]; then
                COMPOSE_FILE="$DOCKER_DIR/docker-compose.local-full.yml"
                COMPOSE_DESC="Original Version"
            else
                print_status $RED "❌ Original compose file not found"
                exit 1
            fi
            ;;
        --interactive|-i)
            echo "📋 Available versions:"
            for i in "${!files[@]}"; do
                echo "  $((i+1)). ${descriptions[$i]}"
            done
            echo ""
            read -p "Select version (1-${#files[@]}): " -n 1 -r
            echo ""
            
            if [[ $REPLY =~ ^[1-${#files[@]}]$ ]]; then
                COMPOSE_FILE="${files[$((REPLY-1))]}"
                COMPOSE_DESC="${descriptions[$((REPLY-1))]}"
            else
                print_status $YELLOW "Invalid selection, using default"
            fi
            ;;
        --help|-h)
            echo ""
            echo "🆘 Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  (no args)      Start with debug version (recommended)"
            echo "  --debug, -d    Start with debug version (enhanced logging)"
            echo "  --fixed, -f    Start with fixed version"
            echo "  --original, -o Start with original version"
            echo "  --interactive, -i  Interactive version selection"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "🎯 Recommended: Use debug version for troubleshooting"
            exit 0
            ;;
    esac
    
    print_status $GREEN "📋 Selected: $COMPOSE_DESC"
    print_status $BLUE "📄 File: $(basename $COMPOSE_FILE)"
    echo ""
}

# Function to check Docker
check_docker() {
    print_status $YELLOW "🐳 Checking Docker..."
    
    if ! command -v docker &> /dev/null; then
        print_status $RED "❌ Docker is not installed"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_status $RED "❌ Docker is not running"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_status $RED "❌ Docker Compose is not available"
        exit 1
    fi
    
    print_status $GREEN "✅ Docker is ready"
    echo ""
}

# Function to check port availability
check_ports() {
    print_status $YELLOW "🔌 Checking port availability..."
    
    local ports=(8888 8000 6379 5432 3000 3001 3002 9090 8080 8811)
    local occupied_ports=()
    
    for port in "${ports[@]}"; do
        if netstat -tuln 2>/dev/null | grep -q ":$port "; then
            occupied_ports+=($port)
        fi
    done
    
    if [ ${#occupied_ports[@]} -gt 0 ]; then
        print_status $YELLOW "⚠️  Some ports are already in use: ${occupied_ports[*]}"
        echo ""
        echo "📋 Port usage:"
        echo "  8888 - Web UI"
        echo "  8000 - ChromaDB"
        echo "  6379 - Redis"
        echo "  5432 - PostgreSQL"
        echo "  3000 - Grafana"
        echo "  3001-3002 - Browser Pools"
        echo "  9090 - Prometheus"
        echo "  8080 - Nginx"
        echo "  8811 - MCP Server"
        echo ""
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status $RED "Exiting. Please free up the ports and try again."
            exit 1
        fi
    else
        print_status $GREEN "✅ All required ports are available"
    fi
    echo ""
}

# Function to start services
start_services() {
    print_status $YELLOW "🚀 Starting services with $COMPOSE_DESC..."
    
    # Start all services
    docker compose -f "$COMPOSE_FILE" up -d
    
    if [ $? -eq 0 ]; then
        print_status $GREEN "✅ Services started successfully!"
    else
        print_status $RED "❌ Failed to start services"
        exit 1
    fi
    echo ""
}

# Function to wait for services
wait_for_services() {
    print_status $YELLOW "⏳ Waiting for services to initialize..."
    
    local max_wait=120
    local waited=0
    local interval=5
    
    while [ $waited -lt $max_wait ]; do
        if curl -s http://localhost:8888/health &> /dev/null; then
            print_status $GREEN "✅ Web UI is ready!"
            break
        fi
        
        echo "⏱️  Waiting... ($waited/${max_wait}s)"
        sleep $interval
        waited=$((waited + interval))
    done
    
    if [ $waited -ge $max_wait ]; then
        print_status $YELLOW "⚠️  Services are taking longer than expected to start"
        echo "📊 You can check the status with: docker compose -f '$COMPOSE_FILE' ps"
        echo "📋 View logs with: docker compose -f '$COMPOSE_FILE' logs"
    fi
    echo ""
}

# Function to show status
show_status() {
    print_status $YELLOW "📊 Service Status:"
    docker compose -f "$COMPOSE_FILE" ps
    echo ""
    
    print_status $YELLOW "🌐 Access URLs:"
    echo "  🖥️  Web UI:        http://localhost:8888"
    echo "  📊 Grafana:       http://localhost:3000 (admin/admin123)"
    echo "  🔍 ChromaDB:      http://localhost:8000"
    echo "  📈 Prometheus:    http://localhost:9090"
    echo "  🔧 API Docs:      http://localhost:8888/api/docs"
    echo ""
    
    print_status $YELLOW "📋 Useful Commands:"
    echo "  📊 View logs:     docker compose -f '$COMPOSE_FILE' logs -f"
    echo "  🛑 Stop all:      ./stop.sh"
    echo "  🔍 Check status:  docker compose -f '$COMPOSE_FILE' ps"
    echo ""
}

# Function to test the system
test_system() {
    print_status $YELLOW "🧪 Testing system..."
    
    echo "📤 Testing API endpoint..."
    local test_response
    test_response=$(curl -s -X POST http://localhost:8888/api/chat \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello, can you help me?"}' 2>/dev/null)
    
    if [ $? -eq 0 ] && echo "$test_response" | grep -q "response"; then
        print_status $GREEN "✅ API is responding correctly"
        echo "📝 Test response received: $(echo "$test_response" | cut -c1-100)..."
    else
        print_status $YELLOW "⚠️  API test failed, but service might still be starting"
        echo "💡 Try the test again in a few minutes"
    fi
    echo ""
}

# Main execution
main() {
    # Parse arguments
    local mode="${1:-}"
    
    # Show help if requested
    if [[ "$mode" == "--help" ]] || [[ "$mode" == "-h" ]]; then
        select_compose_file "$mode"
        return
    fi
    
    # Perform checks
    check_docker
    check_ollama
    select_compose_file "$mode"
    check_ports
    
    # Start services
    start_services
    wait_for_services
    
    # Show results
    show_status
    
    # Optional system test
    if [[ "${mode}" == "--test" ]] || [[ "${mode}" == "-t" ]]; then
        test_system
    fi
    
    print_status $GREEN "🎉 Intelligent Crawl4AI Agent is ready!"
    echo ""
    print_status $BLUE "💡 Next steps:"
    echo "  1. Open http://localhost:8888 in your browser"
    echo "  2. Try a simple request: 'Extract title from https://example.com'"
    echo "  3. Check the logs for detailed AI reasoning: docker logs intelligent_crawl4ai_web_ui -f"
    echo ""
    print_status $YELLOW "📚 For debugging:"
    echo "  - Web UI logs: docker logs intelligent_crawl4ai_web_ui -f"
    echo "  - All logs: docker compose -f '$COMPOSE_FILE' logs -f"
    echo "  - System status: http://localhost:8888/api/system/status"
}

# Run main function with all arguments
main "$@"
