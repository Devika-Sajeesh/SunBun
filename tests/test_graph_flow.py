from graph.orchestrator import get_graph_instance
import json

def run_test():
    graph = get_graph_instance()
    session_id = "test-session-999"
    
    steps = [
        (None, "Initial Start"),
        ("2", "Select Service Support"),
        ("1", "Select Email Method"),
        ("john.doe@example.com", "Enter Email"),
        ("123456", "Enter OTP (Mocked/Simulated)")
    ]
    
    for user_input, action in steps:
        print(f"\n--- ACTION: {action} (Input: {user_input}) ---")
        result = graph.process_message(session_id, user_input)
        print(f"Assistant: {result['response']}")
        
        state = graph.get_session_state(session_id)
        print(f"DEBUG - Current Node: {state.get('current_node')}")
        print(f"DEBUG - In DB: {state.get('in_db')}")
        print(f"DEBUG - Customer Name: {state.get('customer_name')}")

if __name__ == "__main__":
    run_test()
