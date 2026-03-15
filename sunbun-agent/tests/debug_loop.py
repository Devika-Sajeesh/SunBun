
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from graph.graph_aegra import compiled_graph
from langchain_core.messages import HumanMessage, AIMessage

def debug_flow():
    import uuid
    thread_id = f"debug_{uuid.uuid4().hex[:8]}"
    config = {"configurable": {"thread_id": thread_id}}
    print(f"Using fresh thread: {thread_id}")
    
    steps = [
        ("Step 1: Initial Greeting", "hello"),
        ("Step 2: Select Service Support", "2"),
        ("Step 3: Select Use Phone", "2"),
    ]
    
    for label, text in steps:
        print(f"\n{'='*60}")
        print(f"--- {label} (sending: {text!r}) ---")
        print(f"{'='*60}")
        inputs = {"messages": [HumanMessage(content=text)]}
        for event in compiled_graph.stream(inputs, config, stream_mode="updates"):
            for node_name, updates in event.items():
                print(f"\n  [Node: {node_name}]")
                if "messages" in updates:
                    last_msg = updates["messages"][-1]
                    content = last_msg.content.encode('ascii', 'ignore').decode('ascii')
                    print(f"  Bot: {content[:120]}")
                if "current_node" in updates:
                    print(f"  current_node: {updates['current_node']}")
                if "awaiting_input" in updates:
                    print(f"  awaiting_input: {updates['awaiting_input']}")
                if "auth_step" in updates:
                    print(f"  auth_step: {updates['auth_step']}")
        
        # Print state snapshot
        state = compiled_graph.get_state(config)
        sv = state.values
        print(f"\n  --- STATE SNAPSHOT ---")
        print(f"  current_node: {sv.get('current_node')}")
        print(f"  auth_step: {sv.get('auth_step')}")
        print(f"  _user_input: {sv.get('_user_input')}")
        print(f"  support_type: {sv.get('support_type')}")
        print(f"  awaiting_input: {sv.get('awaiting_input')}")
        print(f"  messages count: {len(sv.get('messages', []))}")

if __name__ == "__main__":
    debug_flow()
