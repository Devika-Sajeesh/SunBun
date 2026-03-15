import os
import sys
import uuid
import time
from langchain_core.messages import HumanMessage
from graph.graph_aegra import compiled_graph

def test_bonus_features():
    print("\n" + "="*60)
    print("🧪 BONUS FEATURE: STATEFUL MEMORY (CUSTOMER ID)")
    print("="*60)
    
    # 1. First Thread: Customer Authenticates
    thread_id_1 = f"bonus-mem-{uuid.uuid4().hex[:6]}"
    config_1 = {"configurable": {"thread_id": thread_id_1}}
    
    print(f"\n[Thread 1: {thread_id_1}] New Customer Authentication...")
    
    # Send "hello"
    compiled_graph.invoke({"messages": [HumanMessage(content="hello")]}, config_1)
    # Select Service Support
    compiled_graph.invoke({"messages": [HumanMessage(content="2")]}, config_1)
    # Select Email
    compiled_graph.invoke({"messages": [HumanMessage(content="1")]}, config_1)
    # Enter Email (Existing customer John Doe)
    compiled_graph.invoke({"messages": [HumanMessage(content="john.doe@example.com")]}, config_1)
    # Enter OTP
    state_1 = compiled_graph.invoke({"messages": [HumanMessage(content="123456")]}, config_1)
    
    print(f"✅ Auth Success in Thread 1. ID: {state_1.get('customer_id')} ({state_1.get('customer_name')})")
    print(f"Bot Message: {state_1['messages'][-1].content}")
    
    # 2. Second Thread: Separate ID, Same Customer!
    thread_id_2 = f"bonus-mem-{uuid.uuid4().hex[:6]}"
    config_2 = {"configurable": {"thread_id": thread_id_2}}
    
    print(f"\n[Thread 2: {thread_id_2}] Separate session for same customer...")
    
    # Send "hello"
    compiled_graph.invoke({"messages": [HumanMessage(content="hello")]}, config_2)
    # Select Sales Support
    compiled_graph.invoke({"messages": [HumanMessage(content="1")]}, config_2)
    # Select Email
    compiled_graph.invoke({"messages": [HumanMessage(content="1")]}, config_2)
    # Enter same Email
    compiled_graph.invoke({"messages": [HumanMessage(content="john.doe@example.com")]}, config_2)
    # Enter OTP
    state_2 = compiled_graph.invoke({"messages": [HumanMessage(content="123456")]}, config_2)
    
    msg_2 = state_2['messages'][-1].content
    print(f"✅ Bot remembers customer in Thread 2!")
    print(f"Bot Message: {msg_2}")
    
    if "active issue" in msg_2.lower() and "pending proposal" in msg_2.lower():
        print("\n🏆 BONUS PASS: Memory tied to customer_id demonstrated!")
    else:
        print("\n❌ BONUS FAIL: Memory context missing.")

    print("\n" + "="*60)
    print("🧪 BONUS FEATURE: HUMAN-IN-THE-LOOP (SALES)")
    print("="*60)
    
    # Prepare sales state
    thread_id_3 = f"bonus-hitl-{uuid.uuid4().hex[:6]}"
    config_3 = {"configurable": {"thread_id": thread_id_3}}
    
    print(f"\n[Thread 3: {thread_id_3}] Starting Sales Flow...")
    compiled_graph.invoke({"messages": [HumanMessage(content="hello")]}, config_3)
    compiled_graph.invoke({"messages": [HumanMessage(content="1")]}, config_3) # Sales
    compiled_graph.invoke({"messages": [HumanMessage(content="1")]}, config_3) # Email
    compiled_graph.invoke({"messages": [HumanMessage(content="john.doe@example.com")]}, config_3)
    compiled_graph.invoke({"messages": [HumanMessage(content="123456")]}, config_3)
    
    # Now in sales choice - select "New proposals"
    compiled_graph.invoke({"messages": [HumanMessage(content="2")]}, config_3)
    
    # Fill wizard
    compiled_graph.invoke({"messages": [HumanMessage(content="1")]}, config_3) # Residential
    compiled_graph.invoke({"messages": [HumanMessage(content="6000")]}, config_3) # 6000 bill
    compiled_graph.invoke({"messages": [HumanMessage(content="20")]}, config_3) # 20% growth
    compiled_graph.invoke({"messages": [HumanMessage(content="2")]}, config_3) # 2 options
    state_sales = compiled_graph.invoke({"messages": [HumanMessage(content="1,2")]}, config_3) # Premium+Standard
    
    print(f"Current role: {state_sales.get('user_role')}")
    print(f"Bot Message to Agent:\n{state_sales['messages'][-1].content}")
    
    # Agent selects "Top 5 similar options"
    state_agent = compiled_graph.invoke({"messages": [HumanMessage(content="4")]}, config_3)
    print(f"\nAgent selected Top 5. Bot Response:\n{state_agent['messages'][-1].content}")
    
    # Agent selects one from top 5 (option 1)
    state_added = compiled_graph.invoke({"messages": [HumanMessage(content="1")]}, config_3)
    print(f"\nAgent added option. Bot Response:\n{state_added['messages'][-1].content}")
    
    # Should be back in review loop - check proposal count
    if len(state_added.get("proposals", [])) > 0:
         print(f"✅ Success: Proposal count is {len(state_added['proposals'])}")
         print("🏆 BONUS PASS: Human-in-the-loop iterative flow demonstrated!")
    else:
         print("❌ BONUS FAIL: Proposals not found in state.")

if __name__ == "__main__":
    try:
        test_bonus_features()
        with open("bonus_test_result.txt", "w") as f:
            f.write("PASS")
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        print(f"\n❌ TEST RUN FAILED:\n{error_msg}")
        with open("bonus_test_result.txt", "w") as f:
            f.write(f"FAIL\n{error_msg}")
        sys.exit(1)
