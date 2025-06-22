# Intelligent Crawl4AI Agent: Dual AI Architecture Web Scraping

A powerful, intelligent web scraping system that combines Claude's strategic planning capabilities with local AI execution for cost-effective, scalable data extraction.

## 🚀 Key Features

### **Dual AI Architecture**
- **Claude (via MCP)**: Intelligent planning, strategy selection, and coordination
- **Local AI (Ollama)**: Autonomous execution, pattern recognition, and extraction
- **ChromaDB**: Vector memory for learning and pattern storage

### **Intelligent Strategy Selection**
- **Automatic Website Analysis**: AI analyzes site structure, frameworks, and content patterns
- **Dynamic Strategy Selection**: Chooses optimal Crawl4AI strategy (CSS, LLM, JSON-CSS, Custom)
- **Adaptive Execution**: Adjusts approach based on site characteristics and anti-bot measures

### **High-Volume Automation**
- **Massive Concurrency**: Process 500-2000 URLs per minute
- **Distributed Processing**: 50+ workers with intelligent load balancing
- **Session Management**: Persistent login sessions across multiple sites
- **Anti-Detection**: Proxy rotation, user-agent switching, human-like behavior

### **Advanced Capabilities**
- **Authentication Automation**: Login, 2FA, email verification
- **CAPTCHA Solving**: reCAPTCHA, hCaptcha, image CAPTCHAs
- **Form Automation**: Intelligent form detection and completion
- **Progressive Learning**: System improves through experience

## 🏗️ Architecture

```
Claude Desktop → MCP Orchestrator → AI Strategy Selector → High-Volume Executor
                      ↓                    ↓                    ↓
                 ChromaDB Memory      Ollama Analysis      Worker Pool + Browsers
```

## 📦 Installation

### Prerequisites
- Python 3.8+
- Docker & Docker Compose
- Claude Desktop App
- 16GB+ RAM recommended

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/intelligent-crawl4ai-agent.git
cd intelligent-crawl4ai-agent

# Run setup script
./scripts/setup.sh

# Start the services
docker-compose up -d

# Configure Claude Desktop (see config/claude_desktop_config.json)
```

### Manual Installation

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1
ollama pull nomic-embed-text

# Install Playwright browsers
playwright install chromium

# Set up environment variables
cp config/environment.template.env .env
# Edit .env with your settings
```

## 🎯 Usage Examples

### Basic Intelligent Scraping
```python
# Via Claude Desktop MCP
"Scrape company information from these business directory URLs: [list of URLs]"
# Agent automatically analyzes sites and selects optimal strategies
```

### High-Volume Campaign
```python
# Process thousands of URLs
"Submit a high-volume job to scrape 10,000 restaurant listings from Yelp and Yellow Pages"
# System distributes across worker pool with intelligent batching
```

### Authentication Required
```python
# Handle login automation
"Scrape LinkedIn company profiles - use provided credentials to handle authentication"
# Agent detects login requirements and automates the process
```

## 📊 Performance

- **Throughput**: 500-2000 URLs per minute
- **Concurrency**: Up to 500 simultaneous browser sessions
- **Success Rate**: 95%+ with intelligent retries
- **Scaling**: Horizontal scaling across multiple machines

## 🔧 Configuration

### Claude Desktop Setup
```json
{
  "mcpServers": {
    "intelligent_crawl4ai_agent": {
      "command": "python",
      "args": ["/path/to/src/mcp_servers/intelligent_orchestrator.py"],
      "env": {
        "OLLAMA_URL": "http://localhost:11434",
        "CHROMADB_URL": "http://localhost:8000"
      }
    }
  }
}
```

### Environment Variables
```bash
# AI Services
OLLAMA_URL=http://localhost:11434
CHROMADB_URL=http://localhost:8000

# High-Volume Processing
REDIS_URL=redis://localhost:6379
POSTGRES_URL=postgresql://user:pass@localhost:5432/scraping

# External Services (Optional)
CAPTCHA_API_KEY=your_2captcha_key
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password
```

## 📚 Documentation

- [Installation Guide](docs/installation.md)
- [Configuration Guide](docs/configuration.md)
- [API Reference](docs/api.md)
- [Strategy Selection Guide](docs/strategies.md)
- [High-Volume Processing](docs/high_volume.md)
- [Troubleshooting](docs/troubleshooting.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Crawl4AI](https://github.com/unclecode/crawl4ai) - Powerful web crawling framework
- [Anthropic MCP](https://modelcontextprotocol.io/) - Model Context Protocol
- [Ollama](https://ollama.ai/) - Local AI model serving

## 📞 Support

- [Documentation](docs/)
- [Issues](https://github.com/yourusername/intelligent-crawl4ai-agent/issues)
- [Discussions](https://github.com/yourusername/intelligent-crawl4ai-agent/discussions)
