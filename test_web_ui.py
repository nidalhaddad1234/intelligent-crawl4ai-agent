#!/usr/bin/env python3
"""
Test script for Web UI integration
Tests all the major endpoints and functionality
"""
import asyncio
import aiohttp
import json
import sys
from datetime import datetime

async def test_web_ui():
    """Test the Web UI endpoints"""
    base_url = "http://localhost:8888"
    
    print("🧪 Testing Intelligent Crawl4AI Web UI")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Health endpoint
            print("🔍 Testing health endpoint...")
            async with session.get(f"{base_url}/health") as resp:
                if resp.status == 200:
                    health_data = await resp.json()
                    print(f"✅ Health check passed: {health_data}")
                else:
                    print(f"❌ Health check failed: {resp.status}")
                    return False
            
            # Test 2: Session creation
            print("\n🔍 Testing session creation...")
            async with session.post(f"{base_url}/api/sessions") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    session_id = data["session_id"]
                    print(f"✅ Session created: {session_id}")
                else:
                    print(f"❌ Session creation failed: {resp.status}")
                    return False
            
            # Test 3: Chat endpoint with help message
            print("\n🔍 Testing chat endpoint (help)...")
            chat_data = {
                "message": "What can you help me with?",
                "session_id": session_id
            }
            async with session.post(f"{base_url}/api/chat", json=chat_data) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    print("✅ Chat endpoint working")
                    print(f"Response preview: {response['response'][:200]}...")
                else:
                    print(f"❌ Chat endpoint failed: {resp.status}")
                    return False
            
            # Test 4: Chat endpoint with scraping request
            print("\n🔍 Testing chat endpoint (scraping request)...")
            chat_data = {
                "message": "Scrape data from this website",
                "urls": ["https://example.com"],
                "session_id": session_id
            }
            async with session.post(f"{base_url}/api/chat", json=chat_data) as resp:
                if resp.status == 200:
                    response = await resp.json()
                    print("✅ Scraping request handled")
                    print(f"Response preview: {response['response'][:200]}...")
                else:
                    print(f"❌ Scraping request failed: {resp.status}")
                    return False
            
            # Test 5: System status endpoint
            print("\n🔍 Testing system status endpoint...")
            async with session.get(f"{base_url}/api/system/status") as resp:
                if resp.status == 200:
                    status_data = await resp.json()
                    print("✅ System status endpoint working")
                    print(f"Status: {status_data['status']}")
                    print(f"Components: {status_data['components_health']}")
                else:
                    print(f"❌ System status failed: {resp.status}")
                    return False
            
            # Test 6: Message history
            print("\n🔍 Testing message history...")
            async with session.get(f"{base_url}/api/sessions/{session_id}/messages") as resp:
                if resp.status == 200:
                    messages = await resp.json()
                    print(f"✅ Message history retrieved: {len(messages)} messages")
                else:
                    print(f"❌ Message history failed: {resp.status}")
                    return False
            
            print("\n🎉 All tests passed! Web UI is working correctly.")
            print("\n📋 Test Summary:")
            print("✅ Health check")
            print("✅ Session management") 
            print("✅ Chat functionality")
            print("✅ Scraping requests")
            print("✅ System status")
            print("✅ Message history")
            print(f"\n🌐 Access the Web UI at: {base_url}")
            
            return True
            
        except aiohttp.ClientError as e:
            print(f"❌ Connection error: {e}")
            print("\n💡 Make sure the Web UI server is running:")
            print("   docker-compose up -d web-ui")
            return False
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            return False

async def test_websocket():
    """Test WebSocket functionality"""
    import websockets
    
    print("\n🔌 Testing WebSocket connection...")
    
    try:
        # Create a session first
        async with aiohttp.ClientSession() as session:
            async with session.post("http://localhost:8888/api/sessions") as resp:
                data = await resp.json()
                session_id = data["session_id"]
        
        # Test WebSocket
        uri = f"ws://localhost:8888/ws/{session_id}"
        async with websockets.connect(uri) as websocket:
            # Send a test message
            await websocket.send(json.dumps({
                "message": "Hello via WebSocket!",
                "urls": None
            }))
            
            # Receive response
            response = await websocket.recv()
            data = json.loads(response)
            
            print("✅ WebSocket connection successful")
            print(f"Response type: {data.get('type')}")
            print(f"Response preview: {data.get('content', '')[:100]}...")
            
            return True
            
    except ImportError:
        print("⚠️  websockets library not installed - skipping WebSocket test")
        print("   Install with: pip install websockets")
        return True
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

def main():
    """Main test function"""
    try:
        # Test HTTP endpoints
        success = asyncio.run(test_web_ui())
        
        if success:
            # Test WebSocket if available
            asyncio.run(test_websocket())
            
            print("\n🎯 Next Steps:")
            print("1. Open http://localhost:8888 in your browser")
            print("2. Try asking: 'What can you help me with?'")
            print("3. Test scraping with: 'Analyze this website: https://example.com'")
            print("4. Check system status with: 'Show me the system status'")
            
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
