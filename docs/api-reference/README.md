# 📚 API Reference

> **Complete technical documentation for the Intelligent Crawl4AI Agent**

This reference provides detailed documentation for all classes, methods, and configuration options in the Intelligent Crawl4AI Agent. Use this guide when building custom applications or extending the system.

---

## 🏗️ Core Architecture

### **Service Layer**
- **[HybridAI Service](#hybridai-service)** - Multi-provider AI orchestration
- **[Vector Service](#vector-service)** - Semantic search and similarity
- **[Identity Service](#identity-service)** - Authentication and session management *(Q1 2025)*
- **[Schema Service](#schema-service)** - Extraction schema management *(Q1 2025)*

### **Agent Layer**  
- **[IntelligentAnalyzer](#intelligentanalyzer)** - High-level extraction interface
- **[ExtractionOrchestrator](#extractionorchestrator)** - Workflow automation
- **[StrategySelector](#strategyselector)** - Strategy selection logic

### **Strategy Layer**
- **[BaseExtractionStrategy](#baseextractionstrategy)** - Strategy base class
- **[AIEnhancedStrategy](#aienhancedstrategy)** - AI-powered extraction
- **[AdaptiveCrawlerStrategy](#adaptivecrawlerstrategy)** - Learning-based extraction
- **[MultiStrategy](#multistrategy)** - Strategy coordination

---

## 🤖 HybridAI Service

### **Class: HybridAIService**

Multi-provider AI service with automatic failover and cost optimization.

```python
from ai_core.core.hybrid_ai_service import HybridAIService, create_production_ai_service

# Initialize with production configuration
ai_service = create_production_ai_service()

# Or create with custom configuration
configs = [
    AIConfig(provider=AIProvider.DEEPSEEK, priority=1),
    AIConfig(provider=AIProvider.GROQ, priority=2),
    AIConfig(provider=AIProvider.OPENAI, priority=3)
]
ai_service = HybridAIService(configs=configs)
```

#### **Methods**

##### **generate_structured()**
Generate structured JSON output with schema validation.

```python
async def generate_structured(
    self, 
    prompt: str, 
    schema: Dict[str, Any],
    model: str = None, 
    max_retries: int = 3
) -> Dict[str, Any]:
```

**Parameters:**
- `prompt` (str): Input prompt for generation
- `schema` (Dict): JSON schema for output validation
- `model` (str, optional): Override default model selection
- `max_retries` (int): Maximum retry attempts (default: 3)

**Returns:**
- `Dict[str, Any]`: Structured response matching the schema

**Example:**
```python
schema = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "employee_count": {"type": "number"},
        "founded_year": {"type": "number"}
    },
    "required": ["company_name"]
}

result = await ai_service.generate_structured(
    prompt="Extract company information from this text: 'OpenAI was founded in 2015 and has 700+ employees'",
    schema=schema
)
# Returns: {"company_name": "OpenAI", "employee_count": 700, "founded_year": 2015}
```

---

## 🔍 IntelligentAnalyzer

### **Class: IntelligentAnalyzer**

High-level interface for intelligent website analysis and data extraction.

```python
from src.agents.intelligent_analyzer import IntelligentAnalyzer

analyzer = IntelligentAnalyzer(
    llm_service=ai_service,
    vector_service=vector_service  # Optional
)
```

#### **Methods**

##### **analyze_website()**
Perform comprehensive website analysis and data extraction.

```python
async def analyze_website(
    self,
    url: str,
    purpose: str,
    strategy: str = None,
    profile: Profile = None,  # Q1 2025
    context: Dict[str, Any] = None
) -> StrategyResult:
```

**Parameters:**
- `url` (str): Target website URL
- `purpose` (str): Natural language description of extraction goal
- `strategy` (str, optional): Force specific strategy selection
- `profile` (Profile, optional): Authentication profile for login-protected content
- `context` (Dict, optional): Additional context for extraction

**Returns:**
- `StrategyResult`: Comprehensive extraction results

**Example:**
```python
result = await analyzer.analyze_website(
    url="https://news-site.com/tech",
    purpose="Extract article headlines, publication dates, and author names",
    context={
        "industry": "technology",
        "date_range": "last_7_days",
        "minimum_word_count": 100
    }
)

if result.success:
    articles = result.extracted_data.get('articles', [])
    print(f"Extracted {len(articles)} articles")
    print(f"Confidence: {result.confidence_score:.2f}")
else:
    print(f"Extraction failed: {result.error}")
```

---

**Complete API Documentation** 📚

This is a condensed reference. For complete method signatures, parameters, and examples, see the full documentation files in this directory:

- **[Core Classes](core-classes.md)** - Complete class documentation
- **[Service APIs](service-apis.md)** - Detailed service interfaces
- **[Configuration Objects](configuration-objects.md)** - All configuration options
- **[Data Models](data-models.md)** - Response and data structures
- **[Error Handling](error-handling.md)** - Exception handling guide

👉 **[Examples →](../examples/)**

*See these APIs in action with real-world use cases*
