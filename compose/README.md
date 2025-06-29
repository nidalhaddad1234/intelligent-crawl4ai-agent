# Docker Compose Configurations

This directory contains various Docker Compose configurations for different deployment scenarios.

## Available Configurations

### docker-compose.yml
The main production configuration with all services.
```bash
docker-compose -f docker/compose/docker-compose.yml up -d
```

### docker-compose.dev.yml
Development configuration with hot-reloading and debug features.
```bash
docker-compose -f docker/compose/docker-compose.dev.yml up
```

### docker-compose.local.yml
Lightweight local configuration for testing.
```bash
docker-compose -f docker/compose/docker-compose.local.yml up
```

### docker-compose.local-full.yml
Full local configuration with all services including monitoring.
```bash
docker-compose -f docker/compose/docker-compose.local-full.yml up
```

## Notes

- All configurations assume you're running from the project root directory
- Environment variables should be set in the root `.env` file
- For production deployments, use the main `docker-compose.yml`
- For development, use `docker-compose.dev.yml` for hot-reloading

## Quick Start

From the project root:
```bash
# Production
docker-compose -f docker/compose/docker-compose.yml up -d

# Development
docker-compose -f docker/compose/docker-compose.dev.yml up

# Stop all services
docker-compose -f docker/compose/docker-compose.yml down
```
