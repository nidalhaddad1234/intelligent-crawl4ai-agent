# 🕷️ Intelligent Crawl4AI Agent

> **Enterprise-grade autonomous web data extraction with AI-powered optimization**

An advanced, AI-first web extraction platform featuring multi-provider intelligence, autonomous tool selection, real-time streaming, and enterprise-scale architecture. Built for complex data extraction scenarios requiring reliability, scalability, and intelligent adaptation.

## 🧠 Core Intelligence Features

### **Multi-AI Provider System**
- **6 AI Providers**: OpenRouter, DeepSeek, Groq, OpenAI, Anthropic, Ollama
- **Automatic Failover**: Seamless provider switching on failures
- **Cost Optimization**: Intelligent routing to minimize API costs
- **Performance Monitoring**: Real-time success rate tracking and adaptation

### **Autonomous Tool Selection**
- **AI-Powered Analysis**: Automatically selects optimal tools based on website characteristics
- **Context-Aware Configuration**: Dynamic parameter optimization for each extraction
- **Learning System**: Improves selection accuracy from successful patterns
- **Fallback Strategies**: Multi-level tool chains for maximum reliability

### **Real-Time Intelligence**
- **Background Job Processing**: Parallel execution with live progress tracking
- **WebSocket Communication**: Real-time updates and bidirectional messaging
- **Live Data Streaming**: Continuous monitoring and extraction feeds
- **Pattern Learning**: Stores and reuses successful extraction patterns

## 🏗️ Architecture Highlights

### **Service-Oriented Design**
- **AI Core**: Multi-provider orchestration and intelligent planning
- **Extraction Engine**: Advanced strategies with platform-specific optimizations
- **Real-Time Layer**: WebSocket communication and streaming capabilities
- **Learning System**: Pattern memory and continuous optimization

### **Advanced Extraction Strategies**
- **AI-Enhanced**: Context-aware intelligent extraction
- **Adaptive Crawler**: Self-optimizing based on website characteristics
- **Hybrid Approaches**: Combines multiple methods for reliability
- **Platform-Specific**: Optimized extractors for LinkedIn, Amazon, Facebook, Yelp

### **Enterprise Capabilities**
- **Scalable Architecture**: Multi-worker deployment with load balancing
- **Monitoring Integration**: Grafana dashboards and Prometheus metrics
- **Production Docker**: Multi-service containerized deployment
- **Authentication Systems**: CAPTCHA solving and login automation

## 🚀 Quick Start

### **Installation**
```bash
# Clone and setup
git clone <your-repo-url>
cd intelligent-crawl4ai-agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure AI providers (at least one required)
cp .env.example .env
# Edit .env with your API keys
```

### **Essential Configuration**
```bash
# Multi-AI setup for reliability and cost optimization
OPENROUTER_API_KEY="sk-or-your-key"     # Recommended: Access to 100+ models
DEEPSEEK_API_KEY="sk-your-key"          # Cost-effective: $0.14/1M tokens  
GROQ_API_KEY="gsk-your-key"             # Speed: 500+ tokens/sec

# Performance tuning
MAX_WORKERS=50
MAX_CONCURRENT_PER_WORKER=10
ENABLE_PATTERN_LEARNING=true
ENABLE_AUTONOMOUS_TOOLS=true
```

### **Start the Platform**
```bash
# Web interface with real-time chat
python web_ui_server.py
# Access: http://localhost:8080

# Or direct Python usage
python -c "
import asyncio
from src.agents.intelligent_analyzer import IntelligentAnalyzer
from ai_core.core.hybrid_ai_service import create_production_ai_service

async def demo():
    ai_service = create_production_ai_service()
    analyzer = IntelligentAnalyzer(llm_service=ai_service)
    await analyzer.initialize()
    
    analysis = await analyzer.analyze_website('https://example.com')
    print(f'Type: {analysis.website_type.value}')
    print(f'Complexity: {analysis.estimated_complexity}')
    print(f'Confidence: {analysis.analysis_confidence:.2f}')

asyncio.run(demo())
"
```

## 🔧 Advanced Features

### **Intelligent Website Analysis**
```python
# Comprehensive analysis with AI-powered insights
analysis = await analyzer.analyze_website(url)
# Returns: website type, complexity, frameworks, anti-bot measures,
# data quality indicators, accessibility scores, security features
```

### **Autonomous Tool Selection**
```python
# AI selects optimal tools based on analysis
tool_selection = await tool_selector.select_optimal_tools(intent, context)
# Returns: primary tool, configuration, alternatives, strategy, reasoning
```

### **Real-Time Extraction**
```python
# Background processing with live updates
job_plan = job_decomposer.decompose_request(intent)
jobs = await job_executor.start_background_jobs(job_plan, session_id)
# Real-time progress via WebSocket
```

### **Pattern Learning**
```python
# Stores successful patterns for reuse
pattern_id = await pattern_memory.store_successful_pattern(
    request, intent, results, success_score=0.95
)
# Automatically applies learned optimizations
```

## 🏢 Platform-Specific Extractors

### **Social Networks**
- **LinkedIn**: Professional profiles, company data, job listings
- **Facebook**: Public pages, posts, business information
- **Twitter**: Tweets, profiles, engagement metrics

### **E-commerce**
- **Amazon**: Products, prices, reviews, seller information
- **eBay**: Listings, auction data, seller metrics
- **E-commerce Sites**: Generic product extraction

### **Business Directories**
- **Yelp**: Business listings, reviews, contact information
- **Google Business**: Local business data and reviews
- **Yellow Pages**: Directory listings and contact details

## 🐳 Production Deployment

### **Docker Compose (Multi-Service)**
```bash
# Production deployment with monitoring
docker-compose -f compose/docker-compose.yml up -d

# Services included:
# - crawler-agent: Main application
# - model-manager: AI model management  
# - web-ui: User interface
# - workers: Background processing
# - postgres: Data persistence
# - redis: Caching and sessions
# - prometheus: Metrics collection
# - grafana: Monitoring dashboards
```

### **Scaling Configuration**
```bash
# High-throughput setup
MAX_WORKERS=100
MAX_CONCURRENT_PER_WORKER=20
RATE_LIMIT_PER_MINUTE=5000
BROWSER_POOL_URLS=http://worker1:3001,http://worker2:3001,http://worker3:3001

# Multi-region AI providers
AI_PROVIDER=openrouter
FALLBACK_AI_PROVIDER=deepseek
TERTIARY_AI_PROVIDER=groq
CONFIDENCE_THRESHOLD=0.8
```

## 📊 Performance & Capabilities

### **Extraction Performance**
- **Concurrent Extractions**: 50+ parallel operations
- **Success Rate**: 85%+ with multi-strategy fallbacks
- **Speed**: 500+ pages/hour with optimization
- **Reliability**: Automatic retries and provider failover

### **AI Intelligence**
- **Provider Switching**: Sub-second failover on errors
- **Cost Optimization**: Automatic routing to cheapest viable provider
- **Learning**: Improves accuracy over time from successful patterns
- **Context Awareness**: Adapts strategies based on website characteristics

### **Real-Time Capabilities**
- **Live Updates**: WebSocket-based progress tracking
- **Streaming Data**: Continuous extraction feeds
- **Background Jobs**: Non-blocking parallel processing
- **Monitoring**: Real-time performance metrics and alerts

## 🔍 Supported Website Types

- **Directory Listings**: Business directories, contact databases
- **E-commerce**: Product catalogs, pricing, inventory
- **Social Media**: Profiles, posts, engagement metrics
- **News Articles**: Content, metadata, publishing information
- **Corporate Sites**: Company information, team data
- **Form-Heavy Sites**: Complex interactive applications
- **SPAs**: Dynamic single-page applications
- **Data Tables**: Structured tabular information

## 🛠️ Development & Extension

### **Custom Strategy Development**
```python
# Extend with custom extraction strategies
from src.core.base_strategy import BaseStrategy

class CustomStrategy(BaseStrategy):
    async def extract(self, url, config):
        # Your custom extraction logic
        pass
```

### **AI Provider Integration**
```python
# Add new AI providers
from ai_core.core.hybrid_ai_service import AIConfig, AIProvider

custom_config = AIConfig(
    provider=AIProvider.CUSTOM,
    model="your-model",
    api_key="your-key",
    priority=1
)
```

## 📚 Documentation Structure

- **[📦 Installation](docs/quick-start/01-installation.md)** - Complete setup guide
- **[🤖 AI Providers](docs/quick-start/03-ai-providers.md)** - Multi-provider configuration
- **[🔄 Workflows](docs/quick-start/04-basic-workflows.md)** - Automation examples
- **[🏗️ Architecture](docs/architecture/)** - System design deep-dive
- **[📚 API Reference](docs/api-reference/)** - Complete technical reference
- **[🐳 Deployment](docs/deployment/)** - Production setup guides

## 🔮 Advanced Features in Development

### **Identity-Based Crawling** *(Q1 2025)*
- **Persistent Login Profiles**: Session management across restarts
- **Headful Browser with VNC**: Visual interaction and debugging
- **Visual Schema Generation**: Point-and-click extraction rule creation
- **API Discovery Engine**: Automatic backend endpoint detection

## 🤝 Contributing

This project uses advanced patterns including:
- Service-oriented architecture with dependency injection
- Real-time event-driven communication
- Machine learning pattern recognition
- Multi-provider resilience strategies

See [Contributing Guide](docs/contributing/) for development setup and architectural guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🏆 What Makes This Different

### **Intelligence Over Configuration**
- **Autonomous Operation**: AI selects tools, configures parameters, and optimizes performance
- **Learning System**: Improves over time from successful extractions
- **Context Awareness**: Adapts strategies based on website characteristics

### **Enterprise-Grade Reliability**
- **Multi-Provider Failover**: Never fails due to single AI provider issues
- **Cost Optimization**: Intelligent routing minimizes API costs
- **Scalable Architecture**: Production-ready multi-service deployment

### **Real-Time Capabilities**
- **Live Progress Tracking**: Enhanced user communication with insights
- **Streaming Data**: Continuous extraction and monitoring feeds
- **Background Processing**: Non-blocking parallel execution

---

**Ready for intelligent extraction?** This isn't just another web scraper - it's an AI-powered extraction platform built for the complexities of modern web data collection.
