#!/bin/bash
# Stop script for Intelligent Crawl4AI Agent

echo "🛑 Stopping Intelligent Crawl4AI Agent..."
echo "=" * 50

# Function to stop containers with specific compose file
stop_compose() {
    local compose_file=$1
    local description=$2
    
    echo "🔍 Checking if $description is running..."
    
    if [ -f "$compose_file" ]; then
        echo "📋 Using compose file: $compose_file"
        
        # Check if any containers are running
        running_containers=$(docker compose -f "$compose_file" ps -q)
        
        if [ -n "$running_containers" ]; then
            echo "🛑 Stopping $description..."
            docker compose -f "$compose_file" down
            echo "✅ $description stopped"
        else
            echo "ℹ️  No containers running for $description"
        fi
    else
        echo "⚠️  Compose file not found: $compose_file"
    fi
    echo ""
}

# Function to stop containers by partial name match
stop_by_name() {
    local pattern=$1
    local description=$2
    
    echo "🔍 Looking for containers matching: $pattern"
    
    # Find containers matching the pattern
    containers=$(docker ps -q --filter "name=$pattern")
    
    if [ -n "$containers" ]; then
        echo "🛑 Stopping $description..."
        docker stop $containers
        echo "🗑️  Removing $description..."
        docker rm $containers
        echo "✅ $description stopped and removed"
    else
        echo "ℹ️  No running containers found for: $pattern"
    fi
    echo ""
}

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="$SCRIPT_DIR/docker/compose"

echo "📂 Working directory: $SCRIPT_DIR"
echo "🐳 Docker compose directory: $DOCKER_DIR"
echo ""

# Try to stop using different compose files (in order of preference)
echo "🎯 Attempting to stop using compose files..."

# 1. Try debug version first
stop_compose "$DOCKER_DIR/docker-compose.local-full-debug.yml" "Debug Version"

# 2. Try fixed version
stop_compose "$DOCKER_DIR/docker-compose.local-full-fixed.yml" "Fixed Version"

# 3. Try original version
stop_compose "$DOCKER_DIR/docker-compose.local-full.yml" "Original Version"

# 4. Try any other compose files
for compose_file in "$DOCKER_DIR"/docker-compose*.yml; do
    if [ -f "$compose_file" ]; then
        filename=$(basename "$compose_file")
        if [[ "$filename" != *"debug"* ]] && [[ "$filename" != *"fixed"* ]] && [[ "$filename" != *"local-full.yml" ]]; then
            stop_compose "$compose_file" "$(basename "$compose_file")"
        fi
    fi
done

echo "🧹 Cleaning up any remaining Crawl4AI containers..."

# Stop containers by name pattern
stop_by_name "intelligent_crawl4ai" "Intelligent Crawl4AI containers"
stop_by_name "compose-" "Compose containers"

# Additional cleanup
echo "🔍 Checking for any orphaned containers..."
orphaned=$(docker ps -q --filter "label=com.docker.compose.project=compose")
if [ -n "$orphaned" ]; then
    echo "🧹 Cleaning up orphaned containers..."
    docker stop $orphaned
    docker rm $orphaned
    echo "✅ Orphaned containers cleaned up"
else
    echo "ℹ️  No orphaned containers found"
fi

echo ""
echo "🌐 Checking if networks need cleanup..."
networks=$(docker network ls -q --filter "name=compose_ai_network")
if [ -n "$networks" ]; then
    echo "🧹 Removing AI network..."
    docker network rm compose_ai_network 2>/dev/null || echo "ℹ️  Network already removed or in use"
else
    echo "ℹ️  No AI networks to remove"
fi

echo ""
echo "📊 Final status check..."
remaining=$(docker ps --filter "name=intelligent_crawl4ai" --format "table {{.Names}}\t{{.Status}}")
if [ -n "$remaining" ] && [ "$remaining" != "NAMES	STATUS" ]; then
    echo "⚠️  Some containers are still running:"
    echo "$remaining"
    echo ""
    echo "🔧 To force stop everything:"
    echo "   docker ps --filter 'name=intelligent_crawl4ai' -q | xargs -r docker stop"
    echo "   docker ps --filter 'name=intelligent_crawl4ai' -q | xargs -r docker rm"
else
    echo "✅ All Intelligent Crawl4AI containers stopped successfully!"
fi

echo ""
echo "📋 Available options for cleanup:"
echo "   🗂️  Keep data volumes (default)"
echo "   🗑️  Remove data volumes: ./stop.sh --remove-volumes"
echo "   🧹 Force cleanup all: ./stop.sh --force-cleanup"

# Handle command line arguments
case "${1:-}" in
    --remove-volumes|--volumes|-v)
        echo ""
        echo "🗑️  Removing data volumes..."
        docker volume ls -q --filter "name=compose_" | xargs -r docker volume rm
        echo "✅ Data volumes removed"
        ;;
    --force-cleanup|--force|-f)
        echo ""
        echo "🧹 Force cleanup mode..."
        
        # Stop all crawl4ai related containers
        docker ps -a --filter "name=crawl4ai" -q | xargs -r docker stop
        docker ps -a --filter "name=crawl4ai" -q | xargs -r docker rm
        
        # Stop all compose related containers
        docker ps -a --filter "name=compose-" -q | xargs -r docker stop  
        docker ps -a --filter "name=compose-" -q | xargs -r docker rm
        
        # Remove networks
        docker network ls --filter "name=compose" -q | xargs -r docker network rm
        
        # Remove volumes
        docker volume ls -q --filter "name=compose_" | xargs -r docker volume rm
        
        echo "✅ Force cleanup completed"
        ;;
    --help|-h)
        echo ""
        echo "🆘 Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  (no args)          Stop containers, keep data volumes"
        echo "  --remove-volumes   Stop containers and remove data volumes"
        echo "  --force-cleanup    Force stop and remove everything"
        echo "  --help             Show this help message"
        echo ""
        ;;
esac

echo ""
echo "🎉 Stop script completed!"
echo ""
echo "💡 Quick commands:"
echo "   📊 Check status: docker ps --filter 'name=intelligent_crawl4ai'"
echo "   🗃️  List volumes: docker volume ls --filter 'name=compose_'"
echo "   🌐 List networks: docker network ls --filter 'name=compose'"
echo "   🚀 Restart: ./start.sh"
