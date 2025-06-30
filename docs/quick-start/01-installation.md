# 📦 01. Installation

> **Get the Intelligent Crawl4AI Agent installed in 2 minutes**

This guide covers everything you need to install and verify the agent is working correctly on your system.

---

## 🚀 Quick Install

### **Method 1: Git Clone (Recommended)**
```bash
# Clone the repository
git clone https://github.com/yourusername/intelligent-crawl4ai-agent
cd intelligent-crawl4ai-agent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c \"from src.agents.intelligent_analyzer import IntelligentAnalyzer; print('✅ Installation successful!')\"
```

### **Method 2: Development Install**
```bash
# Clone and install in development mode
git clone https://github.com/yourusername/intelligent-crawl4ai-agent
cd intelligent-crawl4ai-agent
pip install -e .

# Run tests to verify
python -m pytest tests/ -v
```

---

## 🔍 Verify Installation

### **Test Core Components**
```python
# test_installation.py
import asyncio
from src.agents.intelligent_analyzer import IntelligentAnalyzer
from ai_core.core.hybrid_ai_service import create_production_ai_service

async def test_installation():
    # Test AI service creation
    ai_service = create_production_ai_service()
    print(\"✅ AI service created successfully\")
    
    # Test analyzer initialization
    analyzer = IntelligentAnalyzer(llm_service=ai_service)
    print(\"✅ Intelligent analyzer initialized\")
    
    # Test provider status (will show which providers are available)
    try:
        status = ai_service.get_provider_status()
        available_providers = [name for name, info in status.items() if info.get('enabled')]
        print(f\"✅ Available AI providers: {', '.join(available_providers) or 'None (will need API keys)'}\")
    except Exception as e:
        print(f\"⚠️  Provider check failed: {e} (this is normal without API keys)\")
    
    print(\"\\n🎉 Installation verification complete!\")

# Run the test
asyncio.run(test_installation())
```

Run this test:
```bash
python test_installation.py
```

**Expected output:**
```
✅ AI service created successfully
✅ Intelligent analyzer initialized
✅ Available AI providers: None (will need API keys)

🎉 Installation verification complete!
```

---

## 🔧 System Requirements

### **Minimum Requirements**
- **Python**: 3.8 or higher
- **RAM**: 4GB minimum
- **Storage**: 2GB free space
- **Network**: Internet connection for AI providers

### **Recommended Setup**
- **Python**: 3.9+ (better async performance)
- **RAM**: 8GB+ (for concurrent extractions)
- **Storage**: 10GB+ (for logs, profiles, schemas)
- **CPU**: Multi-core (better for parallel processing)

### **For Identity Features** *(Q1 2025)*
- **Docker**: 20.10.0+ with 4GB RAM allocated
- **VNC Viewer**: For headful browser interaction
- **Storage**: Additional 5GB for browser profiles

---

## 🐳 Docker Installation (Optional)

### **Basic Docker Setup**
```bash
# Build the container
docker build -t intelligent-crawler .

# Run basic extraction
docker run -e OPENROUTER_API_KEY=\"your_key\" \\
  intelligent-crawler \\
  python -c \"print('Container is working!')\"
```

### **Docker Compose (Recommended for Development)**
```yaml
# docker-compose.yml
version: '3.8'
services:
  crawler:
    build: .
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    ports:
      - \"8080:8080\"
```

Run with:
```bash
docker-compose up -d
```

---

## 🌍 Environment Setup

### **Create Environment File**
```bash
# Copy example environment
cp .env.example .env

# Edit with your settings
nano .env  # or use your preferred editor
```

### **Basic .env Configuration**
```bash
# .env file

# AI Provider Keys (add at least one)
OPENROUTER_API_KEY=\"\"           # Recommended: many models, good pricing
DEEPSEEK_API_KEY=\"\"             # Cheapest: $0.14/1M tokens
GROQ_API_KEY=\"\"                 # Fastest: 500+ tokens/sec
OPENAI_API_KEY=\"\"               # Premium: most reliable
ANTHROPIC_API_KEY=\"\"            # Smart: best reasoning

# Local AI (optional)
OLLAMA_URL=\"http://localhost:11434\"
OLLAMA_MODEL=\"llama3.2:3b\"

# Vector Search (optional)
QDRANT_URL=\"http://localhost:6333\"
QDRANT_API_KEY=\"\"

# Identity Features (Q1 2025)
ENABLE_IDENTITY_CRAWLING=false
BROWSER_VNC_PORT=5900
PROFILES_STORAGE_PATH=\"./data/profiles\"

# Performance
MAX_CONCURRENT_EXTRACTIONS=5
DEFAULT_TIMEOUT_SECONDS=30
ENABLE_CACHING=true
```

---

## 🔄 Update Installation

### **Update to Latest Version**
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt --upgrade

# Verify update
python -c \"from src import __version__; print(f'Version: {__version__}')\"
```

### **Update Docker Installation**
```bash
# Rebuild container with latest changes
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

---

## 🛠️ Development Installation

### **Full Development Setup**
```bash
# Clone with development tools
git clone https://github.com/yourusername/intelligent-crawl4ai-agent
cd intelligent-crawl4ai-agent

# Install with dev dependencies
pip install -e \".[dev]\"

# Install pre-commit hooks
pre-commit install

# Run full test suite
pytest tests/ --cov=src --cov-report=html

# Start development server
python web_ui_server.py
```

### **Development Tools Included**
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Code linting
- **pre-commit**: Git hooks
- **coverage**: Test coverage reporting

---

## ✅ Installation Complete!

### **What You Have Now**
- ✅ Intelligent Crawl4AI Agent installed and verified
- ✅ Core dependencies configured
- ✅ Environment file ready for API keys
- ✅ Development tools available (if using dev install)

### **What's Next**
1. **[🤖 Setup AI Providers](03-ai-providers.md)** - Add your API keys
2. **[🎯 First Extraction](02-first-extraction.md)** - Extract your first website

### **Need Help?**
- **Installation issues**: [Troubleshooting Guide](../troubleshooting/common-issues.md)
- **Environment problems**: [Configuration Guide](../getting-started/configuration.md)
- **Docker issues**: [Docker Deployment Guide](../deployment/docker/basic-deployment.md)

---

**Ready for your first extraction?**

👉 **[Next: First Extraction →](02-first-extraction.md)**

*You'll extract data from a real website in the next 3 minutes*
