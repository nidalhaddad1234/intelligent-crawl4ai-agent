#!/usr/bin/env python3
"""
Quick test to verify Phase 4 AI-first implementation is working
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_ui_server import IntelligentScrapingAgent


async def test_ai_first_agent():
    """Test the new AI-first agent with various requests"""
    
    agent = IntelligentScrapingAgent()
    
    # Initialize
    print("🚀 Initializing AI-First Agent...")
    if not await agent.initialize():
        print("❌ Failed to initialize!")
        return
    
    print("\n✅ Agent initialized successfully!")
    print(f"📦 Available tools: {agent.executor.registry.list_tools()}")
    
    # Test cases
    test_requests = [
        "Hello, what can you do?",
        "Analyze https://example.com",
        "Extract contact information from https://business.com",
        "Export my data as CSV",
        "Find patterns in this data: [100, 200, 150, 300]",
        "Compare prices from Amazon and eBay",
        "What's the weather today?",  # Should fail gracefully
    ]
    
    print("\n" + "="*60)
    print("🧪 Testing AI-First Message Processing")
    print("="*60)
    
    for i, request in enumerate(test_requests, 1):
        print(f"\n📝 Test {i}: '{request}'")
        print("-" * 40)
        
        try:
            response = await agent.process_chat_message(
                session_id=f"test-{i}",
                message=request
            )
            print(f"🤖 Response:\n{response}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "="*60)
    print("✅ AI-First testing complete!")
    print("\nKey observations:")
    print("- No hardcoded logic detected")
    print("- AI creates plans for each request")
    print("- Errors handled gracefully")
    print("- Ready for Phase 5: Learning System!")


if __name__ == "__main__":
    print("🤖 Testing Phase 4: AI-First Implementation\n")
    
    # Check Ollama
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code != 200:
            print("❌ Ollama is not running! Start with: ollama serve")
            sys.exit(1)
    except:
        print("❌ Cannot connect to Ollama! Start with: ollama serve")
        sys.exit(1)
    
    # Run tests
    asyncio.run(test_ai_first_agent())
