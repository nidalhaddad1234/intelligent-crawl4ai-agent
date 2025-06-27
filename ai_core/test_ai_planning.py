#!/usr/bin/env python3
"""
Test AI Planning - Verify AI can handle all request types

Run this to ensure AI planning works before removing hardcoded logic
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core.planner import AIPlanner
from ai_core.registry import tool_registry

# Import tools to register them
try:
    from ai_core.tools import crawler, database, analyzer, exporter
except ImportError:
    print("Warning: Some tools not available")


async def test_ai_planning():
    """Test various user requests to see what plans AI creates"""
    
    # Initialize planner
    planner = AIPlanner(
        local_ai_url="http://localhost:11434",
        local_model="deepseek-coder:1.3b"
    )
    
    # Test cases covering all the old hardcoded scenarios
    test_cases = [
        # Analysis requests (used to check for 'analyze', 'check', 'examine')
        "Analyze https://example.com for contact information",
        "Check the structure of https://shop.com",
        "Examine https://news.com and tell me what data is available",
        
        # Scraping requests (used to check for 'scrape', 'extract', 'crawl')
        "Scrape product data from https://shop.com",
        "Extract all email addresses from these URLs",
        "Crawl https://directory.com and get business listings",
        "Get exchange rates from https://xe.com",
        
        # Export requests (used to check for 'export', 'csv', 'excel')
        "Export my data as CSV",
        "Save the results to Excel with formatting",
        "Download everything as JSON",
        
        # Pattern detection (new capability)
        "Find patterns in the pricing data",
        "Detect anomalies in the scraped content",
        
        # Comparison requests
        "Compare products from Amazon and eBay",
        "Analyze the differences between these datasets",
        
        # Complex multi-step requests
        "Scrape products from multiple sites, find the cheapest prices, and export to Excel",
        "Analyze these 5 websites and tell me which has the best data structure",
        
        # Ambiguous requests (AI should ask for clarification)
        "Help me with something",
        "Process this data",
        "What can you do?"
    ]
    
    print("🧪 Testing AI Planning System")
    print("=" * 60)
    
    # Show available tools
    tools = tool_registry.list_tools()
    print(f"\n📦 Available Tools ({len(tools)}):")
    for tool in tools:
        print(f"  - {tool}")
    
    print("\n" + "=" * 60)
    
    # Test each case
    for i, test_request in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: '{test_request}'")
        
        try:
            # Create plan
            plan = planner.create_plan(test_request)
            
            print(f"📋 Plan: {plan.description}")
            print(f"🎯 Confidence: {plan.confidence:.0%}")
            
            if plan.steps:
                print("📝 Steps:")
                for step in plan.steps:
                    params_str = ", ".join(f"{k}={v}" for k, v in step.parameters.items())
                    print(f"   {step.step_id}. {step.tool}({params_str})")
                    if step.depends_on:
                        print(f"      ↳ depends on: {step.depends_on}")
            else:
                print("   ⚠️  No steps generated - AI needs clarification")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        print("-" * 40)
    
    print("\n✅ AI Planning test complete!")
    print("\nNext steps:")
    print("1. If plans look correct, proceed with Phase 4")
    print("2. If plans are wrong, tune the planning prompt")
    print("3. Check Ollama is running: curl http://localhost:11434/api/tags")


async def test_plan_execution():
    """Test executing a simple plan"""
    print("\n\n🚀 Testing Plan Execution")
    print("=" * 60)
    
    from ai_core.planner import PlanExecutor
    
    planner = AIPlanner()
    executor = PlanExecutor()
    
    # Simple test case
    test_request = "Analyze this data for patterns: [100, 200, 150, 300, 250]"
    
    print(f"Request: {test_request}")
    
    # Create and execute plan
    plan = planner.create_plan(test_request)
    
    if plan.steps:
        print(f"Executing plan with {len(plan.steps)} steps...")
        executed_plan = await executor.execute_plan(plan)
        
        print(f"\nPlan Status: {executed_plan.status.value}")
        
        for step in executed_plan.steps:
            print(f"\nStep {step.step_id}: {step.tool}")
            print(f"  Status: {step.status.value}")
            if step.result:
                print(f"  Result: {step.result}")
            if step.error:
                print(f"  Error: {step.error}")
    else:
        print("No plan generated!")


if __name__ == "__main__":
    print("🤖 AI-First Architecture Test Suite\n")
    
    # Check if Ollama is available
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama is running")
            models = response.json().get("models", [])
            print(f"   Available models: {[m['name'] for m in models]}")
        else:
            print("⚠️  Ollama returned status:", response.status_code)
    except Exception as e:
        print("❌ Ollama is not running! Start it with: ollama serve")
        print(f"   Error: {e}")
        sys.exit(1)
    
    # Run tests
    asyncio.run(test_ai_planning())
    # asyncio.run(test_plan_execution())
