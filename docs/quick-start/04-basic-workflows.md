# 🔄 04. Basic Workflows

> **Automate complex, multi-step extractions with natural language**

Now that you have AI providers configured, let's create intelligent workflows that can handle complex extraction tasks automatically. You'll see how natural language instructions become sophisticated automation pipelines.

---

## 🎯 What Are Workflows?

### **Simple Extraction** (What you've done so far)
```
Single URL → Extract data → Get results
```

### **Intelligent Workflows** (What you'll learn now)
```
Natural language instruction → AI creates plan → Executes multiple steps → Coordinates results → Provides insights
```

**Example**: *\"Monitor competitor pricing daily and alert me to changes > 10%\"* becomes an automated system that crawls sites, compares prices, tracks changes, and sends notifications.

---

## 🚀 Your First Workflow

### **Simple Multi-Site Extraction**
```python
# basic_workflow.py
import asyncio
from ai_core.core.hybrid_ai_service import create_production_ai_service
from src.agents.orchestrator import ExtractionOrchestrator

async def create_first_workflow():
    print(\"🤖 Creating your first intelligent workflow...\")
    
    # Initialize orchestrator
    ai_service = create_production_ai_service()
    orchestrator = ExtractionOrchestrator(llm_service=ai_service)
    
    # Create workflow from natural language
    workflow = await orchestrator.create_workflow(
        \"Extract product information from 3 e-commerce sites: \
        books.toscrape.com, quotes.toscrape.com, and scrapethissite.com. \
        Compare prices and availability, then create a summary report.\"
    )
    
    print(f\"📋 Created workflow with {len(workflow.steps)} steps\")
    print(f\"🎯 Confidence: {workflow.confidence:.2f}\")
    
    # Execute the workflow
    print(\"\\n🚀 Executing workflow...\")
    results = await orchestrator.execute_workflow(workflow)
    
    if results.success:
        print(\"\\n✅ Workflow completed successfully!\")
        print(f\"⏱️ Total time: {results.execution_time:.2f} seconds\")
        print(f\"📊 Sites processed: {len(results.site_results)}\")
        
        # Display summary
        for site, data in results.site_results.items():
            print(f\"\\n🌐 {site}:\")
            print(f\"   Products found: {len(data.get('products', []))}\")
            print(f\"   Confidence: {data.get('confidence', 0):.2f}\")
        
        # Show comparison insights
        if results.insights:
            print(\"\\n💡 Insights:\")
            for insight in results.insights:
                print(f\"   • {insight}\")
                
    else:
        print(f\"❌ Workflow failed: {results.error}\")

# Run the workflow
if __name__ == \"__main__\":
    asyncio.run(create_first_workflow())
```

Run it:
```bash
python basic_workflow.py
```

### **Expected Output**
```
🤖 Creating your first intelligent workflow...
📋 Created workflow with 4 steps
🎯 Confidence: 0.87

🚀 Executing workflow...

✅ Workflow completed successfully!
⏱️ Total time: 12.34 seconds
📊 Sites processed: 3

🌐 books.toscrape.com:
   Products found: 20
   Confidence: 0.91

🌐 quotes.toscrape.com:
   Products found: 10
   Confidence: 0.89

🌐 scrapethissite.com:
   Products found: 15
   Confidence: 0.85

💡 Insights:
   • Books.toscrape.com has the most consistent pricing structure
   • Quote data quality is highest on quotes.toscrape.com
   • Scrapethissite.com shows varied content types requiring different strategies
```

---

## 🧠 How Workflows Work

### **1. Natural Language Planning**
The AI analyzes your instruction and creates a step-by-step plan:

```python
# What the AI creates from your instruction
workflow_plan = {
    \"description\": \"Multi-site e-commerce data extraction and comparison\",
    \"confidence\": 0.87,
    \"steps\": [
        {
            \"step_id\": 1,
            \"tool\": \"crawl_web\",
            \"description\": \"Extract product data from books.toscrape.com\",
            \"parameters\": {\"url\": \"books.toscrape.com\", \"purpose\": \"product_extraction\"},
            \"depends_on\": []
        },
        {
            \"step_id\": 2,
            \"tool\": \"crawl_web\", 
            \"description\": \"Extract data from quotes.toscrape.com\",
            \"parameters\": {\"url\": \"quotes.toscrape.com\", \"purpose\": \"content_extraction\"},
            \"depends_on\": []
        },
        {
            \"step_id\": 3,
            \"tool\": \"analyze_content\",
            \"description\": \"Compare and analyze extracted data\",
            \"parameters\": {\"analysis_type\": \"comparative\"},
            \"depends_on\": [1, 2]
        },
        {
            \"step_id\": 4,
            \"tool\": \"generate_report\",
            \"description\": \"Create summary report with insights\",
            \"parameters\": {\"format\": \"summary\"},
            \"depends_on\": [3]
        }
    ]
}
```

### **2. Intelligent Execution**
- Runs steps in optimal order (parallel where possible)
- Handles errors and retries automatically
- Adapts strategies based on results
- Provides real-time progress updates

### **3. Result Coordination**
- Combines data from multiple sources
- Generates insights and comparisons
- Creates structured output
- Provides confidence scoring

---

## 🎯 Practical Workflow Examples

### **1. Competitor Price Monitoring**
```python
# Monitor competitor pricing
workflow = await orchestrator.create_workflow(
    \"Check pricing for smartphones on Amazon, Best Buy, and Newegg. \
    Focus on iPhone 15 and Samsung Galaxy S24. \
    Alert if any price changes by more than $50 from last check.\"
)

# The AI automatically:
# - Identifies target products
# - Extracts current prices  
# - Compares with historical data
# - Generates alerts for significant changes
```

### **2. Lead Generation Pipeline**
```python
# Generate leads from directories
workflow = await orchestrator.create_workflow(
    \"Find technology companies in San Francisco from YellowPages, \
    Yelp Business, and LinkedIn company directory. \
    Extract company names, contact info, and employee counts. \
    Filter for companies with 50-200 employees.\"
)

# The AI automatically:
# - Searches multiple directories
# - Extracts contact information
# - Applies filtering criteria
# - Deduplicates results
# - Formats for CRM import
```

### **3. Market Research Automation**
```python
# Research industry trends
workflow = await orchestrator.create_workflow(
    \"Research the electric vehicle market by analyzing news from \
    TechCrunch, Reuters, and Bloomberg. Extract key announcements, \
    funding rounds, and market forecasts from the last 30 days.\"
)

# The AI automatically:
# - Searches news sources
# - Filters by date and relevance
# - Categorizes information types
# - Summarizes trends
# - Identifies key players
```

### **4. Content Aggregation**
```python
# Aggregate industry content
workflow = await orchestrator.create_workflow(
    \"Collect technical blog posts about machine learning from \
    Towards Data Science, AI Research blogs, and company engineering blogs. \
    Summarize key insights and identify trending topics.\"
)

# The AI automatically:
# - Identifies relevant sources
# - Extracts article content
# - Generates summaries
# - Identifies trending topics
# - Creates digest report
```

---

## 🔧 Advanced Workflow Features

### **1. Conditional Logic**
```python
# Workflows with decision points
workflow = await orchestrator.create_workflow(
    \"Check product availability on supplier websites. \
    If any items are out of stock, search for alternative suppliers \
    and compare their pricing. Send alert if prices differ by >20%.\"
)

# The AI creates conditional steps:
# Step 1: Check stock status
# Step 2: IF out of stock → search alternatives
# Step 3: IF alternatives found → compare prices  
# Step 4: IF price difference > 20% → send alert
```

### **2. Data Transformation**
```python
# Automatic data formatting
workflow = await orchestrator.create_workflow(
    \"Extract employee data from company LinkedIn pages \
    and format it for our CRM system. Include name, title, \
    contact info, and export as CSV with proper headers.\"
)

# The AI automatically:
# - Maps fields to CRM schema
# - Handles data validation
# - Applies formatting rules
# - Exports in requested format
```

### **3. Error Handling and Retries**
```python
# Robust error handling built-in
workflow = await orchestrator.create_workflow(
    \"Monitor 50 e-commerce sites for product updates. \
    If any site fails, retry with different strategy. \
    Continue with successful sites and report failures.\"
)

# Automatic features:
# - Strategy fallback on failures
# - Partial success handling
# - Detailed error reporting
# - Retry with exponential backoff
```

---

## 📊 Workflow Monitoring

### **Real-Time Progress**
```python
# Monitor workflow execution
async def monitor_workflow(workflow):
    results = await orchestrator.execute_workflow(
        workflow,
        progress_callback=lambda step, status: print(f\"Step {step}: {status}\")
    )
    
    # Real-time output:
    # Step 1: Starting extraction from site 1
    # Step 1: Completed with confidence 0.89
    # Step 2: Starting extraction from site 2
    # Step 2: Completed with confidence 0.91
    # Step 3: Starting data analysis
    # Step 3: Completed - found 3 key insights
```

### **Performance Analytics**
```python
# Get detailed workflow statistics
stats = orchestrator.get_workflow_stats()

print(f\"Workflows executed: {stats['total_workflows']}\")
print(f\"Success rate: {stats['success_rate']:.1%}\")
print(f\"Average execution time: {stats['avg_execution_time']:.2f}s\")
print(f\"Most used strategies: {stats['top_strategies']}\")

# Per-step performance
for step_type, metrics in stats['step_performance'].items():
    print(f\"{step_type}: {metrics['avg_time']:.2f}s avg, {metrics['success_rate']:.1%} success\")
```

---

## 🔄 Scheduled Workflows

### **Automated Scheduling**
```python
# Set up recurring workflows
from src.automation.scheduler import WorkflowScheduler

scheduler = WorkflowScheduler()

# Daily competitor monitoring
await scheduler.schedule_workflow(
    name=\"daily_competitor_check\",
    instruction=\"Check competitor pricing and product updates daily at 9 AM\",
    schedule=\"0 9 * * *\",  # Cron format
    notifications={
        \"email\": \"alerts@company.com\",
        \"slack\": \"#market-intelligence\"
    }
)

# Weekly market research
await scheduler.schedule_workflow(
    name=\"weekly_market_research\",
    instruction=\"Compile weekly industry news and trend analysis every Friday\",
    schedule=\"0 17 * * 5\",  # 5 PM every Friday
    output_format=\"pdf_report\"
)
```

### **Event-Driven Workflows**
```python
# Trigger workflows based on conditions
await scheduler.create_trigger(
    name=\"price_change_response\",
    condition=\"competitor_price_change > 10%\",
    workflow=\"Investigate price change reasons and update our pricing strategy\",
    immediate=True
)
```

---

## 🛠️ Troubleshooting Workflows

### **Common Issues**

#### **\"Workflow creation failed\"**
```python
# Check workflow complexity
try:
    workflow = await orchestrator.create_workflow(instruction)
    print(f\"Workflow complexity: {len(workflow.steps)} steps\")
    print(f\"Confidence: {workflow.confidence}\")
except Exception as e:
    print(f\"Creation failed: {e}\")
    
    # Try simpler instruction
    simple_workflow = await orchestrator.create_workflow(
        \"Extract data from one website and save as CSV\"
    )
```

#### **\"Low workflow confidence\"**
```python
# Add more specific instructions
instead_of = \"Get data from websites\"
use_this = \"Extract product names, prices, and descriptions from \
            e-commerce websites and save as structured JSON\"

# Check AI provider status
status = ai_service.get_provider_status()
healthy_providers = [p for p, s in status.items() if s['status'] == 'healthy']
print(f\"Available providers: {healthy_providers}\")
```

#### **\"Workflow execution timeout\"**
```python
# Adjust timeout settings
workflow_config = WorkflowConfig(
    max_execution_time=600,    # 10 minutes
    step_timeout=120,          # 2 minutes per step
    retry_attempts=3,
    parallel_execution=True    # Speed up with concurrency
)

results = await orchestrator.execute_workflow(workflow, config=workflow_config)
```

---

## ✅ Workflow Mastery Checklist

After completing this guide:

- ✅ **Created your first workflow** from natural language
- ✅ **Executed multi-step extraction** successfully  
- ✅ **Understood workflow planning** and step coordination
- ✅ **Seen automatic error handling** and retries in action
- ✅ **Explored practical examples** for real use cases
- ✅ **Set up monitoring** and performance tracking

---

## 🚀 What's Next?

### **You Can Now**
- Automate complex extraction tasks with simple instructions
- Handle multiple websites and data sources automatically
- Create intelligent comparisons and analysis
- Monitor and schedule recurring extractions

### **Next Steps**
1. **[🔐 Identity Setup](05-identity-setup.md)** - Access login-protected content *(Q1 2025)*
2. **[📚 Explore Examples](../examples/)** - See real-world workflow implementations

### **Advanced Topics**
- **[Workflow Design](../workflows/workflow-design.md)** - Advanced workflow patterns
- **[Custom Strategies](../contributing/adding-strategies.md)** - Build custom extraction logic
- **[Production Deployment](../deployment/)** - Scale workflows to production

---

**Outstanding!** 🎉

You now understand how to create intelligent workflows that automate complex extraction tasks. The AI handles the planning, execution, and coordination automatically.

👉 **[Next: Identity Setup →](05-identity-setup.md)**

*Learn to extract data from login-protected sites like LinkedIn and Facebook*
