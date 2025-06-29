# Installation Guide - AI-First Web Scraping

## Overview

The AI-First Intelligent Scraper has a simplified installation process. No more complex strategy configurations or multiple services - just install and start chatting!

## Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Storage**: 2GB free space
- **OS**: Linux, macOS, or Windows (with WSL2)

### GPU (Optional but Recommended)
- Any NVIDIA GPU with 4GB+ VRAM
- Speeds up AI planning by 5-10x

## Quick Start (5 Minutes)

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/intelligent-crawl4ai-agent.git
cd intelligent-crawl4ai-agent
```

### 2. Install Dependencies
```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python packages
pip install -r requirements.txt
```

### 3. Install Ollama (Local AI)
```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows (in WSL2)
curl -fsSL https://ollama.com/install.sh | sh
```

### 4. Download AI Model
```bash
# Recommended model (fast, runs on most hardware)
ollama pull deepseek-coder:1.3b

# Alternative models
ollama pull llama3.2:3b      # Better understanding, needs more RAM
ollama pull phi3:mini         # Smallest, fastest
ollama pull mistral:7b        # Best quality, needs GPU
```

### 5. Start the System
```bash
python web_ui_server.py
```

### 6. Open Browser
Navigate to: http://localhost:8888

That's it! Start chatting with your AI scraping assistant.

## Detailed Installation Options

### Option 1: Minimal Installation (Just Chat)
Perfect for trying out the system.

```bash
# Install only core dependencies
pip install fastapi uvicorn aiohttp crawl4ai

# Start with defaults
python web_ui_server.py
```

### Option 2: Full Installation (With Learning)
Includes the self-learning system.

```bash
# Install all dependencies
pip install -r requirements.txt

# Start ChromaDB for learning memory
docker run -d -p 8000:8000 chromadb/chroma

# Install Playwright for dynamic content
playwright install chromium

# Start with learning enabled
LEARNING_ENABLED=true python web_ui_server.py
```

### Option 3: Docker Installation (Production)
Everything containerized and ready to scale.

```bash
# Build and start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f web-ui
```

### Option 4: Development Installation
For contributing or customization.

```bash
# Clone with git history
git clone https://github.com/yourusername/intelligent-crawl4ai-agent.git
cd intelligent-crawl4ai-agent

# Install in development mode
pip install -e .
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/
```

## Configuration

### Basic Configuration (.env)
Create a `.env` file in the project root:

```bash
# AI Configuration
AI_MODEL=deepseek-coder:1.3b    # Choose your model
OLLAMA_URL=http://localhost:11434

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=8888

# Features
LEARNING_ENABLED=true            # Enable self-learning
DEBUG=false                      # Production mode
```

### Advanced Configuration
```bash
# Performance Tuning
PLAN_CACHE_SIZE=1000            # Cache common plans
MAX_WORKERS=10                  # Parallel executions
TOOL_TIMEOUT=30                 # Tool execution timeout

# Learning System
LEARNING_THRESHOLD=0.7          # Minimum confidence to learn
TEACHER_MODE=false              # Enable Claude teacher
PATTERN_RETENTION_DAYS=90       # How long to keep patterns

# Database (auto-configured)
DATABASE_TYPE=sqlite            # or postgresql
DATABASE_URL=sqlite:///data/scraping.db
```

## Platform-Specific Instructions

### macOS
```bash
# Install Xcode tools if needed
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.8+
brew install python@3.11

# Continue with standard installation
```

### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv curl

# Continue with standard installation
```

### Windows (WSL2 Recommended)
```powershell
# Install WSL2 (in PowerShell as Admin)
wsl --install

# Restart and open Ubuntu terminal
# Follow Ubuntu instructions above
```

### Windows (Native)
```powershell
# Install Python from python.org
# Install Git from git-scm.com

# In Command Prompt or PowerShell:
git clone https://github.com/yourusername/intelligent-crawl4ai-agent.git
cd intelligent-crawl4ai-agent

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

# Install Ollama from https://ollama.ai
# Then continue with model download
```

## Verification

### 1. Check AI Service
```bash
# Test Ollama
curl http://localhost:11434/api/tags

# Should return list of installed models
```

### 2. Check Web Interface
```bash
# Test API
curl http://localhost:8888/health

# Should return: {"status": "healthy", ...}
```

### 3. Test AI Planning
```bash
curl -X POST http://localhost:8888/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, can you help me scrape data?"}'

# Should return friendly AI response
```

## Troubleshooting

### "Ollama not found"
```bash
# Verify installation
ollama version

# If not found, reinstall:
curl -fsSL https://ollama.com/install.sh | sh
```

### "Model not found"
```bash
# List installed models
ollama list

# Pull model again
ollama pull deepseek-coder:1.3b
```

### "Port 8888 already in use"
```bash
# Change port in .env
WEB_PORT=8889

# Or find and kill process
lsof -i :8888
kill -9 <PID>
```

### "Out of memory"
```bash
# Use smaller model
AI_MODEL=phi3:mini

# Or reduce batch size
MAX_WORKERS=5
```

### "ChromaDB connection failed"
```bash
# Start ChromaDB
docker run -d -p 8000:8000 chromadb/chroma

# Or disable learning
LEARNING_ENABLED=false
```

## Performance Optimization

### For Slow Hardware
```bash
# .env settings for low-end systems
AI_MODEL=phi3:mini              # Smallest model
MAX_WORKERS=3                   # Reduce parallelism
PLAN_CACHE_SIZE=5000           # More caching
LEARNING_ENABLED=false         # Disable learning initially
```

### For Fast Hardware (GPU)
```bash
# .env settings for high-end systems
AI_MODEL=mistral:7b            # Best model
MAX_WORKERS=50                 # Maximum parallelism
OLLAMA_NUM_GPU=1              # Use GPU
TOOL_TIMEOUT=60               # Allow longer operations
```

## Updating

### Update to Latest Version
```bash
git pull origin main
pip install -r requirements.txt --upgrade
```

### Update AI Models
```bash
ollama pull deepseek-coder:1.3b
```

## Uninstallation

### Remove Application
```bash
# Stop services
docker-compose down

# Remove project
cd ..
rm -rf intelligent-crawl4ai-agent
```

### Remove Ollama (Optional)
```bash
# Linux/macOS
sudo rm -rf /usr/local/bin/ollama
sudo rm -rf ~/.ollama

# Remove models
rm -rf ~/.ollama/models
```

## Next Steps

1. **Start Chatting**: Open http://localhost:8888
2. **Read Usage Guide**: Check [AI Architecture](ai-architecture.md)
3. **Try Examples**: See [API Reference](api.md) for examples
4. **Enable Learning**: Set `LEARNING_ENABLED=true` for improvements
5. **Join Community**: Report issues and contribute!

## Getting Help

- **Quick Start Issues**: Check troubleshooting above
- **GitHub Issues**: [Report Problems](https://github.com/yourusername/intelligent-crawl4ai-agent/issues)
- **Documentation**: [Full Docs](https://github.com/yourusername/intelligent-crawl4ai-agent/docs)

Welcome to AI-First Web Scraping! 🚀
