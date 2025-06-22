#!/bin/bash
# Setup script for Intelligent Crawl4AI Agent

set -e

echo "🚀 Setting up Intelligent Crawl4AI Agent..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "Python 3.8+ is required. Current version: $python_version"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is required but not installed."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is required but not installed."
        exit 1
    fi
    
    print_status "Prerequisites check passed ✓"
}

# Install Python dependencies
install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        print_status "Created virtual environment"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_status "Python dependencies installed ✓"
}

# Install Playwright browsers
install_browsers() {
    print_status "Installing Playwright browsers..."
    
    source venv/bin/activate
    playwright install chromium --with-deps
    
    print_status "Playwright browsers installed ✓"
}

# Setup Ollama
setup_ollama() {
    print_status "Setting up Ollama..."
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        print_status "Installing Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    
    # Start Ollama service
    print_status "Starting Ollama service..."
    ollama serve &
    OLLAMA_PID=$!
    
    # Wait for Ollama to be ready
    sleep 5
    
    # Pull required models
    print_status "Pulling required AI models..."
    ollama pull llama3.1
    ollama pull nomic-embed-text
    
    print_status "Ollama setup complete ✓"
}

# Setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# AI Services
OLLAMA_URL=http://localhost:11434
CHROMADB_URL=http://localhost:8000

# High-Volume Processing
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://scraper_user:secure_password_123@localhost:5432/intelligent_scraping

# Browser Pools
BROWSER_POOL_URLS=http://localhost:3001,http://localhost:3002

# Optional: External Services
CAPTCHA_API_KEY=
PROXY_USERNAME=
PROXY_PASSWORD=

# Logging
LOG_LEVEL=INFO

# Performance
MAX_WORKERS=50
MAX_CONCURRENT_PER_WORKER=10
EOF
        print_status "Environment file created ✓"
    else
        print_warning "Environment file already exists, skipping..."
    fi
}

# Build and start Docker services
start_services() {
    print_status "Building and starting Docker services..."
    
    # Build custom images
    docker-compose build
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    print_status "Docker services started ✓"
}

# Check service health
check_service_health() {
    print_status "Checking service health..."
    
    services=("chromadb:8000" "redis:6379" "postgres:5432" "browser-pool-1:3001" "browser-pool-2:3002")
    
    for service in "${services[@]}"; do
        IFS=':' read -r name port <<< "$service"
        
        if curl -f "http://localhost:$port" > /dev/null 2>&1 || nc -z localhost "$port" > /dev/null 2>&1; then
            print_status "$name service is healthy ✓"
        else
            print_warning "$name service may not be ready yet"
        fi
    done
}

# Setup Claude Desktop configuration
setup_claude_config() {
    print_status "Setting up Claude Desktop configuration..."
    
    # Get the current directory
    CURRENT_DIR=$(pwd)
    
    # Update the Claude Desktop config with the correct path
    sed -i.bak "s|/Users/stm2/Desktop/site-web/private/intelligent-crawl4ai-agent|$CURRENT_DIR|g" config/claude_desktop_config.json
    
    print_status "Claude Desktop configuration updated ✓"
    print_warning "Please manually copy config/claude_desktop_config.json to your Claude Desktop settings"
    print_warning "Claude Desktop config location: ~/.config/Claude Desktop/claude_desktop_config.json"
}

# Run initial tests
run_tests() {
    print_status "Running initial tests..."
    
    source venv/bin/activate
    
    # Test Ollama connection
    if curl -f http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_status "Ollama connection test passed ✓"
    else
        print_warning "Ollama connection test failed"
    fi
    
    # Test ChromaDB connection
    if curl -f http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
        print_status "ChromaDB connection test passed ✓"
    else
        print_warning "ChromaDB connection test failed"
    fi
    
    # Test Redis connection
    if redis-cli ping > /dev/null 2>&1; then
        print_status "Redis connection test passed ✓"
    else
        print_warning "Redis connection test failed"
    fi
}

# Main setup function
main() {
    echo "🎯 Intelligent Crawl4AI Agent Setup"
    echo "===================================="
    
    check_prerequisites
    install_python_deps
    install_browsers
    setup_environment
    setup_ollama
    start_services
    setup_claude_config
    run_tests
    
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Copy config/claude_desktop_config.json to your Claude Desktop settings"
    echo "2. Restart Claude Desktop"
    echo "3. Test the agent with: 'Analyze and scrape https://example.com for company_info'"
    echo ""
    echo "Services running:"
    echo "- Ollama: http://localhost:11434"
    echo "- ChromaDB: http://localhost:8000"
    echo "- Grafana Dashboard: http://localhost:3000 (admin/admin123)"
    echo "- Prometheus: http://localhost:9090"
    echo ""
    echo "To stop services: docker-compose down"
    echo "To view logs: docker-compose logs -f"
    echo ""
    echo "Happy scraping! 🕸️"
}

# Run main function
main "$@"
