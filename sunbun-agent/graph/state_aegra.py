"""
SunBun State Definition for Aegra Platform
This file defines the TypedDict state used by the LangGraph workflow.
"""

from typing import Annotated, TypedDict, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import AnyMessage

class StateAegra(TypedDict):
    """State with LangGraph message support"""
    
    # Standard message history (REQUIRED for Aegra)
    messages: Annotated[list[AnyMessage], add_messages]
    
    # Session & routing
    session_id: str
    support_type: Literal["sales", "service", None]
    user_role: Literal["agent", "customer", "service_executive", "sales_executive", None]
    
    # Authentication
    auth_verified: bool
    auth_step: str | None
    otp_attempts: int
    otp_code: str | None
    contact: dict
    
    # Customer data
    customer_id: int | None
    is_in_db: bool | None
    customer_name: str | None
    location: str | None
    site_id: int | None
    has_proposals: bool
    
    # Service flow
    issue_flag: bool | None
    issue_text: str | None
    action_text: str | None
    metrics: dict | None
    selected_issue: str | None
    description: str | None
    photos: list[str]
    ticket_id: str | None
    nps_score: int | None
    service_step: str | None
    system_info: dict | None
    unknown_step: str | None
    available_agent: dict | None
    
    # Sales flow
    sales_profile: dict | None
    sales_step: str | None
    proposals: list[dict]
    chosen_proposal_id: str | None
    chosen_proposal: dict | None
    opportunity_id: str | None
    
    # Node tracking
    current_node: str
    awaiting_input: bool
    
    # Internal (for node communication)
    _user_input: str | None

def initial_state_aegra() -> StateAegra:
    """Factory for initial state"""
    return {
        "messages": [],
        "session_id": "",
        "support_type": None,
        "user_role": "customer",
        "auth_verified": False,
        "auth_step": None,
        "otp_attempts": 0,
        "otp_code": None,
        "contact": {"email": None, "phone": None},
        "customer_id": None,
        "is_in_db": None,
        "customer_name": None,
        "location": None,
        "site_id": None,
        "has_proposals": False,
        "issue_flag": None,
        "issue_text": None,
        "action_text": None,
        "metrics": None,
        "selected_issue": None,
        "description": None,
        "photos": [],
        "ticket_id": None,
        "nps_score": None,
        "service_step": None,
        "system_info": None,
        "unknown_step": None,
        "available_agent": None,
        "sales_profile": None,
        "sales_step": None,
        "proposals": [],
        "chosen_proposal_id": None,
        "chosen_proposal": None,
        "opportunity_id": None,
        "current_node": "entry_node",
        "awaiting_input": False,
        "_user_input": None
    }
