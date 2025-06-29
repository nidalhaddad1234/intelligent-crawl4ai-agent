#!/bin/bash
# Docker Compose convenience wrapper
# This script simplifies running docker-compose with the new directory structure

# Default to production compose file
COMPOSE_FILE="${COMPOSE_FILE:-docker/compose/docker-compose.yml}"

# Check if a specific variant was requested
case "$1" in
    dev|development)
        COMPOSE_FILE="docker/compose/docker-compose.dev.yml"
        shift
        ;;
    local)
        COMPOSE_FILE="docker/compose/docker-compose.local.yml"
        shift
        ;;
    local-full)
        COMPOSE_FILE="docker/compose/docker-compose.local-full.yml"
        shift
        ;;
    prod|production)
        COMPOSE_FILE="docker/compose/docker-compose.yml"
        shift
        ;;
esac

# Run docker-compose with the selected file
docker compose -f "$COMPOSE_FILE" "$@"
