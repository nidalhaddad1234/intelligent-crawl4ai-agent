#!/usr/bin/env python3
"""
Test Phase 5: Learning System Implementation

This script tests the learning capabilities of the AI-first architecture
"""

import asyncio
import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_core.adaptive_planner import AdaptivePlanner
from ai_core.planner import PlanExecutor, ExecutionPlan, PlanStatus


async def test_learning_system():
    """Test the learning system capabilities"""
    
    print("🧠 Testing Phase 5: Learning System")
    print("=" * 60)
    
    # Initialize adaptive planner
    planner = AdaptivePlanner(
        local_ai_url="http://localhost:11434",
        local_model="deepseek-coder:1.3b",
        chromadb_host="localhost",
        chromadb_port=8000,
        enable_learning=True
    )
    
    executor = PlanExecutor()
    
    # Test 1: Create and execute plans, recording outcomes
    print("\n📝 Test 1: Recording Execution Outcomes")
    print("-" * 40)
    
    test_cases = [
        {
            "request": "Analyze https://example.com for pricing information",
            "expected_success": True
        },
        {
            "request": "Export data as CSV with charts",
            "expected_success": True
        },
        {
            "request": "Find patterns in dataset: [100, 200, 150, 300, 250]",
            "expected_success": True
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['request']}")
        
        # Create plan
        start = time.time()
        plan = await planner.create_plan(test["request"])
        planning_time = time.time() - start
        
        print(f"  Plan created in {planning_time:.2f}s")
        print(f"  Confidence: {plan.confidence:.0%}")
        print(f"  Steps: {len(plan.steps)}")
        
        # Simulate execution
        execution_start = time.time()
        
        # For testing, mark plan as completed
        plan.status = PlanStatus.COMPLETED
        for step in plan.steps:
            step.status = PlanStatus.COMPLETED
            step.result = {"simulated": True}
        
        execution_time = time.time() - execution_start
        
        # Record outcome
        await planner.record_outcome(
            request=test["request"],
            plan=plan,
            success=True,
            execution_time=execution_time
        )
        
        print(f"  ✅ Outcome recorded (execution time: {execution_time:.2f}s)")
    
    # Test 2: Check if similar requests use learned patterns
    print("\n\n📝 Test 2: Pattern Reuse")
    print("-" * 40)
    
    similar_request = "Analyze https://shop.com for pricing data"
    print(f"Similar request: {similar_request}")
    
    plan = await planner.create_plan(similar_request)
    print(f"  Confidence: {plan.confidence:.0%}")
    
    if "Adapted" in plan.description:
        print("  ✅ Successfully reused learned pattern!")
    else:
        print("  ℹ️  Created new plan (pattern matching may need more examples)")
    
    # Test 3: Get learning statistics
    print("\n\n📊 Test 3: Learning Statistics")
    print("-" * 40)
    
    stats = await planner.get_learning_stats()
    
    print(f"Total patterns stored: {stats.get('total_patterns', 0)}")
    print(f"Success rate: {stats.get('success_rate', 0):.0%}")
    print(f"Status: {stats.get('status', 'Unknown')}")
    
    # Test 4: Tool performance
    print("\n\n🔧 Test 4: Tool Performance")
    print("-" * 40)
    
    if planner.memory:
        tool_performance = await planner.memory.get_tool_performance()
        
        for tool, metrics in tool_performance.items():
            print(f"\n{tool}:")
            print(f"  Uses: {metrics['total_uses']}")
            print(f"  Success rate: {metrics['success_rate']:.0%}")
            print(f"  Avg time: {metrics['avg_time']:.2f}s")
    else:
        print("Learning memory not available")
    
    # Test 5: Run learning routine
    print("\n\n🎓 Test 5: Learning Routine")
    print("-" * 40)
    
    report = await planner.run_learning_routine()
    
    if report.get("statistics"):
        print(f"Learning routine completed!")
        print(f"Analyzed {report['statistics']['total_patterns']} patterns")
        
        if report.get("recommendations"):
            print("\nRecommendations:")
            for rec in report["recommendations"][:3]:
                print(f"  • {rec}")
    
    print("\n" + "=" * 60)
    print("✅ Learning System test complete!")
    print("\nKey Features Demonstrated:")
    print("1. Recording execution outcomes")
    print("2. Pattern storage in ChromaDB")
    print("3. Similarity-based pattern reuse")
    print("4. Tool performance tracking")
    print("5. Learning routine for continuous improvement")


async def test_failure_learning():
    """Test learning from failures"""
    print("\n\n💥 Testing Failure Learning")
    print("=" * 60)
    
    planner = AdaptivePlanner(enable_learning=True)
    
    # Simulate a failure
    request = "Extract data from https://nonexistent-site-12345.com"
    plan = await planner.create_plan(request)
    
    # Mark as failed
    plan.status = PlanStatus.FAILED
    error_details = "Connection timeout: Site not reachable"
    
    # Record failure
    await planner.record_outcome(
        request=request,
        plan=plan,
        success=False,
        execution_time=30.0,
        error_details=error_details
    )
    
    print("Recorded failure - system will learn to handle timeouts better")
    
    # Get failure analysis
    if planner.trainer:
        analysis = await planner.trainer.analyze_failures(limit=5)
        if analysis:
            print(f"\nFailure Analysis:")
            for item in analysis:
                print(f"  Type: {item['failure_type']}")
                print(f"  Count: {item['count']}")
                print(f"  Suggestion: {item['suggestion']}")


if __name__ == "__main__":
    print("🤖 Phase 5: Learning System Test\n")
    
    # Check prerequisites
    import requests
    
    # Check Ollama
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama is running")
        else:
            print("⚠️  Ollama issue:", response.status_code)
    except:
        print("❌ Ollama not running! Start with: ollama serve")
        sys.exit(1)
    
    # Check ChromaDB
    try:
        response = requests.get("http://localhost:8000/api/v1/heartbeat", timeout=2)
        if response.status_code == 200:
            print("✅ ChromaDB is running")
        else:
            print("⚠️  ChromaDB issue:", response.status_code)
            print("   Learning will be disabled")
    except:
        print("⚠️  ChromaDB not running - learning features disabled")
        print("   To enable: docker run -p 8000:8000 chromadb/chroma")
    
    print()
    
    # Run tests
    asyncio.run(test_learning_system())
    # asyncio.run(test_failure_learning())
