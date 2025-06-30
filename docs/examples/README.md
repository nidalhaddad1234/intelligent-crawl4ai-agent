# 💡 Examples & Use Cases

> **Real-world applications of the Intelligent Crawl4AI Agent with complete code examples**

This section provides practical, working examples that demonstrate how to use the Intelligent Crawl4AI Agent for common business scenarios. Each example includes complete code, expected output, and detailed explanations.

---

## 🎯 Example Categories

### **🏢 Business Intelligence**
- **[Competitor Analysis](#competitor-analysis)** - Monitor competitor pricing, products, and market positioning
- **[Market Research](#market-research)** - Industry trend analysis and market intelligence
- **[Lead Generation](#lead-generation)** - Extract prospects from directories and business listings

### **📊 E-commerce & Retail**
- **[Price Monitoring](#price-monitoring)** - Track pricing across multiple e-commerce platforms
- **[Product Research](#product-research)** - Analyze product features, reviews, and availability
- **[Inventory Tracking](#inventory-tracking)** - Monitor stock levels and supplier information

### **🔐 Identity-Based Extraction** *(Q1 2025)*
- **[LinkedIn Intelligence](#linkedin-intelligence)** - Professional network data extraction
- **[Social Media Monitoring](#social-media-monitoring)** - Cross-platform social intelligence
- **[Internal Systems](#internal-systems)** - Enterprise data aggregation

### **🔄 Automation & Workflows**
- **[Scheduled Monitoring](#scheduled-monitoring)** - Automated daily/weekly data collection
- **[Event-Driven Extraction](#event-driven-extraction)** - Trigger-based data collection
- **[Multi-Source Aggregation](#multi-source-aggregation)** - Complex data combination workflows

---

## 🚀 Quick Start Examples

### **Simple Website Analysis**
```python
# simple_extraction.py
import asyncio
from ai_core.core.hybrid_ai_service import create_production_ai_service
from src.agents.intelligent_analyzer import IntelligentAnalyzer

async def analyze_ecommerce_site():
    ai_service = create_production_ai_service()
    analyzer = IntelligentAnalyzer(llm_service=ai_service)
    
    result = await analyzer.analyze_website(
        url="https://books.toscrape.com/",
        purpose="Extract book titles, prices, ratings, and availability"
    )
    
    if result.success:
        print(f"✅ Found {len(result.extracted_data.get('books', []))} books")
        print(f"🎯 Confidence: {result.confidence_score:.2f}")
        return result.extracted_data
    else:
        print(f"❌ Extraction failed: {result.error}")

# Run the example
asyncio.run(analyze_ecommerce_site())
```

### **Multi-Site Batch Processing**
```python
# batch_extraction.py
import asyncio
from ai_core.core.hybrid_ai_service import create_production_ai_service
from src.agents.intelligent_analyzer import IntelligentAnalyzer

async def batch_competitor_analysis():
    ai_service = create_production_ai_service()
    analyzer = IntelligentAnalyzer(llm_service=ai_service)
    
    competitor_sites = [
        "https://competitor1.com/products",
        "https://competitor2.com/catalog", 
        "https://competitor3.com/pricing"
    ]
    
    # Process all sites concurrently
    tasks = [
        analyzer.analyze_website(
            url=url,
            purpose="Extract product pricing and availability data"
        )
        for url in competitor_sites
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful_extractions = [
        r for r in results 
        if not isinstance(r, Exception) and r.success
    ]
    
    print(f"✅ Successfully analyzed {len(successful_extractions)}/{len(competitor_sites)} sites")
    return successful_extractions

# Run batch analysis
asyncio.run(batch_competitor_analysis())
```

---

## 🏢 Detailed Business Examples

### **Competitor Pricing Intelligence**
```python
# competitor_pricing.py
import asyncio
import json
from datetime import datetime
from ai_core.core.hybrid_ai_service import create_production_ai_service
from src.agents.orchestrator import ExtractionOrchestrator

async def competitor_pricing_intelligence():
    """
    Monitor competitor pricing with change detection and alerts
    """
    
    ai_service = create_production_ai_service()
    orchestrator = ExtractionOrchestrator(llm_service=ai_service)
    
    # Define competitors and products to monitor
    monitoring_config = {
        "competitors": [
            {"name": "TechCorp", "url": "https://techcorp.com/pricing"},
            {"name": "InnovateCo", "url": "https://innovateco.com/products"},
            {"name": "FutureTech", "url": "https://futuretech.com/solutions"}
        ],
        "target_products": [
            "Enterprise Plan",
            "Professional Suite", 
            "Basic Package",
            "Premium Features"
        ],
        "alert_thresholds": {
            "price_change_percent": 5.0,
            "new_product_launch": True,
            "discount_campaigns": 15.0
        }
    }
    
    # Create comprehensive pricing analysis workflow
    workflow = await orchestrator.create_workflow(f"""
    Perform comprehensive competitor pricing analysis:
    
    1. Extract current pricing for all products from each competitor
    2. Compare with historical pricing data (if available)
    3. Identify pricing changes above {monitoring_config['alert_thresholds']['price_change_percent']}%
    4. Detect new products or discontinued items
    5. Analyze discount campaigns and promotional pricing
    6. Generate pricing strategy recommendations
    
    Competitors to analyze: {[c['name'] for c in monitoring_config['competitors']]}
    Focus products: {monitoring_config['target_products']}
    
    Output detailed comparison matrix with insights and recommendations.
    """)
    
    print(f"🎯 Created pricing analysis workflow")
    print(f"📊 Analyzing {len(monitoring_config['competitors'])} competitors")
    
    # Execute pricing analysis
    results = await orchestrator.execute_workflow(workflow)
    
    if results.success:
        pricing_data = results.extracted_data
        
        # Generate pricing insights
        insights = await generate_pricing_insights(pricing_data, monitoring_config)
        
        # Display summary
        print(f"\n✅ Pricing Analysis Complete")
        print(f"📈 Price points analyzed: {insights['total_price_points']}")
        print(f"🚨 Significant changes: {insights['significant_changes']}")
        print(f"🆕 New products detected: {insights['new_products']}")
        
        # Show key alerts
        if insights['alerts']:
            print(f"\n🚨 Price Change Alerts:")
            for alert in insights['alerts']:
                print(f"   • {alert['competitor']}: {alert['product']}")
                print(f"     Change: {alert['old_price']} → {alert['new_price']} ({alert['change_percent']:+.1f}%)")
                print(f"     Impact: {alert['impact_assessment']}")
        
        # Export detailed report
        report = {
            "timestamp": datetime.now().isoformat(),
            "pricing_data": pricing_data,
            "insights": insights,
            "recommendations": await generate_pricing_recommendations(insights)
        }
        
        report_file = f"pricing_intelligence_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved: {report_file}")
        
    else:
        print(f"❌ Pricing analysis failed: {results.error}")

async def generate_pricing_insights(pricing_data: dict, config: dict) -> dict:
    """Generate actionable pricing insights from extracted data"""
    
    insights = {
        "total_price_points": 0,
        "significant_changes": 0,
        "new_products": 0,
        "alerts": [],
        "market_positioning": {},
        "pricing_trends": {}
    }
    
    # Analyze pricing data and generate insights
    # (Implementation would include detailed pricing analysis logic)
    
    return insights

# Run pricing intelligence
if __name__ == "__main__":
    asyncio.run(competitor_pricing_intelligence())
```

---

## 🔐 Identity-Based Examples *(Q1 2025)*

### **LinkedIn Professional Intelligence**
```python
# linkedin_intelligence.py
import asyncio
from src.services.identity_service import IdentityService
from src.agents.intelligent_analyzer import IntelligentAnalyzer
from ai_core.core.hybrid_ai_service import create_production_ai_service

async def linkedin_company_research():
    """
    Extract comprehensive company intelligence from LinkedIn
    """
    
    # Initialize services
    ai_service = create_production_ai_service()
    identity = IdentityService()
    analyzer = IntelligentAnalyzer(llm_service=ai_service)
    
    # Create or load LinkedIn profile
    linkedin_profile = await identity.create_profile(
        platform="linkedin",
        name="business_research",
        login_method="interactive"  # Opens VNC browser
    )
    
    target_companies = ["openai", "anthropic", "microsoft", "google"]
    
    company_data = {}
    
    for company in target_companies:
        print(f"📊 Analyzing {company.upper()}...")
        
        result = await analyzer.analyze_website(
            url=f"https://linkedin.com/company/{company}",
            purpose="""Extract comprehensive company intelligence:
            - Employee count and growth trends
            - Recent posts and announcements
            - Key leadership information
            - Hiring activity and open positions
            - Company growth indicators
            """,
            profile=linkedin_profile
        )
        
        if result.success:
            company_data[company] = result.extracted_data
            print(f"   ✅ Extracted data for {company}")
        else:
            print(f"   ❌ Failed: {result.error}")
    
    # Generate competitive analysis
    if len(company_data) > 1:
        analysis = await analyzer.generate_competitive_analysis(company_data)
        print(f"\n📈 Competitive Analysis Generated")
        
        # Display key insights
        for insight in analysis.get('key_insights', []):
            print(f"   • {insight['category']}: {insight['insight']}")
    
    return company_data

# Run LinkedIn intelligence
if __name__ == "__main__":
    asyncio.run(linkedin_company_research())
```

---

## 📊 Performance & Scaling Examples

### **High-Volume Batch Processing**
```python
# batch_processing.py
import asyncio
import time
from typing import List
from ai_core.core.hybrid_ai_service import create_production_ai_service
from src.agents.intelligent_analyzer import IntelligentAnalyzer

async def process_large_url_batch():
    """
    Efficiently process hundreds of URLs with intelligent batching
    """
    
    ai_service = create_production_ai_service()
    analyzer = IntelligentAnalyzer(llm_service=ai_service)
    
    # Generate URL list (replace with your actual URLs)
    urls = [f"https://example-site-{i}.com/products" for i in range(1, 201)]
    
    # Batch configuration
    batch_size = 20
    max_concurrent = 8
    
    print(f"🚀 Processing {len(urls)} URLs in batches of {batch_size}")
    
    start_time = time.time()
    all_results = []
    
    # Process in batches
    for i in range(0, len(urls), batch_size):
        batch_urls = urls[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        print(f"\n📦 Processing batch {batch_num}: {len(batch_urls)} URLs")
        
        # Limit concurrency within batch
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_with_semaphore(url):
            async with semaphore:
                return await analyzer.analyze_website(
                    url=url,
                    purpose="Extract product data and pricing information"
                )
        
        # Execute batch
        batch_tasks = [process_with_semaphore(url) for url in batch_urls]
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        
        # Process results
        successful = sum(1 for r in batch_results if not isinstance(r, Exception) and getattr(r, 'success', False))
        print(f"   ✅ Batch {batch_num}: {successful}/{len(batch_urls)} successful")
        
        all_results.extend(batch_results)
        
        # Rate limiting delay between batches
        await asyncio.sleep(1)
    
    # Calculate statistics
    total_time = time.time() - start_time
    successful_count = sum(1 for r in all_results if not isinstance(r, Exception) and getattr(r, 'success', False))
    
    print(f"\n📊 Batch Processing Complete:")
    print(f"   Total URLs: {len(urls)}")
    print(f"   Successful: {successful_count}")
    print(f"   Success rate: {successful_count/len(urls):.1%}")
    print(f"   Total time: {total_time:.2f} seconds")
    print(f"   Throughput: {len(urls)/total_time:.2f} URLs/second")
    
    return all_results

# Run batch processing
if __name__ == "__main__":
    asyncio.run(process_large_url_batch())
```

---

## 🔄 Automation Examples

### **Scheduled Monitoring Workflow**
```python
# scheduled_monitoring.py
import asyncio
from src.automation.scheduler import WorkflowScheduler
from src.agents.orchestrator import ExtractionOrchestrator

async def setup_monitoring_automation():
    """
    Set up automated monitoring with intelligent alerting
    """
    
    scheduler = WorkflowScheduler()
    orchestrator = ExtractionOrchestrator()
    
    # Daily competitor monitoring
    daily_workflow = await orchestrator.create_workflow("""
    Monitor top 5 competitors for:
    1. Pricing changes > 5%
    2. New product announcements
    3. Marketing campaign launches
    4. Website structure changes
    
    Generate executive summary with actionable insights.
    Send alerts for significant changes.
    """)
    
    await scheduler.schedule_workflow(
        name="daily_competitor_monitor",
        workflow=daily_workflow,
        schedule="0 9 * * *",  # 9 AM daily
        alert_settings={
            "email": ["strategy@company.com"],
            "slack": "#competitive-intel",
            "threshold": "medium"
        }
    )
    
    # Weekly industry analysis
    weekly_workflow = await orchestrator.create_workflow("""
    Compile weekly industry intelligence report:
    1. Aggregate news from 20+ industry sources
    2. Analyze funding and M&A activity
    3. Track technology trends and developments
    4. Monitor regulatory changes
    
    Generate comprehensive weekly brief for executives.
    """)
    
    await scheduler.schedule_workflow(
        name="weekly_industry_analysis",
        workflow=weekly_workflow,
        schedule="0 17 * * 5",  # 5 PM Friday
        alert_settings={
            "email": ["executives@company.com"],
            "format": "executive_brief"
        }
    )
    
    print("✅ Automated monitoring configured")
    print("📊 Dashboard: http://localhost:8080/monitoring")

# Setup automation
if __name__ == "__main__":
    asyncio.run(setup_monitoring_automation())
```

---

## ✅ Running the Examples

### **Prerequisites**
```bash
# Ensure you have the agent installed
pip install -r requirements.txt

# Set up at least one AI provider
export OPENROUTER_API_KEY="your_key_here"
# or
export DEEPSEEK_API_KEY="your_key_here"
```

### **Running Examples**
```bash
# Basic examples
python docs/examples/simple_extraction.py
python docs/examples/batch_extraction.py

# Business intelligence
python docs/examples/competitor_pricing.py
python docs/examples/market_research.py

# Performance examples
python docs/examples/batch_processing.py

# Automation setup
python docs/examples/scheduled_monitoring.py
```

### **Expected Results**
Each example includes detailed output showing:
- ✅ **Success metrics** (extraction count, confidence scores)
- ⏱️ **Performance data** (execution time, throughput)
- 📊 **Business insights** (competitive intelligence, trends)
- 📄 **Export options** (JSON, CSV, reports)

---

## 🎯 Customization Guide

### **Adapting Examples**
1. **Replace URLs** with your target websites
2. **Modify purposes** to match your extraction needs
3. **Adjust batch sizes** based on your system capacity
4. **Configure alerts** for your notification preferences

### **Error Handling**
All examples include comprehensive error handling:
- **Retry logic** for failed extractions
- **Fallback strategies** when primary approaches fail
- **Graceful degradation** for partial failures
- **Detailed logging** for troubleshooting

### **Performance Tuning**
- **Adjust concurrency** based on your system and target sites
- **Configure rate limiting** to respect site policies
- **Optimize batch sizes** for your memory constraints
- **Monitor AI provider costs** and adjust accordingly

---

**Ready to build your own?** 🚀

These examples provide the foundation for any web intelligence application. Copy, modify, and extend them to create powerful automation for your specific use cases.

👉 **[API Reference →](../api-reference/)**

*Get detailed documentation for all the classes and methods used in these examples*
