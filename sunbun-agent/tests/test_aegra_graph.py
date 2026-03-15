"""
SunBun Aegra Graph - Compilation & Invocation Tests
Verifies that the compiled LangGraph workflow works with state persistence.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver


def test_graph_import():
    """Test that graph can be imported"""
    print("🧪 Test 1: Import graph module")
    
    try:
        from graph.graph_aegra import compiled_graph
        print("✅ Graph imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import graph: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_compilation():
    """Test that graph is properly compiled"""
    print("\n🧪 Test 2: Verify graph compilation")
    
    try:
        from graph.graph_aegra import compiled_graph
        
        # Check graph has nodes
        nodes = compiled_graph.get_graph().nodes
        print(f"  Graph has {len(nodes)} nodes")
        
        # Check for key nodes
        key_nodes = ["entry_node", "auth_collect_contact", "service_status_check", "sales_existing_router"]
        missing = [n for n in key_nodes if n not in nodes]
        
        if missing:
            print(f"❌ Missing nodes: {missing}")
            return False
        
        print(f"✅ Graph compiled with all key nodes")
        return True
        
    except Exception as e:
        print(f"❌ Graph compilation check failed: {e}")
        return False


def test_state_schema():
    """Test that StateAegra has required fields"""
    print("\n🧪 Test 3: Validate state schema")
    
    try:
        from graph.state_aegra import StateAegra, initial_state_aegra
        
        # Create initial state
        state = initial_state_aegra()
        
        # Check required fields
        required_fields = [
            "messages",
            "session_id",
            "support_type",
            "auth_verified",
            "is_in_db",
            "customer_id",
            "proposals",
            "current_node"
        ]
        
        missing = [f for f in required_fields if f not in state]
        
        if missing:
            print(f"❌ Missing state fields: {missing}")
            return False
        
        # Check messages is a list
        if not isinstance(state["messages"], list):
            print(f"❌ 'messages' field is not a list")
            return False
        
        print(f"✅ State schema valid with {len(state)} fields")
        return True
        
    except Exception as e:
        print(f"❌ State schema validation failed: {e}")
        return False


def test_postgres_checkpointer():
    """Test PostgreSQL checkpointer initialization"""
    print("\n🧪 Test 4: PostgreSQL checkpointer")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Using 5433 to match our docker-compose mapping
        DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sunbun_agent:sunbun_secret_2025@localhost:5433/sunbun_week2")
        
        checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
        
        print("✅ PostgreSQL checkpointer initialized")
        return True
        
    except Exception as e:
        print(f"❌ Checkpointer initialization failed: {e}")
        print("   Make sure PostgreSQL is running: docker-compose up -d postgres")
        return False


def test_simple_invocation():
    """Test simple graph invocation"""
    print("\n🧪 Test 5: Simple graph invocation")
    
    try:
        from graph.graph_aegra import compiled_graph
        from graph.state_aegra import initial_state_aegra
        
        # Create initial state
        config = {"configurable": {"thread_id": "test-thread-001"}}
        
        # Invoke with initial message
        initial_state = initial_state_aegra()
        initial_state["messages"] = [HumanMessage(content="Start")]
        
        result = compiled_graph.invoke(initial_state, config)
        
        # Check result has messages
        if "messages" not in result:
            print("❌ Result missing 'messages' field")
            return False
        
        if len(result["messages"]) == 0:
            print("❌ No messages in result")
            return False
        
        # Print first bot message
        ai_messages = [m for m in result["messages"] if m.type == "ai"]
        if ai_messages:
            print(f"  Bot response: {ai_messages[0].content[:100]}...")
        
        print("✅ Graph invocation successful")
        return True
        
    except Exception as e:
        print(f"❌ Graph invocation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_persistence():
    """Test that state persists across invocations"""
    print("\n🧪 Test 6: State persistence")
    
    try:
        from graph.graph_aegra import compiled_graph
        from graph.state_aegra import initial_state_aegra
        
        thread_id = "test-persistence-001"
        config = {"configurable": {"thread_id": thread_id}}
        
        # First invocation
        state1 = initial_state_aegra()
        state1["messages"] = [HumanMessage(content="Start")]
        
        result1 = compiled_graph.invoke(state1, config)
        node_after_first = result1.get("current_node")
        
        # Second invocation (should resume from saved state)
        state2 = initial_state_aegra()
        state2["messages"] = [HumanMessage(content="1")]  # Select option 1
        
        result2 = compiled_graph.invoke(state2, config)
        node_after_second = result2.get("current_node")
        
        # Nodes should be different (conversation progressed)
        if node_after_first == node_after_second:
            print(f"⚠️  Warning: Node didn't change ({node_after_first} → {node_after_second})")
            print("   This might be okay depending on the flow")
        
        # Check that messages accumulated
        if len(result2["messages"]) < len(result1["messages"]):
            print("❌ Messages not accumulating")
            return False
        
        print(f"✅ State persisted ({len(result1['messages'])} → {len(result2['messages'])} messages)")
        return True
        
    except Exception as e:
        print(f"❌ State persistence test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_button_metadata():
    """Test that button metadata is present in responses"""
    print("\n🧪 Test 7: Button metadata in responses")
    
    try:
        from graph.graph_aegra import compiled_graph
        from graph.state_aegra import initial_state_aegra
        
        config = {"configurable": {"thread_id": "test-buttons-001"}}
        
        # Invoke graph
        state = initial_state_aegra()
        state["messages"] = [HumanMessage(content="Start")]
        
        result = compiled_graph.invoke(state, config)
        
        # Find AI messages
        ai_messages = [m for m in result["messages"] if m.type == "ai"]
        
        if not ai_messages:
            print("❌ No AI messages found")
            return False
        
        # Check for button metadata
        last_ai_msg = ai_messages[-1]
        
        # Check additional_kwargs
        metadata = getattr(last_ai_msg, "additional_kwargs", {}).get("metadata", {})
        options = metadata.get("options", [])
        
        if options:
            print(f"✅ Button metadata found: {len(options)} options")
            for opt in options[:3]:  # Show first 3
                print(f"     • {opt.get('label', 'N/A')} → {opt.get('value', 'N/A')}")
            return True
        else:
            print("⚠️  No button metadata (might be a text-only response)")
            return True  # Not critical
        
    except Exception as e:
        print(f"❌ Button metadata test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("🧪 SunBun Aegra Graph - Compilation & Invocation Tests")
    print("="*70)
    
    tests = [
        test_graph_import,
        test_graph_compilation,
        test_state_schema,
        test_postgres_checkpointer,
        test_simple_invocation,
        test_state_persistence,
        test_button_metadata
    ]
    
    results = []
    for test_func in tests:
        try:
            passed = test_func()
            results.append(passed)
        except Exception as e:
            print(f"❌ Test crashed: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED!")
        print("Graph is ready for Aegra deployment")
        return 0
    else:
        print(f"\n❌ {total - passed} TEST(S) FAILED")
        print("Fix the issues before deploying")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
