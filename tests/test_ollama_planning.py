"""
Test AI Planning with Ollama
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core.registry import tool_registry
from ai_core.planner import AIPlanner
from ai_core.tools import analyzer, exporter  # These should work
import json


def test_ollama_planning():
    """Test AI planning with real Ollama"""
    print("=== Testing AI Planning with Ollama ===\n")
    
    # Initialize planner
    planner = AIPlanner(local_model="llama3.1:latest")  # Use llama3.1 instead
    
    # Test requests
    test_requests = [
        "Analyze this data for patterns: [{'price': 100}, {'price': 200}, {'price': 150}]",
        "Export this data to CSV: [{'name': 'Product A', 'price': 99.99}]",
        "Compare two datasets and export results to Excel"
    ]
    
    for request in test_requests:
        print(f"Request: {request}")
        print("-" * 60)
        
        try:
            plan = planner.create_plan(request)
            print(f"Plan ID: {plan.plan_id}")
            print(f"Description: {plan.description}")
            print(f"Confidence: {plan.confidence}")
            print(f"Steps:")
            
            for step in plan.steps:
                print(f"  Step {step.step_id}: {step.tool}")
                print(f"    Description: {step.description}")
                print(f"    Parameters: {json.dumps(step.parameters, indent=6)}")
                
        except Exception as e:
            print(f"Error: {e}")
            
        print("\n")


def test_simple_prompt():
    """Test with a simpler prompt format"""
    print("=== Testing Simple Prompt ===\n")
    
    import requests
    
    # Direct test with Ollama
    prompt = """Task: Extract prices from a website
Tools available: analyze_content, export_csv, export_json
Create a plan with steps.
Return only JSON: {"steps": [{"tool": "...", "action": "..."}]}"""
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.1:latest",
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"Raw response: {result.get('response', 'No response')}")
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Show available tools
    tools = tool_registry.get_all_tools()
    print(f"Available tools: {list(tools.keys())}\n")
    
    # Test planning
    test_ollama_planning()
    
    # Test simple prompt
    test_simple_prompt()
