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
    
    # Test simple request
    test_request = "Extract product prices from https://example.com/products"
    
    print(f"User request: {test_request}")
    
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
        print(f"Plan creation failed (expected if Ollama not running): {e}")
        
        # Show fallback plan
        fallback = planner._create_fallback_plan(test_request)
        print(f"\nFallback plan created:")
        print(f"- Steps: {len(fallback.steps)}")
        for step in fallback.steps:
            print(f"  Step {step.step_id}: {step.tool}")


async def test_tool_execution():
    """Test direct tool execution"""
    print("\n\nTesting Tool Execution...")
    
    # Get the crawl_web tool
    crawl_tool = tool_registry.get_tool("crawl_web")
    
    if crawl_tool:
        print("Found crawl_web tool")
        # Would execute here if we wanted to actually crawl
        print("Tool ready for execution")
    else:
        print("crawl_web tool not found!")


def main():
    """Run all tests"""
    print("=== AI-First Architecture Test ===\n")
    
    # Test 1: Tool Registry
    registry_ok = test_tool_registry()
    
    # Test 2: AI Planner
    test_ai_planner()
    
    # Test 3: Tool Execution
    asyncio.run(test_tool_execution())
    
    print("\n\n=== Summary ===")
    print(f"Tool Registry: {'✓' if registry_ok else '✗'}")
    print("\nNext steps:")
    print("1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh")
    print("2. Pull model: ollama pull deepseek")
    print("3. Implement remaining tools (database, analyzer, exporter)")
    print("4. Connect to existing Crawl4AI strategies")
    print("5. Remove hardcoded logic from web_ui_server.py")


if __name__ == "__main__":
    main()
