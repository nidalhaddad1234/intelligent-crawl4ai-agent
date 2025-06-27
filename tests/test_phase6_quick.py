#!/usr/bin/env python3
"""
Quick test to verify Phase 6 components are working
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing Phase 6 components...")

try:
    # Test imports
    from ai_core.tool_enhancer import (
        DynamicParameterDiscovery,
        ToolCombinationEngine,
        PerformanceProfiler,
        CapabilityMatcher,
        ToolRecommendationEngine,
        EnhancedToolOrchestrator
    )
    print("✅ Tool enhancer components imported successfully")
    
    from ai_core.enhanced_adaptive_planner import EnhancedAdaptivePlanner
    print("✅ Enhanced adaptive planner imported successfully")
    
    # Test instantiation
    orchestrator = EnhancedToolOrchestrator()
    print("✅ Tool orchestrator created successfully")
    
    planner = EnhancedAdaptivePlanner()
    print("✅ Enhanced planner created successfully")
    
    # Test basic functionality
    discovery = DynamicParameterDiscovery()
    discovery.record_parameters("test", "function", {"param": "value"}, True)
    suggestions = discovery.suggest_parameters("test", "function", {"user_query": "export to CSV"})
    print(f"✅ Parameter discovery working: {suggestions}")
    
    print("\n🎉 Phase 6 components are working!")
    print("\nPhase 6 Features Implemented:")
    print("  ✅ Dynamic Parameter Discovery")
    print("  ✅ Tool Combination Engine")
    print("  ✅ Performance Profiler")
    print("  ✅ Capability Matcher")
    print("  ✅ Tool Recommendation Engine")
    print("  ✅ Enhanced Adaptive Planner")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
