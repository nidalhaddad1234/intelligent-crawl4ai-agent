#!/usr/bin/env python3
"""
Example: AI-First Intelligent Scraping
Demonstrates how to use the AI-driven agent for various scraping scenarios
"""

import asyncio
import json
from typing import List, Dict, Any

# Import the AI-first components
from ai_core.enhanced_adaptive_planner import EnhancedAdaptivePlanner
from ai_core.planner import PlanExecutor
from ai_core.registry import tool_registry

# Example URLs for different scenarios
EXAMPLE_URLS = {
    "business_directories": [
        "https://www.yellowpages.com/new-york-ny/restaurants",
        "https://www.yelp.com/nyc/restaurants",
    ],
    "company_websites": [
        "https://www.stripe.com/about",
        "https://www.openai.com/about",
    ],
    "e_commerce": [
        "https://www.amazon.com/dp/B08N5WRWNW",
        "https://www.etsy.com/listing/1234567890",
    ],
    "news_articles": [
        "https://www.reuters.com/business/",
        "https://techcrunch.com/2024/01/15/ai-news/",
    ]
}

async def demonstrate_ai_planning():
    """Example: Show how AI creates plans from natural language"""
    
    print("🤖 Example 1: AI-Driven Planning")
    print("=" * 50)
    
    # Initialize AI planner
    planner = EnhancedAdaptivePlanner()
    executor = PlanExecutor()
    
    # Natural language request - NO HARDCODED LOGIC!
    user_request = "I need to extract company information from https://stripe.com/about including their mission, team size, and contact details"
    
    print(f"User Request: {user_request}")
    print("\nAI Creating Plan...")
    
    # AI creates the plan
    plan = await planner.create_plan(user_request)
    
    print(f"\nAI Plan (Confidence: {plan.confidence:.0%}):")
    print(f"Description: {plan.description}")
    print("\nSteps:")
    for step in plan.steps:
        print(f"  {step.step_id}. {step.tool}({step.parameters})")
        print(f"     Purpose: {step.description}")
    
    # Execute the plan
    print("\nExecuting AI Plan...")
    result = await executor.execute_plan(plan)
    
    print(f"\nResult: {result.status.value}")
    if result.status.value == "completed":
        for step in result.steps:
            if step.result:
                print(f"\n{step.description}:")
                print(json.dumps(step.result, indent=2)[:200] + "...")

async def demonstrate_learning_system():
    """Example: Show how the system learns from usage"""
    
    print("\n\n🧠 Example 2: Self-Learning System")
    print("=" * 50)
    
    planner = EnhancedAdaptivePlanner()
    
    # Check learning statistics
    stats = await planner.get_learning_stats()
    
    print("Learning System Statistics:")
    print(f"- Total Patterns Learned: {stats.get('total_patterns', 0)}")
    print(f"- Success Rate: {stats.get('success_rate', 0):.1%}")
    print(f"- Tools Used: {stats.get('tools_used', {})}")
    
    # Show how it adapts
    print("\nThe AI learns from:")
    print("- ✅ Successful execution patterns")
    print("- ❌ Failed attempts and errors")
    print("- 🎯 User feedback and corrections")
    print("- 📊 Performance metrics")

async def demonstrate_tool_discovery():
    """Example: Show available AI tools"""
    
    print("\n\n🔧 Example 3: AI-Discoverable Tools")
    print("=" * 50)
    
    # List all registered tools
    tools = tool_registry.list_tools()
    
    print("Available AI Tools:")
    for tool_name in tools:
        tool_info = tool_registry.get_tool(tool_name)
        if tool_info:
            print(f"\n📦 {tool_name}:")
            print(f"   Functions: {list(tool_info['functions'].keys())}")
            print(f"   Description: {tool_info.get('description', 'N/A')[:100]}...")

async def demonstrate_complex_request():
    """Example: Complex multi-step request"""
    
    print("\n\n🚀 Example 4: Complex Multi-Step Request")
    print("=" * 50)
    
    planner = EnhancedAdaptivePlanner()
    executor = PlanExecutor()
    
    # Complex request that requires multiple tools
    complex_request = """
    I need to:
    1. Crawl these 3 company websites for contact information
    2. Save the results to a database
    3. Analyze which companies have the most complete contact info
    4. Export a CSV report with the analysis
    
    URLs:
    - https://stripe.com/about
    - https://openai.com/about
    - https://anthropic.com/company
    """
    
    print(f"Complex Request: {complex_request[:100]}...")
    
    # AI figures out the entire workflow
    plan = await planner.create_plan(complex_request)
    
    print(f"\nAI Generated {len(plan.steps)} Steps:")
    for i, step in enumerate(plan.steps, 1):
        print(f"{i}. {step.tool} → {step.description}")

async def demonstrate_enhanced_capabilities():
    """Example: Show Phase 6 enhanced capabilities"""
    
    print("\n\n⚡ Example 5: Enhanced AI Capabilities (Phase 6)")
    print("=" * 50)
    
    planner = EnhancedAdaptivePlanner()
    
    # Get tool insights
    insights = planner.get_tool_insights()
    
    print("Tool Performance Insights:")
    if 'tool_performance' in insights:
        for tool, metrics in insights['tool_performance'].items():
            print(f"\n{tool}:")
            print(f"  - Avg Time: {metrics.get('avg_time', 0):.2f}s")
            print(f"  - Success Rate: {metrics.get('success_rate', 0):.1%}")
    
    # Get recommendations
    recommendations = planner.suggest_new_capabilities()
    
    print("\n\nAI Recommendations:")
    if recommendations.get('missing_tools'):
        print("\nSuggested New Tools:")
        for tool in recommendations['missing_tools'][:3]:
            print(f"  - {tool['intent']}: Create tool for '{tool['example_request']}'")

async def demonstrate_natural_language():
    """Example: Various natural language requests"""
    
    print("\n\n💬 Example 6: Natural Language Requests")
    print("=" * 50)
    
    planner = EnhancedAdaptivePlanner()
    
    example_requests = [
        "What's on this website? https://example.com",
        "Extract all email addresses from these 5 URLs: ...",
        "Compare pricing between these three competitors",
        "Monitor this website daily for changes",
        "Find all PDF documents on this site",
        "Export my last scraping results as Excel"
    ]
    
    print("The AI understands requests like:")
    for request in example_requests:
        print(f"  ✅ '{request}'")
    
    print("\nNo keywords or specific formats needed!")

def show_migration_guide():
    """Show how to migrate from old system"""
    
    print("\n\n📋 Migration from Rule-Based System")
    print("=" * 50)
    
    print("OLD WAY (Rule-Based):")
    print("```python")
    print("if 'analyze' in message:")
    print("    strategy = select_strategy(url)")
    print("    result = execute_strategy(strategy, url)")
    print("```")
    
    print("\nNEW WAY (AI-First):")
    print("```python")
    print("# Just ask in natural language!")
    print("plan = await planner.create_plan(user_request)")
    print("result = await executor.execute_plan(plan)")
    print("```")
    
    print("\nBenefits:")
    print("✅ No hardcoded logic")
    print("✅ Handles any request")
    print("✅ Self-improving")
    print("✅ Easier to extend")

async def main():
    """Run all examples"""
    
    print("🎯 AI-First Intelligent Crawl4AI Agent")
    print("=" * 60)
    print("Version 2.0 - Fully AI-Driven Architecture\n")
    
    await demonstrate_ai_planning()
    await demonstrate_learning_system()
    await demonstrate_tool_discovery()
    await demonstrate_complex_request()
    await demonstrate_enhanced_capabilities()
    await demonstrate_natural_language()
    show_migration_guide()
    
    print("\n" + "=" * 60)
    print("🌟 Key Principles:")
    print("1. Every decision is made by AI")
    print("2. No hardcoded business logic")
    print("3. System learns and improves")
    print("4. Natural language interface")
    print("5. Extensible through tools")
    
    print("\n📚 For API usage, see: web_ui_server.py")
    print("🔗 Documentation: docs/ai-first-architecture.md")

if __name__ == "__main__":
    # Note: This example assumes you have Ollama running locally
    # Install: https://ollama.ai
    # Run: ollama run deepseek-coder:1.3b
    asyncio.run(main())
