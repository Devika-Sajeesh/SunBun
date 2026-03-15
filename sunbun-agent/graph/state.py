from typing import List, Literal, Optional, Dict, Any, Union, TypedDict

class State(TypedDict):
    session_id: str
    support_type: Literal["sales", "service", None]
    user_role: Literal["agent", "customer", "service_executive", "sales_executive", None]
    auth_verified: bool
    otp_attempts: int
    otp_code: Optional[str]
    contact: Dict[str, Any]  # keys: "email", "phone"
    customer_id: Optional[str]
    is_in_db: bool
    customer_name: str
    location: str
    site_id: str
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
    auth_step: Optional[str]
    service_step: Optional[str]
    unknown_step: Optional[str]
    system_info: Optional[Dict[str, Any]]
    available_agent: Optional[Dict[str, Any]]
    nps_feedback: Optional[str]
    sales_step: Optional[str]
    chosen_proposal: Optional[Dict[str, Any]]
    opportunity_id: Optional[str]
    _user_input: Optional[str]

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
        "is_in_db": False,
        "customer_name": "",
        "location": "",
        "site_id": "",
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
        "current_node": "entry_node",
        "awaiting_input": False,
        "last_message": "",
        "conversation_history": [],
        "auth_step": None,
        "service_step": None,
        "unknown_step": None,
        "system_info": None,
        "available_agent": None,
        "nps_feedback": None,
        "sales_step": None,
        "chosen_proposal": None,
        "opportunity_id": None,
        "_user_input": None
    }
