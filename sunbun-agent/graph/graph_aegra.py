"""
SunBun Main Graph Implementation for Aegra Platform
This file compiles the LangGraph workflow, including node wrapping for message support
and PostgreSQL persistence.
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import AIMessage, HumanMessage
import os

from graph.state_aegra import StateAegra, initial_state_aegra

# Import original nodes
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
from graph.nodes.sales_agent_review import (
    sales_agent_review_interrupt,
    sales_agent_decision,
    sales_add_notes,
    sales_select_from_top5
)


def create_button_message(text: str, options: list[dict]) -> AIMessage:
    """
    Create AI message with button metadata for UI rendering
    
    Args:
        text: Message text to display
        options: List of {"label": "Button Text", "value": "1"}
    
    Returns:
        AIMessage with button metadata
    """
    return AIMessage(
        content=text,
        additional_kwargs={
            "metadata": {
                "options": options
            }
        }
    )


def wrap_node_with_messages(node_func):
    """
    Wrapper to convert node outputs to message format.
    ALWAYS clears _user_input after reading to guarantee one-time consumption.
    """
    def wrapped(state: StateAegra) -> dict:
        node_name = node_func.__name__
        # Read input (set by dispatcher) 
        user_input = state.get("_user_input")
        
        print(f"DEBUG [{node_name}]: entering with user_input={user_input!r}, "
              f"current_node={state.get('current_node')}, "
              f"auth_step={state.get('auth_step')}")
        
        # Call original node
        updates = node_func(state, user_input)
        
        # Extract message text
        message_text = updates.get("last_message", "")
        
        # Parse buttons from text
        options = []
        for line in message_text.split("\n"):
            if "\u2192" in line:
                parts = line.strip().split("\u2192", 1)
                if len(parts) == 2:
                    options.append({"label": parts[1].strip(), "value": parts[0].strip()})
        
        # Add message to state only if there's actual content
        if message_text.strip() or options:
            if options:
                ai_msg = create_button_message(message_text, options)
            else:
                ai_msg = AIMessage(content=message_text)
            updates["messages"] = [ai_msg]
        
        if "last_message" in updates:
            del updates["last_message"]
        
        # ALWAYS clear _user_input after reading - guarantees one-time consumption
        updates["_user_input"] = None
        
        # Ensure current_node is always set
        if "current_node" not in updates:
            updates["current_node"] = state.get("current_node")

        print(f"DEBUG [{node_name}]: exiting -> current_node={updates.get('current_node')}, "
              f"awaiting_input={updates.get('awaiting_input')}")
        return updates
    
    return wrapped


def customer_lookup_router(state: StateAegra) -> dict:
    """Router after auth - decides sales vs service"""
    support_type = state.get("support_type")
    is_in_db = state.get("is_in_db", False)
    
    if support_type == "service":
        next_node = "service_status_check" if is_in_db else "service_unknown_customer"
    else:  # sales
        if is_in_db and state.get("has_proposals"):
            next_node = "sales_existing_router"
        else:
            next_node = "sales_info_capture"
    
    print(f"DEBUG [customer_lookup_router]: routing to {next_node}")
    return {
        "current_node": next_node,
        "awaiting_input": False
    }


def dispatcher(state: StateAegra) -> dict:
    """
    Dispatcher node: extracts the latest human message into _user_input.
    """
    updates = {"awaiting_input": False}
    
    messages = state.get("messages", [])
    if messages:
        last_msg = messages[-1]
        
        # Triple-redundant HumanMessage detection
        is_human = (
            isinstance(last_msg, HumanMessage) or
            (hasattr(last_msg, "type") and last_msg.type == "human") or
            (isinstance(last_msg, dict) and last_msg.get("type") == "human")
        )
        
        if is_human:
            content = getattr(last_msg, "content", "") if hasattr(last_msg, "content") else last_msg.get("content", "")
            updates["_user_input"] = content
        else:
            updates["_user_input"] = None  # No new human input this turn

    # Keep existing current_node; only set entry_node if completely unset
    current = state.get("current_node")
    if not current:
        updates["current_node"] = "entry_node"
        
    print(f"DEBUG [dispatcher]: current_node={current}, _user_input={updates.get('_user_input')!r}, "
          f"auth_step={state.get('auth_step')}, last_msg_type={type(messages[-1]).__name__ if messages else 'N/A'}")
    return updates


def route_with_input_check(state: StateAegra) -> str:
    """
    Universal router: respects awaiting_input to stop the graph.
    """
    if state.get("awaiting_input"):
        return END
    
    next_node = state.get("current_node", "entry_node")
    print(f"DEBUG: router routing to -> {next_node}")
    return next_node


# Build graph
workflow = StateGraph(StateAegra)

# Define nodes
workflow.add_node("dispatcher", dispatcher)
workflow.add_node("entry_node", wrap_node_with_messages(entry_node))
workflow.add_node("auth_collect_contact", wrap_node_with_messages(auth_collect_contact))
workflow.add_node("auth_verify_otp", wrap_node_with_messages(auth_verify_otp))
workflow.add_node("auth_not_found_handler", wrap_node_with_messages(auth_not_found_handler))
workflow.add_node("auth_failed", wrap_node_with_messages(auth_failed))
workflow.add_node("customer_lookup_result", customer_lookup_router)

# Service nodes
workflow.add_node("service_status_check", wrap_node_with_messages(service_status_check))
workflow.add_node("service_resolution_router", wrap_node_with_messages(service_resolution_router))
workflow.add_node("service_happy_close", wrap_node_with_messages(service_happy_close))
workflow.add_node("service_nps_collect", wrap_node_with_messages(service_nps_collect))
workflow.add_node("service_nps_feedback", wrap_node_with_messages(service_nps_feedback))
workflow.add_node("service_issue_capture", wrap_node_with_messages(service_issue_capture))
workflow.add_node("service_unknown_customer", wrap_node_with_messages(service_unknown_customer))

# Sales nodes
workflow.add_node("sales_existing_router", wrap_node_with_messages(sales_existing_router))
workflow.add_node("sales_proposal_choice", wrap_node_with_messages(sales_proposal_choice))
workflow.add_node("sales_review_proposals", wrap_node_with_messages(sales_review_proposals))
workflow.add_node("sales_info_capture", wrap_node_with_messages(sales_info_capture))
workflow.add_node("sales_proposal_generate", wrap_node_with_messages(sales_proposal_generate))
workflow.add_node("sales_agent_review_interrupt", wrap_node_with_messages(sales_agent_review_interrupt))
workflow.add_node("sales_agent_decision", wrap_node_with_messages(sales_agent_decision))
workflow.add_node("sales_add_notes", wrap_node_with_messages(sales_add_notes))
workflow.add_node("sales_select_from_top5", wrap_node_with_messages(sales_select_from_top5))
workflow.add_node("sales_proposal_select", wrap_node_with_messages(sales_proposal_select))
workflow.add_node("sales_proposal_confirm", wrap_node_with_messages(sales_proposal_confirm))
workflow.add_node("sales_handoff", wrap_node_with_messages(sales_handoff))

# Set entry point to dispatcher
workflow.set_entry_point("dispatcher")

# Conditional edges using the new router
workflow.add_conditional_edges("dispatcher", route_with_input_check)
workflow.add_conditional_edges("entry_node", route_with_input_check)
workflow.add_conditional_edges("auth_collect_contact", route_with_input_check)
workflow.add_conditional_edges("auth_verify_otp", route_with_input_check)
workflow.add_conditional_edges("auth_not_found_handler", route_with_input_check)
workflow.add_conditional_edges("auth_failed", lambda s: END if s["current_node"] == "end" else route_with_input_check(s))

workflow.add_conditional_edges(
    "customer_lookup_result",
    route_with_input_check,
    {
        "service_status_check": "service_status_check",
        "service_unknown_customer": "service_unknown_customer",
        "sales_existing_router": "sales_existing_router",
        "sales_info_capture": "sales_info_capture",
        END: END
    }
)

# Service edges
workflow.add_conditional_edges("service_status_check", route_with_input_check)
workflow.add_conditional_edges("service_resolution_router", route_with_input_check)
workflow.add_conditional_edges("service_happy_close", route_with_input_check)
workflow.add_conditional_edges("service_nps_collect", route_with_input_check)
workflow.add_conditional_edges("service_nps_feedback", lambda s: END if s["current_node"] == "end" else route_with_input_check(s))
workflow.add_conditional_edges("service_issue_capture", lambda s: END if s["current_node"] == "end" else route_with_input_check(s))
workflow.add_conditional_edges("service_unknown_customer", route_with_input_check)

# Sales edges
workflow.add_conditional_edges("sales_existing_router", route_with_input_check)
workflow.add_conditional_edges("sales_proposal_choice", route_with_input_check)
workflow.add_conditional_edges("sales_review_proposals", route_with_input_check)
workflow.add_conditional_edges("sales_info_capture", route_with_input_check)
workflow.add_edge("sales_proposal_generate", "sales_agent_review_interrupt")
workflow.add_conditional_edges("sales_agent_review_interrupt", route_with_input_check)
workflow.add_conditional_edges("sales_agent_decision", route_with_input_check)
workflow.add_conditional_edges("sales_add_notes", route_with_input_check)
workflow.add_conditional_edges("sales_select_from_top5", route_with_input_check)
workflow.add_conditional_edges("sales_proposal_select", route_with_input_check)
workflow.add_conditional_edges("sales_proposal_confirm", lambda s: END if s["current_node"] == "end" else route_with_input_check(s))
workflow.add_conditional_edges("sales_handoff", lambda s: END if s["current_node"] == "end" else route_with_input_check(s))

# Compile with PostgreSQL checkpointer
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://sunbun_agent:sunbun_secret_2025@localhost:5433/sunbun_week2")

# Setup connection pool
from psycopg_pool import ConnectionPool
pool = ConnectionPool(conninfo=DATABASE_URL)

checkpointer = PostgresSaver(pool)
checkpointer.setup()

compiled_graph = workflow.compile(checkpointer=checkpointer)

print("SunBun Aegra graph compiled successfully!")
