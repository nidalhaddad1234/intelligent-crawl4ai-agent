# 🎯 02. First Extraction

> **Extract data from your first website in 3 minutes**

Now that you have the agent installed, let's perform your first intelligent extraction. You'll see how the multi-AI system automatically understands website content and extracts exactly what you need.

---

## 🚀 Quick First Extraction

### **Before We Start**
Make sure you have at least one AI provider configured. If not, quickly add one:

```bash
# Add to your .env file (choose one)
export OPENROUTER_API_KEY=\"sk-or-your-key-here\"  # Recommended
export DEEPSEEK_API_KEY=\"sk-your-key-here\"       # Cheapest
export OPENAI_API_KEY=\"sk-your-key-here\"         # Premium
```

### **Your First Extraction**
Create and run this simple script:

```python
# first_extraction.py
import asyncio
from ai_core.core.hybrid_ai_service import create_production_ai_service
from src.agents.intelligent_analyzer import IntelligentAnalyzer

async def first_extraction():
    print(\"🤖 Initializing AI service...\")
    
    # Create AI service with multiple providers
    ai_service = create_production_ai_service()
    
    # Initialize the intelligent analyzer
    analyzer = IntelligentAnalyzer(llm_service=ai_service)
    
    print(\"🎯 Starting extraction...\")
    
    # Extract data from a real website
    result = await analyzer.analyze_website(
        url=\"https://quotes.toscrape.com/\",
        purpose=\"Extract quotes, authors, and tags\"
    )
    
    # Display results
    if result.success:
        print(\"\\n✅ Extraction successful!\")
        print(f\"📊 Confidence: {result.confidence_score:.2f}\")
        print(f\"⚡ Time taken: {result.execution_time:.2f} seconds\")
        print(f\"🧠 Strategy used: {result.strategy_used}\")
        
        print(\"\\n📋 Extracted Data:\")
        print(\"=\" * 50)
        
        # Pretty print the extracted data
        import json
        print(json.dumps(result.extracted_data, indent=2))
        
        print(\"\\n🎉 Your first extraction is complete!\")
    else:
        print(f\"❌ Extraction failed: {result.error}\")
        print(\"💡 Try adding an AI provider API key to your .env file\")

# Run the extraction
if __name__ == \"__main__\":
    asyncio.run(first_extraction())
```

Run it:
```bash
python first_extraction.py
```

### **Expected Output**
```
🤖 Initializing AI service...
🎯 Starting extraction...

✅ Extraction successful!
📊 Confidence: 0.89
⚡ Time taken: 3.24 seconds
🧠 Strategy used: AIEnhancedStrategy

📋 Extracted Data:
==================================================
{
  \"quotes\": [
    {
      \"text\": \"The world as we have created it is a process of our thinking...\",
      \"author\": \"Albert Einstein\",
      \"tags\": [\"change\", \"deep-thoughts\", \"thinking\", \"world\"]
    },
    {
      \"text\": \"It is our choices, Harry, that show what we truly are...\",
      \"author\": \"J.K. Rowling\",
      \"tags\": [\"abilities\", \"choices\"]
    }
    // ... more quotes
  ],
  \"total_quotes\": 10,
  \"page_info\": {
    \"title\": \"Quotes to Scrape\",
    \"url\": \"https://quotes.toscrape.com/\"
  }
}

🎉 Your first extraction is complete!
```

---

## 🧠 What Just Happened?

### **1. Intelligent Website Analysis**
The AI automatically:
- Analyzed the website structure
- Identified quote content patterns  
- Determined the best extraction strategy
- Generated appropriate data schema

### **2. Multi-Provider AI System**
- Tried providers in priority order (cheapest first)
- Used DeepSeek or OpenRouter for cost efficiency
- Fell back to premium providers if needed
- Selected best model for the task

### **3. Adaptive Extraction**
- Started with AI-enhanced strategy
- Analyzed content semantically
- Generated CSS selectors automatically
- Validated extracted data quality

### **4. Structured Output**
- Returned clean, structured JSON
- Included metadata and confidence scores
- Provided performance metrics
- Organized data logically

---

## 🔄 Try Different Websites

### **E-commerce Example**
```python
# Extract product information
result = await analyzer.analyze_website(
    url=\"https://books.toscrape.com/\",
    purpose=\"Extract book titles, prices, ratings, and availability\"
)
```

### **News Site Example**
```python
# Extract articles
result = await analyzer.analyze_website(
    url=\"https://example-news-site.com/tech\",
    purpose=\"Extract article headlines, dates, authors, and summaries\"
)
```

### **Directory/Listing Example**
```python
# Extract contact information
result = await analyzer.analyze_website(
    url=\"https://example-directory.com/companies\",
    purpose=\"Extract company names, addresses, phone numbers, and websites\"
)
```

---

## 🎯 Understanding Extraction Strategies

### **AI-Enhanced Strategy** (Most Common)
- Uses AI to understand content semantically
- Generates CSS selectors automatically
- Adapts to website changes
- **Best for**: Complex, dynamic content

### **Adaptive Crawler Strategy**
- Learns from extraction patterns
- Optimizes performance over time
- Handles multiple similar sites
- **Best for**: Repeated extractions from similar sites

### **Multi-Strategy Coordination**
- Combines multiple approaches
- Uses consensus for reliability
- Provides backup options
- **Best for**: Critical, high-accuracy needs

---

## 🔧 Customizing Your Extractions

### **Specify Extraction Context**
```python
result = await analyzer.analyze_website(
    url=\"https://ecommerce-site.com/products\",
    purpose=\"Extract pricing data for competitive analysis\",
    context={
        \"industry\": \"electronics\",
        \"focus\": \"price_comparison\",
        \"format\": \"spreadsheet_ready\"
    }
)
```

### **Control Strategy Selection**
```python
from src.strategies.hybrid.ai_enhanced import AIEnhancedStrategy

# Use specific strategy
custom_strategy = AIEnhancedStrategy(
    llm_service=ai_service,
    config=AIEnhancementConfig(
        confidence_threshold=0.8,
        enable_data_validation=True
    )
)

result = await custom_strategy.extract(
    url=\"https://target-site.com\",
    html_content=html,
    purpose=\"high_accuracy_extraction\"
)
```

### **Monitor Performance**
```python
# Get detailed performance info
performance = analyzer.get_performance_stats()

print(f\"Success rate: {performance['success_rate']:.1%}\")
print(f\"Average confidence: {performance['avg_confidence']:.2f}\")
print(f\"Strategy usage: {performance['strategy_usage']}\")
```

---

## 🛠️ Troubleshooting First Extraction

### **Common Issues**

#### **\"All AI providers failed\"**
```python
# Check provider status
status = ai_service.get_provider_status()
for provider, info in status.items():
    print(f\"{provider}: {info['status']} - {info.get('error', 'OK')}\")

# Solution: Add valid API key to .env
```

#### **\"Low confidence score (< 0.5)\"**
```python
# Use more specific purpose
result = await analyzer.analyze_website(
    url=\"https://complex-site.com\",
    purpose=\"Extract product names and prices from the main product listing table\",  # More specific
    context={\"format\": \"ecommerce_products\"}  # Add context
)
```

#### **\"Empty or partial results\"**
```python
# Check website accessibility
import requests
response = requests.get(\"https://target-site.com\")
print(f\"Status: {response.status_code}\")
print(f\"Content length: {len(response.text)}\")

# Try different strategy
from src.strategies.hybrid.multi_strategy import MultiStrategy
strategy = MultiStrategy(strategies=all_strategies, llm_service=ai_service)
```

### **Debug Mode**
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Run extraction with full debug output
result = await analyzer.analyze_website(
    url=\"problem-site.com\",
    purpose=\"debug extraction\",
    debug=True
)
```

---

## ✅ Success Checklist

After your first extraction, you should have:

- ✅ **Successful extraction** with confidence > 0.7
- ✅ **Structured JSON output** with relevant data
- ✅ **Performance metrics** showing execution time
- ✅ **Strategy information** showing which approach worked
- ✅ **Understanding** of how the AI analyzed the website

---

## 🚀 What's Next?

### **Immediate Next Steps**
1. **[🤖 Setup More AI Providers](03-ai-providers.md)** - Add redundancy and cost optimization
2. **[🔄 Basic Workflows](04-basic-workflows.md)** - Automate multi-step extractions

### **Explore Further**
- **[Extraction Strategies](../strategies/)** - Learn about different approaches
- **[Examples](../examples/)** - See real-world use cases
- **[API Reference](../api-reference/)** - Detailed technical documentation

### **Ready for Production?**
- **[Deployment Guide](../deployment/)** - Deploy to cloud or on-premises
- **[Monitoring](../deployment/monitoring/)** - Track performance and costs

---

**Congratulations!** 🎉

You've successfully performed your first intelligent extraction. The AI understood the website, selected the best strategy, and extracted structured data automatically.

👉 **[Next: Setup AI Providers →](03-ai-providers.md)**

*Add more AI providers for better reliability and cost optimization*
