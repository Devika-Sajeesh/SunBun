from graph.orchestrator import get_graph_instance
import os

def test_routing_fix():
    print("🧪 Verifying Routing Fix...")
    graph = get_graph_instance()
    sid = "fix-verify-001"

    # Step 1: Start
    res1 = graph.process_message(sid, "hi")
    print(f"Turn 1 (hi) -> Node: {res1['current_node']}")
    
    # Step 2: Choose Sales
    res2 = graph.process_message(sid, "sales")
    print(f"Turn 2 (sales) -> Node: {res2['current_node']}")
    print(f"Assistant Message 2: {repr(res2['response'])}")

    # Step 3: Choose Phone (Input "2") 
    res3 = graph.process_message(sid, "2")
    print(f"Turn 3 ('2') -> Node: {res3['current_node']}")
    print(f"Assistant Message 3: {repr(res3['response'])}")
    
    if res3['current_node'] == "auth_collect_contact" and "mobile number" in res3['response'].lower():
        print("✅ SUCCESS: Routing kept us in auth_collect_contact!")
    else:
        print(f"❌ FAILED: Node was {res3['current_node']}")

if __name__ == "__main__":
    test_routing_fix()
