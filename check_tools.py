#!/usr/bin/env python3
"""
Tool Status Checker - Shows which tools and functions are available
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🔍 AI-First Intelligent Crawler - Tool Status")
print("=" * 60)

# Tool modules we expect
expected_tools = {
    'crawler': ['crawl_web', 'crawl_multiple', 'crawl_paginated'],
    'database': ['store_data', 'query_data', 'update_data', 'delete_data'],
    'analyzer': ['analyze_content', 'detect_patterns', 'compare_datasets'],
    'exporter': ['export_csv', 'export_json', 'export_excel', 'export_xml', 'export_html'],
    'extractor': ['extract_structured_data', 'extract_tables', 'extract_contact_info', 
                  'extract_lists', 'extract_metadata', 'extract_patterns', 'extract_by_proximity']
}

# Check each tool module
tool_status = {}
total_expected_functions = 0
total_loaded_functions = 0

for tool_name, expected_functions in expected_tools.items():
    total_expected_functions += len(expected_functions)
    print(f"\n📦 {tool_name.upper()} Tool:")
    
    try:
        module = __import__(f'ai_core.tools.{tool_name}', fromlist=[''])
        print(f"  ✅ Module loaded successfully")
        
        # Check individual functions
        loaded_functions = []
        for func_name in expected_functions:
            if hasattr(module, func_name):
                loaded_functions.append(func_name)
                print(f"    ✅ {func_name}")
            else:
                print(f"    ❌ {func_name} - not found")
        
        tool_status[tool_name] = {
            'loaded': True,
            'functions': loaded_functions,
            'total': len(loaded_functions)
        }
        total_loaded_functions += len(loaded_functions)
        
    except ImportError as e:
        print(f"  ❌ Module failed to load: {str(e)}")
        tool_status[tool_name] = {
            'loaded': False,
            'error': str(e),
            'functions': [],
            'total': 0
        }

# Check registry
print("\n" + "=" * 60)
print("📊 TOOL REGISTRY STATUS:")

try:
    from ai_core.registry import tool_registry
    registered_tools = tool_registry.list_tools()
    
    print(f"\n✅ Total functions registered: {len(registered_tools)}")
    print(f"✅ Expected functions: {total_expected_functions}")
    print(f"✅ Actually loaded: {total_loaded_functions}")
    
    if len(registered_tools) < total_expected_functions:
        print(f"\n⚠️  Missing {total_expected_functions - len(registered_tools)} functions!")
        
    # Group by tool
    print("\nRegistered functions by tool:")
    tool_groups = {}
    for func in sorted(registered_tools):
        # Try to determine which tool it belongs to
        for tool_name, funcs in expected_tools.items():
            if func in funcs:
                if tool_name not in tool_groups:
                    tool_groups[tool_name] = []
                tool_groups[tool_name].append(func)
                break
    
    for tool_name, funcs in sorted(tool_groups.items()):
        print(f"\n  {tool_name}: {len(funcs)} functions")
        for func in funcs:
            print(f"    - {func}")
            
except Exception as e:
    print(f"\n❌ Failed to check registry: {e}")

# Summary
print("\n" + "=" * 60)
print("📈 SUMMARY:")

working_tools = sum(1 for t in tool_status.values() if t['loaded'])
print(f"\n✅ Tool Modules: {working_tools}/{len(expected_tools)} loaded")
print(f"✅ Functions: {total_loaded_functions}/{total_expected_functions} available")

if working_tools < len(expected_tools):
    print("\n⚠️  TO FIX MISSING TOOLS:")
    print("Run: ./setup.sh")
    print("Or manually install:")
    for tool_name, status in tool_status.items():
        if not status['loaded']:
            if 'crawl4ai' in status['error']:
                print(f"  pip install crawl4ai>=0.3.0")
            elif 'psycopg' in status['error']:
                print(f"  pip install psycopg2-binary>=2.9.0")
            elif 'bs4' in status['error']:
                print(f"  pip install beautifulsoup4>=4.12.0")
            elif 'pandas' in status['error']:
                print(f"  pip install pandas>=2.0.0")

print("\n✨ For full setup, run: ./setup.sh")
print("=" * 60)
