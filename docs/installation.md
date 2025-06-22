# Installation Guide

## Prerequisites

Before installing the Intelligent Crawl4AI Agent, ensure you have the following prerequisites:

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- **RAM**: 16GB+ recommended (8GB minimum)
- **Storage**: 10GB+ free space
- **CPU**: 4+ cores recommended
- **GPU**: NVIDIA GPU with 8GB+ VRAM (optional, for faster AI processing)

### Software Prerequisites
- **Python**: 3.8 or higher
- **Docker**: Latest version with Docker Compose
- **Git**: For version control
- **Claude Desktop**: For MCP integration

## Quick Installation

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/intelligent-crawl4ai-agent.git
cd intelligent-crawl4ai-agent
```

### 2. Run the Setup Script
```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The setup script will automatically:
- Install Python dependencies
- Set up Ollama and download AI models
- Start Docker services
- Configure the environment

### 3. Configure Claude Desktop
```bash
# Copy the configuration to Claude Desktop
cp config/claude_desktop_config.json ~/.config/Claude\ Desktop/claude_desktop_config.json
```

Restart Claude Desktop to load the new configuration.

## Manual Installation

If you prefer to install manually or the setup script fails:

### 1. Python Environment
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium --with-deps
```

### 2. Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve &

# Pull required models
ollama pull llama3.1
ollama pull nomic-embed-text
```

### 3. Start Services
```bash
# Start Docker services
docker-compose up -d

# Wait for services to be ready
sleep 30

# Check service health
docker-compose ps
```

### 4. Environment Configuration
Create a `.env` file:
```bash
cp .env.example .env
# Edit .env with your configuration
```

## Docker-Only Installation

For a Docker-only setup without local Python installation:

```bash
# Clone repository
git clone https://github.com/yourusername/intelligent-crawl4ai-agent.git
cd intelligent-crawl4ai-agent

# Start all services
docker-compose up -d

# The agent will be available at localhost:8811
```

## Verification

### Test the Installation
```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Test ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# Test Redis
redis-cli ping

# Test PostgreSQL
psql -h localhost -U scraper_user -d intelligent_scraping -c "SELECT 1;"
```

### Test Claude Desktop Integration
Open Claude Desktop and try this command:
```
"Analyze and scrape https://example.com for company information"
```

## Troubleshooting

### Common Issues

**Ollama Models Not Downloading**
```bash
# Manually download models
ollama pull llama3.1
ollama pull nomic-embed-text

# Check available models
ollama list
```

**Docker Services Not Starting**
```bash
# Check Docker daemon
sudo systemctl status docker

# Check service logs
docker-compose logs chromadb
docker-compose logs ollama
```

**Claude Desktop Not Connecting**
1. Verify the config file path is correct
2. Restart Claude Desktop
3. Check the Python path in the config
4. Ensure all services are running

**Memory Issues**
```bash
# Reduce Docker memory usage
docker system prune -f

# Adjust worker limits in .env
MAX_WORKERS=25
MAX_CONCURRENT_PER_WORKER=5
```

### Performance Optimization

**For High-Volume Usage**
```bash
# Increase resource limits
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Optimize Docker
sudo tee /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF
sudo systemctl restart docker
```

**For GPU Acceleration**
```bash
# Install NVIDIA Docker support
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

sudo apt-get update && sudo apt-get install -y nvidia-docker2
sudo systemctl restart docker
```

## Next Steps

After successful installation:

1. **Read the Configuration Guide**: [configuration.md](configuration.md)
2. **Try the Examples**: Check out [examples/](../examples/)
3. **Explore the API**: Review [api.md](api.md)
4. **Monitor Performance**: Access Grafana at http://localhost:3000

## Getting Help

- **Documentation**: Check the [docs/](.) directory
- **Issues**: Report problems on GitHub Issues
- **Discussions**: Join GitHub Discussions for questions

## Uninstallation

To completely remove the system:
```bash
# Stop and remove containers
docker-compose down -v

# Remove Docker images
docker rmi $(docker images | grep intelligent-crawl4ai | awk '{print $3}')

# Remove data volumes
docker volume prune -f

# Remove Python environment
rm -rf venv/

# Remove Ollama models (optional)
ollama rm llama3.1
ollama rm nomic-embed-text
```
