"""
Test script to verify AI-first architecture setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core.registry import tool_registry
from ai_core.planner import AIPlanner, PlanExecutor
import asyncio
import json


def test_tool_registry():
    """Test that tools are being registered correctly"""
    print("Testing Tool Registry...")
    
    # Import tools to trigger registration
    try:
        from ai_core.tools import crawler
    except ImportError as e:
        print(f"Note: Could not import crawler tool: {e}")
        print("This is expected if crawl4ai is not installed yet.")
    
    # Import other tools that don't have external dependencies
    try:
        from ai_core.tools import database
        print("✓ Database tool imported")
    except ImportError as e:
        print(f"✗ Database tool import failed: {e}")
    
    try:
        from ai_core.tools import analyzer
        print("✓ Analyzer tool imported")
    except ImportError as e:
        print(f"✗ Analyzer tool import failed: {e}")
    
    try:
        from ai_core.tools import exporter
        print("✓ Exporter tool imported")
    except ImportError as e:
        print(f"✗ Exporter tool import failed: {e}")
    
    # Get all registered tools
    tools = tool_registry.get_all_tools()
    print(f"Registered tools: {list(tools.keys())}")
    
    # Get tool manifest
    manifest = tool_registry.get_tool_manifest()
    print(f"\nTool Manifest (first tool):")
    if manifest["tools"]:
        print(json.dumps(manifest["tools"][0], indent=2))
    
    # Search by capability
    web_tools = tool_registry.search_tools_by_capability("web")
    print(f"\nTools with 'web' capability: {web_tools}")
    
    return len(tools) > 0


def test_ai_planner():
    """Test AI planner creation"""
    print("\n\nTesting AI Planner...")
    
    planner = AIPlanner()
    
    # Test multiple requests
    test_requests = [
        "Extract product prices from https://example.com/products",
        "Scrape news from CNN, analyze sentiment, and export to Excel",
        "Get all restaurants in Chicago, store in database, and create CSV report"
    ]
    
    for test_request in test_requests:
        print(f"\nUser request: {test_request}")
        
        # This will fail if Ollama is not running, but shows the structure
        try:
            plan = planner.create_plan(test_request)
            print(f"\nGenerated plan:")
            print(f"- ID: {plan.plan_id}")
            print(f"- Description: {plan.description}")
            print(f"- Confidence: {plan.confidence}")
            print(f"- Steps: {len(plan.steps)}")
            
            for step in plan.steps:
                print(f"  Step {step.step_id}: {step.tool} - {step.description}")
                
        except Exception as e:
            # Show fallback plan
            fallback = planner._create_fallback_plan(test_request)
            print(f"\nFallback plan created (Ollama not available):")
            print(f"- Steps: {len(fallback.steps)}")
            for step in fallback.steps:
                print(f"  Step {step.step_id}: {step.tool}")


async def test_tool_execution():
    """Test direct tool execution"""
    print("\n\nTesting Tool Capabilities...")
    
    # List all available tools and their capabilities
    all_tools = tool_registry.get_all_tools()
    
    if all_tools:
        print(f"\nFound {len(all_tools)} registered tools:\n")
        
        for tool_name, tool_info in all_tools.items():
            print(f"📦 {tool_name}:")
            print(f"   Description: {tool_info['description']}")
            print(f"   Category: {tool_info['category']}")
            print(f"   Parameters: {len(tool_info['parameters'])} params")
            print(f"   Examples: {len(tool_info['examples'])} examples")
            print(f"   Capabilities: {len(tool_info['capabilities'])} capabilities")
            print()
    else:
        print("No tools registered!")
    
    # Test capability search
    print("\nSearching for tools by capability:")
    web_tools = tool_registry.search_tools_by_capability("web")
    print(f"Tools with 'web' capability: {web_tools}")
    
    data_tools = tool_registry.search_tools_by_capability("data")
    print(f"Tools with 'data' capability: {data_tools}")
    
    export_tools = tool_registry.get_tools_by_category("export")
    print(f"Tools in 'export' category: {export_tools}")


def main():
    """Run all tests"""
    print("=== AI-First Architecture Test ===\n")
    
    # Test 1: Tool Registry
    registry_ok = test_tool_registry()
    
    # Test 2: AI Planner
    test_ai_planner()
    
    # Test 3: Tool Execution
    asyncio.run(test_tool_execution())
    
    # Count tools
    tool_count = len(tool_registry.get_all_tools())
    
    print("\n\n=== Summary ===")
    print(f"Tool Registry: {'✓' if registry_ok else '✗'}")
    print(f"Total Tools Registered: {tool_count}")
    print(f"- Crawler: {'✓' if 'crawl_web' in tool_registry.get_all_tools() else 'Needs crawl4ai'}")
    print(f"- Database: {'✓' if 'store_data' in tool_registry.get_all_tools() else '✗'}")
    print(f"- Analyzer: {'✓' if 'analyze_content' in tool_registry.get_all_tools() else '✗'}")
    print(f"- Exporter: {'✓' if 'export_csv' in tool_registry.get_all_tools() else '✗'}")
    
    print("\nNext steps:")
    if tool_count < 4:
        print("1. Install crawl4ai to enable crawler tools")
    print("1. Test with Ollama (already installed!)")
    print("2. Start removing hardcoded logic from web_ui_server.py")
    print("3. Connect existing extraction strategies")
    print("4. Implement learning system with ChromaDB")
    print("5. Add Claude MCP teacher interface")


if __name__ == "__main__":
    main()
