from typing import List, Literal, Optional, Dict, Any, Union
from typing_extensions import TypedDict

class State(TypedDict):
    session_id: str
    support_type: Literal["sales", "service", None]
    user_role: Literal["agent", "customer", "service_executive", "sales_executive", None]
    auth_verified: bool
    otp_attempts: int
    otp_code: Optional[str]
    contact: Dict[str, Any]  # keys: "email", "phone"
    customer_id: Optional[str]
    in_db: Optional[bool]
    customer_name: Optional[str]
    location: Optional[str]
    site_id: Optional[str]
    has_proposals: bool
    issue_flag: Optional[bool]
    issue_text: Optional[str]
    action_text: Optional[str]
    metrics: Optional[Dict[str, Any]]
    selected_issue: Optional[str]
    description: Optional[str]
    photos: List[str]
    ticket_id: Optional[str]
    nps_score: Optional[int]
    sales_profile: Optional[Dict[str, Any]]
    proposals: List[Dict[str, Any]]
    chosen_proposal_id: Optional[str]
    current_node: str
    awaiting_input: bool
    last_message: str
    conversation_history: List[Dict[str, Any]]

def initial_state() -> State:
    return {
        "session_id": "",
        "support_type": None,
        "user_role": None,
        "auth_verified": False,
        "otp_attempts": 0,
        "otp_code": None,
        "contact": {"email": None, "phone": None},
        "customer_id": None,
        "in_db": None,
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
        "sales_profile": None,
        "proposals": [],
        "chosen_proposal_id": None,
        "current_node": "",
        "awaiting_input": False,
        "last_message": "",
        "conversation_history": []
    }
