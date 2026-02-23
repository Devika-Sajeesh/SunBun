from typing import TypedDict, Literal, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.graph import StateGraph, END
from graph.state import State, initial_state
from graph.nodes.auth_nodes import (
    entry_node,
    auth_collect_contact,
    auth_verify_otp,
    auth_not_found_handler,
    auth_failed
)
from graph.nodes.service_nodes import (
    service_status_check,
    service_resolution_router,
    service_happy_close,
    service_nps_collect,
    service_nps_feedback,
    service_issue_capture,
    service_unknown_customer
)
from graph.nodes.sales_nodes import (
    sales_existing_router,
    sales_proposal_choice,
    sales_review_proposals,
    sales_info_capture,
    sales_proposal_generate,
    sales_proposal_select,
    sales_proposal_confirm,
    sales_handoff
)


class SunBunGraph:
    """LangGraph orchestrator for SunBun assistant"""
    
    def __init__(self):
        self.graph = self._build_graph()
        self.sessions = {}  # session_id -> state dict
    
    def _build_graph(self):
        """Build and compile the state graph"""
        
        # Create graph
        workflow = StateGraph(State)
        
        # Add all nodes
        workflow.add_node("entry_node", self._wrap_node(entry_node))
        workflow.add_node("auth_collect_contact", self._wrap_node(auth_collect_contact))
        workflow.add_node("auth_verify_otp", self._wrap_node(auth_verify_otp))
        workflow.add_node("auth_not_found_handler", self._wrap_node(auth_not_found_handler))
        workflow.add_node("auth_failed", self._wrap_node(auth_failed))
        workflow.add_node("customer_lookup_result", self._customer_lookup_router)
        
        # Service nodes
        workflow.add_node("service_status_check", self._wrap_node(service_status_check))
        workflow.add_node("service_resolution_router", self._wrap_node(service_resolution_router))
        workflow.add_node("service_happy_close", self._wrap_node(service_happy_close))
        workflow.add_node("service_nps_collect", self._wrap_node(service_nps_collect))
        workflow.add_node("service_nps_feedback", self._wrap_node(service_nps_feedback))
        workflow.add_node("service_issue_capture", self._wrap_node(service_issue_capture))
        workflow.add_node("service_unknown_customer", self._wrap_node(service_unknown_customer))
        
        # Sales nodes
        workflow.add_node("sales_existing_router", self._wrap_node(sales_existing_router))
        workflow.add_node("sales_proposal_choice", self._wrap_node(sales_proposal_choice))
        workflow.add_node("sales_review_proposals", self._wrap_node(sales_review_proposals))
        workflow.add_node("sales_info_capture", self._wrap_node(sales_info_capture))
        workflow.add_node("sales_proposal_generate", self._wrap_node(sales_proposal_generate))
        workflow.add_node("sales_proposal_select", self._wrap_node(sales_proposal_select))
        workflow.add_node("sales_proposal_confirm", self._wrap_node(sales_proposal_confirm))
        workflow.add_node("sales_handoff", self._wrap_node(sales_handoff))
        
        # Set entry point
        workflow.set_entry_point("entry_node")
        
        # Wire edges
        
        # Auth flow
        workflow.add_conditional_edges(
            "entry_node",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "auth_collect_contact",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "auth_verify_otp",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "auth_not_found_handler",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "auth_failed",
            lambda s: s["current_node"]
        )
        
        # Customer lookup router - branches to sales or service
        workflow.add_conditional_edges(
            "customer_lookup_result",
            self._route_after_lookup,
            {
                "service_status_check": "service_status_check",
                "service_unknown_customer": "service_unknown_customer",
                "sales_existing_router": "sales_existing_router",
                "sales_info_capture": "sales_info_capture"
            }
        )
        
        # Service flow
        workflow.add_conditional_edges(
            "service_status_check",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "service_resolution_router",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "service_happy_close",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "service_nps_collect",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "service_nps_feedback",
            lambda s: s["current_node"] if s["current_node"] != "end" else END
        )
        
        workflow.add_conditional_edges(
            "service_issue_capture",
            lambda s: s["current_node"] if s["current_node"] != "end" else END
        )
        
        workflow.add_conditional_edges(
            "service_unknown_customer",
            lambda s: s["current_node"]
        )
        
        # Sales flow
        workflow.add_conditional_edges(
            "sales_existing_router",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "sales_proposal_choice",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "sales_review_proposals",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "sales_info_capture",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "sales_proposal_generate",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "sales_proposal_select",
            lambda s: s["current_node"]
        )
        
        workflow.add_conditional_edges(
            "sales_proposal_confirm",
            lambda s: s["current_node"] if s["current_node"] != "end" else END
        )
        
        workflow.add_conditional_edges(
            "sales_handoff",
            lambda s: s["current_node"] if s["current_node"] != "end" else END
        )
        
        return workflow.compile()
    
    def _wrap_node(self, node_func):
        """Wrapper to handle node function calls"""
        def wrapped(state: dict) -> dict:
            # Get user input from state
            user_input = state.get("_user_input")
            
            # Call node function
            updates = node_func(state, user_input)
            
            # Clear user input after processing
            updates["_user_input"] = None
            
            return updates
        
        return wrapped
    
    def _customer_lookup_router(self, state: dict) -> dict:
        """Router node after authentication - decides sales vs service"""
        support_type = state.get("support_type")
        in_db = state.get("in_db", False)
        
        # Determine next node
        if support_type == "service":
            if in_db:
                next_node = "service_status_check"
            else:
                next_node = "service_unknown_customer"
        else:  # sales
            if in_db and state.get("has_proposals"):
                next_node = "sales_existing_router"
            else:
                next_node = "sales_info_capture"
        
        return {
            "current_node": next_node,
            "awaiting_input": False
        }
    
    def _route_after_lookup(self, state: dict) -> str:
        """Edge function for customer_lookup_result"""
        return state.get("current_node", "entry_node")
    
    def get_or_create_session(self, session_id: str) -> dict:
        """Get existing session or create new one"""
        if session_id not in self.sessions:
            self.sessions[session_id] = initial_state()
            self.sessions[session_id]["session_id"] = session_id
        return self.sessions[session_id]
    
    def process_message(self, session_id: str, user_input: str) -> dict:
        """
        Process a user message and return assistant response
        
        Args:
            session_id: Unique session identifier
            user_input: User's message text
            
        Returns:
            dict with keys: response (str), is_complete (bool), current_node (str)
        """
        # Get or create session state
        state = self.get_or_create_session(session_id)
        
        # Add user input to state
        state["_user_input"] = user_input
        
        # Determine starting node
        current_node = state.get("current_node", "entry_node")
        
        try:
            # Invoke the graph from current node
            if current_node == "end":
                # Conversation ended, restart
                state = initial_state()
                state["session_id"] = session_id
                self.sessions[session_id] = state
                state["_user_input"] = user_input
                current_node = "entry_node"
            
            # Run one step of the graph
            result = self.graph.invoke(state, {"recursion_limit": 50})
            
            # Update session state
            self.sessions[session_id] = result
            
            # Extract response
            response = result.get("last_message", "I'm sorry, something went wrong.")
            is_complete = result.get("current_node") == "end"
            current_node = result.get("current_node", "entry_node")
            
            return {
                "response": response,
                "is_complete": is_complete,
                "current_node": current_node,
                "awaiting_input": result.get("awaiting_input", True)
            }
            
        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            return {
                "response": f"I encountered an error: {str(e)}. Let's start over. How can I help you today?",
                "is_complete": False,
                "current_node": "entry_node",
                "awaiting_input": True
            }
    
    def reset_session(self, session_id: str):
        """Reset a session to initial state"""
        if session_id in self.sessions:
            del self.sessions[session_id]
    
    def get_session_state(self, session_id: str) -> dict:
        """Get current state for debugging"""
        return self.sessions.get(session_id, {})
    
    def export_graph_diagram(self) -> str:
        """Export mermaid diagram of the graph"""
        try:
            return self.graph.get_graph().draw_mermaid()
        except Exception as e:
            return f"Could not generate diagram: {e}"


# Singleton instance
_instance = None

def get_graph_instance() -> SunBunGraph:
    """Get or create singleton graph instance"""
    global _instance
    if _instance is None:
        print("🌞 Initializing SunBun Graph...")
        _instance = SunBunGraph()
        print("✅ Graph initialized successfully!")
    return _instance


# For testing
if __name__ == "__main__":
    graph = get_graph_instance()
    
    # Print mermaid diagram
    print("\n📊 Graph Structure:")
    # print(graph.export_graph_diagram())
    
    # Test conversation flow
    print("\n🧪 Testing conversation flow:")
    session_id = "test-001"
    
    # Start conversation
    result = graph.process_message(session_id, None)
    print(f"\nAssistant: {result['response']}")
    
    # User selects service
    result = graph.process_message(session_id, "2")
    print(f"\nAssistant: {result['response']}")
    
    # User selects email
    result = graph.process_message(session_id, "1")
    print(f"\nAssistant: {result['response']}")
    
    # User enters email
    result = graph.process_message(session_id, "john.doe@example.com")
    print(f"\nAssistant: {result['response']}")
    
    # Check state
    state = graph.get_session_state(session_id)
    print(f"\n📋 Session state:")
    print(f"  Current node: {state.get('current_node')}")
    print(f"  Support type: {state.get('support_type')}")
    print(f"  Customer: {state.get('customer_name')}")
