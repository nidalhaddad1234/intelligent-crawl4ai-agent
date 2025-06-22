#!/bin/bash
# =============================================================================
# Intelligent Crawl4AI Agent - Docker Build and Management Script
# =============================================================================
# Convenient script for building, running, and managing Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="intelligent-crawl4ai"
DOCKERFILE_PATH="docker/Dockerfile.agent"
COMPOSE_FILE="docker-compose.yml"

# Default values
BUILD_TARGET="production"
TAG_NAME="latest"
DOCKER_REGISTRY=""
PUSH_TO_REGISTRY=false
RUN_TESTS=false
CLEANUP_BEFORE=false
VERBOSE=false

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌${NC} $1" >&2
}

show_help() {
    cat << EOF
🎯 Intelligent Crawl4AI Agent - Docker Management Script

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    build       Build Docker image
    run         Run container interactively
    start       Start services with docker-compose
    stop        Stop services
    restart     Restart services
    logs        Show container logs
    test        Run test suite
    clean       Clean up Docker resources
    push        Push image to registry
    help        Show this help message

BUILD OPTIONS:
    --target STAGE      Build target stage (production|development) [default: production]
    --tag TAG           Docker image tag [default: latest]
    --registry URL      Docker registry URL for pushing
    --push              Push to registry after build
    --no-cache          Build without using cache
    --test              Run tests after build

RUN OPTIONS:
    --env ENV_FILE      Environment file to use
    --port PORT         Port mapping [default: 8811:8811]
    --volume PATH       Additional volume mount
    --detach            Run in background
    --rm                Remove container when it stops

GENERAL OPTIONS:
    --cleanup           Clean up before building
    --verbose           Enable verbose output
    --help              Show this help message

EXAMPLES:
    # Build production image
    $0 build

    # Build development image with tests
    $0 build --target development --test

    # Build and push to registry
    $0 build --registry myregistry.com --push

    # Run container interactively
    $0 run

    # Start all services
    $0 start

    # View logs
    $0 logs --follow

    # Clean up everything
    $0 clean --all

ENVIRONMENT:
    Copy docker/.env.docker to .env and customize for your environment.

EOF
}

check_requirements() {
    log "🔍 Checking requirements..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_warning "docker-compose not found. Some features may not work."
    fi
    
    # Check if Dockerfile exists
    if [[ ! -f "$DOCKERFILE_PATH" ]]; then
        log_error "Dockerfile not found at $DOCKERFILE_PATH"
        exit 1
    fi
    
    log_success "Requirements check passed"
}

# =============================================================================
# Build Functions
# =============================================================================

build_image() {
    local target="$1"
    local tag="$2"
    local no_cache="$3"
    
    log "🏗️ Building Docker image..."
    log "📁 Target: $target"
    log "🏷️ Tag: $PROJECT_NAME:$tag"
    
    local build_args=(
        "docker" "build"
        "--target" "$target"
        "-t" "$PROJECT_NAME:$tag"
        "-f" "$DOCKERFILE_PATH"
    )
    
    if [[ "$no_cache" == "true" ]]; then
        build_args+=("--no-cache")
        log "🚫 Cache disabled"
    fi
    
    if [[ "$VERBOSE" == "true" ]]; then
        build_args+=("--progress=plain")
    fi
    
    build_args+=(".")
    
    log "🔧 Build command: ${build_args[*]}"
    
    if "${build_args[@]}"; then
        log_success "Docker image built successfully"
        
        # Show image info
        local image_size=$(docker images "$PROJECT_NAME:$tag" --format "{{.Size}}")
        log "📏 Image size: $image_size"
        
        return 0
    else
        log_error "Docker build failed"
        return 1
    fi
}

run_tests() {
    local tag="$1"
    
    log "🧪 Running test suite..."
    
    # Run the test container
    if docker run --rm \
        -e "APP_ENV=test" \
        -e "LOG_LEVEL=DEBUG" \
        "$PROJECT_NAME:$tag" \
        strategy-test; then
        log_success "All tests passed"
        return 0
    else
        log_error "Tests failed"
        return 1
    fi
}

push_image() {
    local registry="$1"
    local tag="$2"
    
    local full_tag="$registry/$PROJECT_NAME:$tag"
    
    log "📤 Pushing image to registry..."
    log "🏷️ Full tag: $full_tag"
    
    # Tag for registry
    if docker tag "$PROJECT_NAME:$tag" "$full_tag"; then
        log_success "Image tagged for registry"
    else
        log_error "Failed to tag image"
        return 1
    fi
    
    # Push to registry
    if docker push "$full_tag"; then
        log_success "Image pushed successfully"
        return 0
    else
        log_error "Failed to push image"
        return 1
    fi
}

# =============================================================================
# Run Functions
# =============================================================================

run_container() {
    local tag="$1"
    local env_file="$2"
    local port="$3"
    local volumes=("${@:4}")
    
    log "🚀 Running container..."
    
    local run_args=(
        "docker" "run"
        "--name" "${PROJECT_NAME}-container"
        "-p" "$port"
    )
    
    if [[ -n "$env_file" && -f "$env_file" ]]; then
        run_args+=("--env-file" "$env_file")
        log "📋 Using environment file: $env_file"
    fi
    
    for volume in "${volumes[@]}"; do
        run_args+=("-v" "$volume")
        log "💾 Volume mount: $volume"
    done
    
    run_args+=("--rm" "-it" "$PROJECT_NAME:$tag")
    
    log "🔧 Run command: ${run_args[*]}"
    
    "${run_args[@]}"
}

# =============================================================================
# Compose Functions
# =============================================================================

start_services() {
    log "🐳 Starting services with docker-compose..."
    
    if [[ -f "$COMPOSE_FILE" ]]; then
        if docker-compose -f "$COMPOSE_FILE" up -d; then
            log_success "Services started successfully"
            
            # Show running services
            docker-compose -f "$COMPOSE_FILE" ps
        else
            log_error "Failed to start services"
            return 1
        fi
    else
        log_error "docker-compose.yml not found at $COMPOSE_FILE"
        return 1
    fi
}

stop_services() {
    log "🛑 Stopping services..."
    
    if docker-compose -f "$COMPOSE_FILE" down; then
        log_success "Services stopped successfully"
    else
        log_error "Failed to stop services"
        return 1
    fi
}

show_logs() {
    local service="$1"
    local follow="$2"
    
    local logs_args=("docker-compose" "-f" "$COMPOSE_FILE" "logs")
    
    if [[ "$follow" == "true" ]]; then
        logs_args+=("-f")
    fi
    
    if [[ -n "$service" ]]; then
        logs_args+=("$service")
    fi
    
    "${logs_args[@]}"
}

# =============================================================================
# Cleanup Functions
# =============================================================================

cleanup_docker() {
    local cleanup_all="$1"
    
    log "🧹 Cleaning up Docker resources..."
    
    # Remove stopped containers
    if docker container prune -f; then
        log_success "Removed stopped containers"
    fi
    
    # Remove unused images
    if docker image prune -f; then
        log_success "Removed unused images"
    fi
    
    # Remove unused volumes
    if docker volume prune -f; then
        log_success "Removed unused volumes"
    fi
    
    # Remove unused networks
    if docker network prune -f; then
        log_success "Removed unused networks"
    fi
    
    if [[ "$cleanup_all" == "true" ]]; then
        log_warning "Performing full cleanup (this will remove ALL unused Docker resources)"
        if docker system prune -a -f; then
            log_success "Full cleanup completed"
        fi
    fi
}

# =============================================================================
# Main Command Processing
# =============================================================================

process_command() {
    local command="$1"
    shift
    
    case "$command" in
        "build")
            local no_cache=false
            local test_after=false
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --target)
                        BUILD_TARGET="$2"
                        shift 2
                        ;;
                    --tag)
                        TAG_NAME="$2"
                        shift 2
                        ;;
                    --registry)
                        DOCKER_REGISTRY="$2"
                        shift 2
                        ;;
                    --push)
                        PUSH_TO_REGISTRY=true
                        shift
                        ;;
                    --no-cache)
                        no_cache=true
                        shift
                        ;;
                    --test)
                        test_after=true
                        shift
                        ;;
                    *)
                        log_error "Unknown build option: $1"
                        exit 1
                        ;;
                esac
            done
            
            if build_image "$BUILD_TARGET" "$TAG_NAME" "$no_cache"; then
                if [[ "$test_after" == "true" ]]; then
                    run_tests "$TAG_NAME"
                fi
                
                if [[ "$PUSH_TO_REGISTRY" == "true" && -n "$DOCKER_REGISTRY" ]]; then
                    push_image "$DOCKER_REGISTRY" "$TAG_NAME"
                fi
            fi
            ;;
            
        "run")
            local env_file=""
            local port="8811:8811"
            local volumes=()
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --env)
                        env_file="$2"
                        shift 2
                        ;;
                    --port)
                        port="$2"
                        shift 2
                        ;;
                    --volume)
                        volumes+=("$2")
                        shift 2
                        ;;
                    *)
                        log_error "Unknown run option: $1"
                        exit 1
                        ;;
                esac
            done
            
            run_container "$TAG_NAME" "$env_file" "$port" "${volumes[@]}"
            ;;
            
        "start")
            start_services
            ;;
            
        "stop")
            stop_services
            ;;
            
        "restart")
            stop_services
            start_services
            ;;
            
        "logs")
            local service=""
            local follow=false
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --service)
                        service="$2"
                        shift 2
                        ;;
                    --follow|-f)
                        follow=true
                        shift
                        ;;
                    *)
                        log_error "Unknown logs option: $1"
                        exit 1
                        ;;
                esac
            done
            
            show_logs "$service" "$follow"
            ;;
            
        "test")
            run_tests "$TAG_NAME"
            ;;
            
        "clean")
            local cleanup_all=false
            
            while [[ $# -gt 0 ]]; do
                case $1 in
                    --all)
                        cleanup_all=true
                        shift
                        ;;
                    *)
                        log_error "Unknown clean option: $1"
                        exit 1
                        ;;
                esac
            done
            
            cleanup_docker "$cleanup_all"
            ;;
            
        "push")
            if [[ -z "$DOCKER_REGISTRY" ]]; then
                log_error "Registry URL required for push command"
                exit 1
            fi
            push_image "$DOCKER_REGISTRY" "$TAG_NAME"
            ;;
            
        "help"|"--help"|"-h")
            show_help
            ;;
            
        *)
            log_error "Unknown command: $command"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# =============================================================================
# Main Execution
# =============================================================================

main() {
    # Parse global options
    while [[ $# -gt 0 ]]; do
        case $1 in
            --cleanup)
                CLEANUP_BEFORE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            --*)
                # Keep other options for command processing
                break
                ;;
            *)
                # This is the command
                break
                ;;
        esac
    done
    
    local command="${1:-help}"
    shift || true
    
    # Show banner
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║              🎯 Intelligent Crawl4AI Agent                      ║"
    echo "║                   Docker Management Script                       ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    # Check requirements
    check_requirements
    
    # Cleanup if requested
    if [[ "$CLEANUP_BEFORE" == "true" ]]; then
        cleanup_docker false
    fi
    
    # Process command
    process_command "$command" "$@"
    
    log_success "Operation completed successfully! 🎉"
}

# Execute main function
main "$@"
