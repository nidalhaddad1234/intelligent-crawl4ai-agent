# 🤖 03. AI Providers Setup

> **Configure multiple AI providers for reliability, speed, and cost optimization**

The Intelligent Crawl4AI Agent uses a multi-provider AI system that automatically routes requests to the best available service. This guide shows you how to set up and optimize your AI providers.

---

## 🎯 Why Multiple Providers?

### **Reliability** 
- Never fail due to a single provider outage
- Automatic fallback when one provider is slow
- Continue working even if your primary provider hits limits

### **Cost Optimization**
- Start with cheapest providers (DeepSeek: $0.14/1M tokens)
- Fall back to premium only when needed
- Optimize spending based on use case

### **Performance**
- Use fastest providers (Groq: 500+ tokens/sec) for speed
- Route complex tasks to best models
- Balance quality vs cost automatically

---

## 🚀 Quick Setup (Choose One)

### **💰 Budget Option: DeepSeek Only**
```bash
# Add to .env file
export DEEPSEEK_API_KEY=\"sk-your-deepseek-key\"
```
**Cost**: ~$0.14 per 1M tokens • **Quality**: Very good • **Speed**: Good

### **⚡ Speed Option: Groq + DeepSeek**
```bash
# Add to .env file  
export GROQ_API_KEY=\"gsk-your-groq-key\"
export DEEPSEEK_API_KEY=\"sk-your-deepseek-key\"
```
**Speed**: Fastest responses • **Reliability**: Good • **Cost**: Low

### **🏆 Premium Option: All Providers**
```bash
# Add to .env file
export OPENROUTER_API_KEY=\"sk-or-your-openrouter-key\"
export DEEPSEEK_API_KEY=\"sk-your-deepseek-key\"
export GROQ_API_KEY=\"gsk-your-groq-key\"
export OPENAI_API_KEY=\"sk-your-openai-key\"
export ANTHROPIC_API_KEY=\"sk-ant-your-anthropic-key\"
```
**Reliability**: Maximum • **Quality**: Best • **Speed**: Optimized • **Cost**: Controlled

---

## 🔧 Detailed Provider Setup

### **1. OpenRouter (Recommended First)**
**Why**: Access to 100+ models through one API • Good pricing • Reliable

```bash
# Get API key from https://openrouter.ai/
export OPENROUTER_API_KEY=\"sk-or-your-key-here\"
export OPENROUTER_MODEL=\"meta-llama/llama-3.1-8b-instruct:free\"  # Free model
```

**Configuration Options**:
```python
# In your Python code
from ai_core.core.hybrid_ai_service import AIConfig, AIProvider

openrouter_config = AIConfig(
    provider=AIProvider.OPENROUTER,
    model=\"meta-llama/llama-3.1-8b-instruct:free\",  # or premium models
    api_key=os.getenv('OPENROUTER_API_KEY'),
    priority=1,  # Highest priority
    max_tokens=4096,
    temperature=0.1
)
```

### **2. DeepSeek (Best Value)**
**Why**: Extremely cheap • High quality • Good for most extractions

```bash
# Get API key from https://platform.deepseek.com/
export DEEPSEEK_API_KEY=\"sk-your-deepseek-key\"
export DEEPSEEK_MODEL=\"deepseek-chat\"
```

**Cost Analysis**:
- **Input**: $0.14 per 1M tokens
- **Output**: $0.28 per 1M tokens  
- **Example**: 1000 extractions ≈ $2-5 total cost

### **3. Groq (Speed Champion)**
**Why**: Fastest inference • Good for real-time applications • Affordable

```bash
# Get API key from https://console.groq.com/
export GROQ_API_KEY=\"gsk-your-groq-key\"
export GROQ_MODEL=\"llama-3.1-8b-instant\"
```

**Performance**: 500+ tokens/second (10x faster than others)

### **4. OpenAI (Premium Quality)**
**Why**: Most reliable • Best for complex reasoning • Industry standard

```bash
# Get API key from https://platform.openai.com/
export OPENAI_API_KEY=\"sk-your-openai-key\"
export OPENAI_MODEL=\"gpt-4o-mini\"  # Cost-effective option
```

**Model Recommendations**:
- **gpt-4o-mini**: Best balance of cost/quality
- **gpt-4o**: Maximum quality for critical extractions

### **5. Anthropic (Advanced Reasoning)**
**Why**: Excellent reasoning • Safe outputs • Good for complex analysis

```bash
# Get API key from https://console.anthropic.com/
export ANTHROPIC_API_KEY=\"sk-ant-your-anthropic-key\"
export ANTHROPIC_MODEL=\"claude-3-haiku-20240307\"
```

### **6. Local Ollama (Self-Hosted)**
**Why**: No API costs • Full privacy • Works offline

```bash
# Install Ollama first: https://ollama.ai/
ollama pull llama3.2:3b

# Configure
export OLLAMA_URL=\"http://localhost:11434\"
export OLLAMA_MODEL=\"llama3.2:3b\"
```

---

## 🎯 Provider Priority Configuration

### **Cost-Optimized Setup**
```python
# Cheapest first, premium fallback
configs = [
    AIConfig(provider=AIProvider.DEEPSEEK, priority=1),      # $0.14/1M
    AIConfig(provider=AIProvider.GROQ, priority=2),         # Fast + cheap  
    AIConfig(provider=AIProvider.OPENROUTER, priority=3),   # Many models
    AIConfig(provider=AIProvider.OPENAI, priority=4),       # Premium fallback
]
```

### **Speed-Optimized Setup**
```python
# Fastest first
configs = [
    AIConfig(provider=AIProvider.GROQ, priority=1),         # 500+ tokens/sec
    AIConfig(provider=AIProvider.DEEPSEEK, priority=2),     # Good speed + cheap
    AIConfig(provider=AIProvider.OPENAI, priority=3),       # Reliable fallback
]
```

### **Quality-Optimized Setup**
```python
# Best models first  
configs = [
    AIConfig(provider=AIProvider.OPENAI, model=\"gpt-4o\", priority=1),
    AIConfig(provider=AIProvider.ANTHROPIC, model=\"claude-3-opus\", priority=2),
    AIConfig(provider=AIProvider.DEEPSEEK, priority=3),     # Cost fallback
]
```

---

## 🔍 Testing Your Setup

### **Test All Providers**
```python
# test_providers.py
import asyncio
from ai_core.core.hybrid_ai_service import create_production_ai_service

async def test_providers():
    ai_service = create_production_ai_service()
    
    print(\"🔍 Testing AI provider setup...\")
    
    # Health check all providers
    health = await ai_service.health_check()
    
    for provider_name, status in health.items():
        if status['status'] == 'healthy':
            print(f\"✅ {provider_name}: Working (response time: {status['response_time']:.2f}s)\")
        elif status['status'] == 'disabled':
            print(f\"➖ {provider_name}: Disabled (no API key)\")
        else:
            print(f\"❌ {provider_name}: Failed - {status['error']}\")
    
    # Test actual extraction
    try:
        result = await ai_service.generate_structured(
            prompt=\"Extract key info from this text: 'John Smith, CEO of TechCorp, email: john@techcorp.com'\",
            schema={
                \"type\": \"object\",
                \"properties\": {
                    \"name\": {\"type\": \"string\"},
                    \"title\": {\"type\": \"string\"},
                    \"company\": {\"type\": \"string\"},
                    \"email\": {\"type\": \"string\"}
                }
            }
        )
        
        if 'error' not in result:
            print(f\"\\n✅ Extraction test successful!\")
            print(f\"📊 Result: {result}\")
        else:
            print(f\"\\n❌ Extraction test failed: {result['error']}\")
            
    except Exception as e:
        print(f\"\\n❌ Test extraction failed: {e}\")

# Run the test
asyncio.run(test_providers())
```

Run the test:
```bash
python test_providers.py
```

### **Expected Output**
```
🔍 Testing AI provider setup...
✅ deepseek: Working (response time: 1.24s)
✅ groq: Working (response time: 0.31s)
➖ openai: Disabled (no API key)
➖ anthropic: Disabled (no API key)
✅ local_ollama: Working (response time: 2.15s)

✅ Extraction test successful!
📊 Result: {
  \"name\": \"John Smith\",
  \"title\": \"CEO\", 
  \"company\": \"TechCorp\",
  \"email\": \"john@techcorp.com\"
}
```

---

## 💰 Cost Optimization Strategies

### **Understanding Costs**
| Provider | Input (per 1M tokens) | Output (per 1M tokens) | Speed | Quality |
|----------|----------------------|-------------------------|--------|---------|
| DeepSeek | $0.14 | $0.28 | Good | Very Good |
| Groq | $0.27 | $0.27 | Fastest | Good |
| OpenRouter | $0.06-$30 | Varies | Good | Varies |
| OpenAI (GPT-4o-mini) | $0.15 | $0.60 | Good | Excellent |
| Anthropic (Haiku) | $0.25 | $1.25 | Good | Excellent |

### **Smart Usage Patterns**
```python
# Use cheap providers for bulk operations
bulk_config = AIConfig(
    provider=AIProvider.DEEPSEEK,
    temperature=0.1,  # More deterministic = fewer tokens
    max_tokens=1024   # Limit output length
)

# Use premium for critical extractions  
critical_config = AIConfig(
    provider=AIProvider.OPENAI,
    model=\"gpt-4o\",
    temperature=0.3,
    max_tokens=4096
)

# Dynamic provider selection
async def smart_extraction(complexity_level):
    if complexity_level == \"simple\":
        provider = \"deepseek\"
    elif complexity_level == \"fast\":
        provider = \"groq\"  
    else:
        provider = \"openai\"
    
    return await ai_service.generate_with_provider(prompt, provider)
```

### **Cost Monitoring**
```python
# Monitor usage and costs
stats = ai_service.get_provider_status()

for provider, info in stats.items():
    if info['total_requests'] > 0:
        print(f\"{provider}:\")
        print(f\"  Requests: {info['total_requests']}\")
        print(f\"  Success rate: {info['success_rate']:.1%}\")
        print(f\"  Avg response time: {info['avg_response_time']:.2f}s\")
```

---

## 🔧 Advanced Configuration

### **Custom Provider Priorities**
```python
# Dynamic priority adjustment
ai_service.switch_provider_priority(AIProvider.GROQ, priority=1)  # Make Groq primary
ai_service.disable_provider(AIProvider.OPENAI)  # Temporarily disable expensive provider
```

### **Provider-Specific Settings**
```python
# Fine-tune each provider
configs = [
    AIConfig(
        provider=AIProvider.DEEPSEEK,
        model=\"deepseek-chat\",
        temperature=0.1,      # Low temperature for consistency
        max_tokens=2048,      # Limit costs
        timeout=30,           # Fast timeout
        priority=1
    ),
    AIConfig(
        provider=AIProvider.OPENAI,
        model=\"gpt-4o-mini\",
        temperature=0.3,      # Balanced creativity
        max_tokens=4096,      # Higher quality output
        timeout=60,           # Allow more time
        priority=2
    )
]
```

### **Environment-Based Configuration**
```python
# Different setups for different environments
if os.getenv('ENVIRONMENT') == 'production':
    # Production: Reliability over cost
    primary_provider = AIProvider.OPENAI
elif os.getenv('ENVIRONMENT') == 'development':
    # Development: Cost over everything
    primary_provider = AIProvider.DEEPSEEK
else:
    # Local: Use free local models
    primary_provider = AIProvider.LOCAL_OLLAMA
```

---

## ✅ Provider Setup Checklist

After configuring your providers:

- ✅ **At least one provider** working and tested
- ✅ **Health check** showing green status
- ✅ **Test extraction** completed successfully 
- ✅ **Cost monitoring** understanding in place
- ✅ **Backup providers** configured for reliability

---

## 🚀 What's Next?

### **Now You Can**
- Extract data with automatic provider failover
- Optimize costs by using cheaper providers first
- Get faster responses from speed-optimized providers
- Scale without worrying about single provider limits

### **Next Steps**
1. **[🔄 Basic Workflows](04-basic-workflows.md)** - Automate multi-step extractions
2. **[🔐 Identity Setup](05-identity-setup.md)** - Access login-protected content

### **Advanced Topics**
- **[Cost Optimization](../ai-providers/cost-optimization.md)** - Detailed cost management
- **[Provider Comparison](../ai-providers/provider-setup.md)** - Full provider comparison
- **[Monitoring](../deployment/monitoring/)** - Production monitoring setup

---

**Excellent!** 🎉 

You now have a robust, multi-provider AI system that optimizes for cost, speed, and reliability automatically.

👉 **[Next: Basic Workflows →](04-basic-workflows.md)**

*Learn to automate complex, multi-step extractions*
