"""
SunBun Agent Protocol Compliance Tests
Verifies that the backend follows the Agent Protocol standard for frontend integration.
"""

import requests
import time
from typing import Dict, Any


BASE_URL = "http://127.0.0.1:2026"
AGENT_ID = "agent"


def print_test(name: str):
    """Print test header"""
    print(f"\n{'='*70}")
    print(f"🧪 {name}")
    print('='*70)


def test_server_health():
    """Test if Aegra server is running"""
    print_test("Test 1: Server Health Check")
    
    try:
        response = requests.get(f"{BASE_URL}/info", timeout=5)
        
        if response.status_code == 200:
            print("✅ Server is running")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server")
        print("   Run: aegra dev")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


def test_create_thread():
    """Test creating a new thread"""
    print_test("Test 2: Create Thread")
    
    try:
        response = requests.post(
            f"{BASE_URL}/threads",
            json={},
            timeout=5
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to create thread: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
        
        data = response.json()
        thread_id = data.get("thread_id")
        
        if not thread_id:
            print("❌ No thread_id in response")
            return None
        
        print(f"✅ Thread created: {thread_id}")
        return thread_id
        
    except Exception as e:
        print(f"❌ Thread creation failed: {e}")
        return None


def test_send_message(thread_id: str, message: str):
    """Test sending a message to a thread"""
    print_test(f"Test 3: Send Message ('{message}')")
    
    try:
        response = requests.post(
            f"{BASE_URL}/threads/{thread_id}/runs",
            json={
                "assistant_id": AGENT_ID,
                "input": {
                    "messages": [
                        {"type": "human", "content": message}
                    ]
                }
            },
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to send message: {response.status_code}")
            print(f"   Response: {response.text}")
            return None
        
        data = response.json()
        
        # Check for messages in response
        messages = data.get("messages", [])
        
        if not messages:
            print("⚠️  No messages in response")
            return data
        
        # Find AI response
        ai_messages = [m for m in messages if m.get("type") == "ai"]
        
        if ai_messages:
            last_ai = ai_messages[-1]
            content = last_ai.get("content", "")
            print(f"✅ Bot response: {content[:150]}...")
            
            # Check for button metadata
            metadata = last_ai.get("additional_kwargs", {}).get("metadata", {})
            options = metadata.get("options", [])
            
            if options:
                print(f"   📱 {len(options)} buttons available:")
                for opt in options[:3]:
                    print(f"      • {opt.get('label')} → {opt.get('value')}")
        
        return data
        
    except Exception as e:
        print(f"❌ Message send failed: {e}")
        return None


def test_streaming_response(thread_id: str, message: str):
    """Test streaming mode"""
    print_test(f"Test 4: Streaming Response")
    
    try:
        response = requests.post(
            f"{BASE_URL}/threads/{thread_id}/runs/stream",
            json={
                "assistant_id": AGENT_ID,
                "input": {
                    "messages": [
                        {"type": "human", "content": message}
                    ]
                },
                "stream_mode": "messages"
            },
            stream=True,
            timeout=15
        )
        
        if response.status_code != 200:
            print(f"❌ Streaming failed: {response.status_code}")
            return False
        
        chunks_received = 0
        for line in response.iter_lines():
            if line:
                chunks_received += 1
                # Decode SSE format
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]  # Remove 'data: ' prefix
                    if chunks_received <= 3:  # Show first few chunks
                        print(f"   📦 Chunk {chunks_received}: {data_str[:100]}...")
        
        if chunks_received > 0:
            print(f"✅ Received {chunks_received} streaming chunks")
            return True
        else:
            print("⚠️  No streaming chunks received")
            return False
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False


def test_thread_state(thread_id: str):
    """Test retrieving thread state"""
    print_test("Test 5: Thread State Retrieval")
    
    try:
        response = requests.get(
            f"{BASE_URL}/threads/{thread_id}/state",
            timeout=5
        )
        
        if response.status_code != 200:
            print(f"❌ State retrieval failed: {response.status_code}")
            return False
        
        data = response.json()
        
        # Check state has required fields
        values = data.get("values", {})
        
        if not values:
            print("⚠️  No state values returned")
            return False
        
        # Show some state fields
        print(f"✅ State retrieved:")
        print(f"   • Messages: {len(values.get('messages', []))}")
        print(f"   • Current node: {values.get('current_node', 'N/A')}")
        print(f"   • Support type: {values.get('support_type', 'N/A')}")
        print(f"   • Auth verified: {values.get('auth_verified', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ State retrieval failed: {e}")
        return False


def test_conversation_flow():
    """Test a complete conversation flow"""
    print_test("Test 6: Complete Conversation Flow")
    
    try:
        # Create thread
        thread_id = test_create_thread()
        if not thread_id:
            return False
        
        time.sleep(0.5)
        
        # Start conversation
        result = test_send_message(thread_id, "Start")
        if not result:
            return False
        
        time.sleep(0.5)
        
        # Select service support
        result = test_send_message(thread_id, "2")
        if not result:
            return False
        
        time.sleep(0.5)
        
        # Select email
        result = test_send_message(thread_id, "1")
        if not result:
            return False
        
        time.sleep(0.5)
        
        # Check final state
        if not test_thread_state(thread_id):
            return False
        
        print("\n✅ Complete flow executed successfully")
        print(f"   Thread ID: {thread_id}")
        print(f"   Can resume conversation at any time!")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation flow test failed: {e}")
        return False


def main():
    """Run all Agent Protocol tests"""
    print("\n" + "="*70)
    print("🌐 SunBun Agent Protocol Compliance Tests")
    print("="*70)
    print("\n⚠️  Make sure Aegra server is running: aegra dev\n")
    
    # Give server time to start if just launched
    time.sleep(1)
    
    tests = [
        ("Server Health", test_server_health),
        ("Conversation Flow", test_conversation_flow)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
            time.sleep(0.5)  # Rate limiting
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for name, passed in results:
        icon = "✅" if passed else "❌"
        print(f"{icon} {name}")
    
    passed_count = sum(1 for _, p in results if p)
    total = len(results)
    
    print(f"\nPassed: {passed_count}/{total}")
    
    if passed_count == total:
        print("\n✅ ALL AGENT PROTOCOL TESTS PASSED!")
        print("Backend is ready for frontend integration")
        return 0
    else:
        print(f"\n❌ {total - passed_count} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = main()
    import sys
    sys.exit(exit_code)
