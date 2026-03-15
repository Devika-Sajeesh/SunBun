"""
Authentication and Entry Nodes
Handles user welcome and identity verification (OTP) via Email/Phone.
"""

from typing import Dict, Any, Optional, Literal
from graph.state import State
from services.data_service import get_instance
import logging

logger = logging.getLogger(__name__)

def entry_node(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Entry point for the assistant.
    Determines if the user needs Sales or Service support.
    """
    if user_input is None:
        return {
            "last_message": "👋 Welcome to SunBun Solar!\n\nHow can we help you today?\n\nReply:\n  1 → Sales Support – I'm interested in buying/upgrading\n  2 → Service Support – I need help with an existing system",
            "current_node": "entry_node",
            "awaiting_input": True
        }
    
    normalized_input = user_input.lower().strip()
    
    # Handle greetings or "start"
    if normalized_input in ["hi", "hello", "start", "hey"]:
        return {
            "last_message": "👋 Welcome to SunBun Solar!\n\nHow can we help you today?\n\nReply:\n  1 → Sales Support – I'm interested in buying/upgrading\n  2 → Service Support – I need help with an existing system",
            "current_node": "entry_node",
            "awaiting_input": True
        }
    
    if normalized_input == "1" or "sales" in normalized_input:
        return {
            "support_type": "sales",
            "current_node": "auth_collect_contact",
            "awaiting_input": False
        }
    
    elif normalized_input == "2" or "service" in normalized_input:
        return {
            "support_type": "service",
            "current_node": "auth_collect_contact",
            "awaiting_input": False
        }
    
    else:
        return {
            "last_message": "I didn't catch that. Please choose an option:\n  1 → Sales Support\n  2 → Service Support",
            "current_node": "entry_node",
            "awaiting_input": True
        }

def auth_collect_contact(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Collects contact method (email/phone) and the identifier itself.
    Triggers simulated OTP.
    """
    auth_step = state.get("auth_step")
    
    # STEP 1: Choose method (email or phone)
    if auth_step is None or auth_step == "choose_method":
        if user_input is None:
            # First time or after reset - show options
            support_type = state.get("support_type", "sales")
            prefix = "Great! Let's get you set up with Sales Support. 📊" if support_type == "sales" else "Got it! Let's connect you with Service Support. 🔧"
            return {
                "auth_step": "choose_method",
                "last_message": f"{prefix}\n\nPlease choose how to verify your identity:\n  1 → Use Email\n  2 → Use Phone",
                "current_node": "auth_collect_contact",
                "awaiting_input": True
            }
        
        # User selected method
        normalized_input = user_input.lower().strip() if user_input else ""
        if normalized_input == "1" or "email" in normalized_input:
            return {
                "contact": {"email": None, "phone": None, "method": "email"},
                "auth_step": "enter_identifier",
                "last_message": "Please enter your email address:",
                "current_node": "auth_collect_contact",
                "awaiting_input": True
            }
        elif normalized_input == "2" or "phone" in normalized_input:
            return {
                "contact": {"email": None, "phone": None, "method": "phone"},
                "auth_step": "enter_identifier",
                "last_message": "Please enter your mobile number (e.g., 555-0101):",
                "current_node": "auth_collect_contact",
                "awaiting_input": True
            }
        else:
            # Invalid choice
            return {
                "last_message": "Invalid choice. Please reply:\n  1 → Use Email\n  2 → Use Phone",
                "current_node": "auth_collect_contact",
                "awaiting_input": True
            }

    # STEP 2: Enter identifier
    elif auth_step == "enter_identifier":
        method = state.get("contact", {}).get("method")
        data_service = get_instance()
        
        if method == "email":
            otp = data_service.simulate_otp(user_input, "email")
            return {
                "contact": {"email": user_input, "phone": None, "method": "email"},
                "otp_code": otp,
                "last_message": f"📧 We've sent a 6-digit code to {user_input}.\n\n(Check console for simulated OTP: {otp})\n\nEnter the 6-digit code:",
                "current_node": "auth_verify_otp",
                "awaiting_input": True
            }
        
        elif method == "phone":
            otp = data_service.simulate_otp(user_input, "phone")
            return {
                "contact": {"email": None, "phone": user_input, "method": "phone"},
                "otp_code": otp,
                "last_message": f"📱 We've sent a 6-digit code to {user_input}.\n\n(Check console for simulated OTP: {otp})\n\nEnter the 6-digit code:",
                "current_node": "auth_verify_otp",
                "awaiting_input": True
            }
            
    return {"current_node": "auth_collect_contact", "awaiting_input": True}


def auth_verify_otp(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    if user_input is None:
        # Re-prompt
        return {
             "last_message": "Please enter the 6-digit code:",
             "current_node": "auth_verify_otp",
             "awaiting_input": True
        }

    identifier = state["contact"].get("email") or state["contact"].get("phone")
    channel = "email" if state["contact"].get("email") else "phone"
    
    data_service = get_instance()
    is_valid = data_service.verify_otp(identifier, channel, user_input.strip())
    
    if is_valid:
        customer = data_service.lookup_customer(identifier)
        
        if customer:
            print(f"DEBUG AUTH: Found customer {customer['name']}, setting is_in_db=True")
            
            # BONUS: Stateful memory implementation
            # Fetch recent activity to show we "remember" them across sessions
            recent_proposals = data_service.get_proposals(int(customer["customer_id"]))
            recent_issues = data_service.get_site_issues(int(customer["site_id"]))
            
            memory_context = ""
            if recent_issues:
                memory_context += f"\n⚠️ I see an active issue: {recent_issues[0]['issue_text']}"
            if recent_proposals:
                memory_context += f"\n📝 I also found {len(recent_proposals)} pending proposal(s) for you."
            
            welcome_msg = f"✅ Identity verified!\n\nWelcome back, {customer['name']}!{memory_context}"
            
            return {
                "auth_verified": True,
                "is_in_db": True,
                "customer_id": int(customer["customer_id"]),
                "customer_name": customer["name"],
                "location": customer["location"],
                "site_id": int(customer["site_id"]),
                "has_proposals": bool(customer["has_proposals"]),
                "last_message": welcome_msg,
                "current_node": "customer_lookup_result",
                "awaiting_input": False
            }
        else:
            return {
                "auth_verified": True,
                "is_in_db": False,
                "last_message": f"✅ Identity verified!\n\nWe couldn't find an existing SunBun system under {identifier}.\n\nWould you like to:\n  1 → Try a different email/phone\n  2 → Continue anyway",
                "current_node": "auth_not_found_handler",
                "awaiting_input": True
            }
            
    else:
        # Incorrect OTP
        attempts = state.get("otp_attempts", 0) + 1
        
        if attempts >= 3:
            return {
                "otp_attempts": attempts,
                "last_message": "❌ We couldn't verify your identity after 3 attempts.\n\nReply:\n  1 → Retry authentication\n  2 → Exit",
                "current_node": "auth_failed",
                "awaiting_input": True
            }
        else:
            return {
                "otp_attempts": attempts,
                "last_message": f"❌ That code doesn't look right. {3 - attempts} attempt(s) remaining.\n\nPlease try again:",
                "current_node": "auth_verify_otp",
                "awaiting_input": True
            }

def auth_not_found_handler(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    normalized_input = user_input.strip() if user_input else ""
    
    if normalized_input == "1":
        return {
            "auth_step": None,
            "otp_attempts": 0,
            "otp_code": None,
            "contact": {"email": None, "phone": None},
            "last_message": "No problem! Let's try again.\n\nPlease choose:\n  1 → Use Email\n  2 → Use Phone",
            "current_node": "auth_collect_contact",
            "awaiting_input": True
        }
    
    elif normalized_input == "2":
        return {
            "is_in_db": False,
            "last_message": "Got it! We'll help you anyway.",
            "current_node": "customer_lookup_result",
            "awaiting_input": False
        }
        
    else:
        return {
            "last_message": "Please choose an option:\n  1 → Try a different email/phone\n  2 → Continue anyway",
            "current_node": "auth_not_found_handler",
            "awaiting_input": True
        }

def auth_failed(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    normalized_input = user_input.strip() if user_input else ""
    
    if normalized_input == "1":
        return {
            "auth_step": None,
            "otp_attempts": 0,
            "otp_code": None,
            "contact": {"email": None, "phone": None},
            "auth_verified": False,
            "last_message": "Let's start fresh. Please choose:\n  1 → Use Email\n  2 → Use Phone",
            "current_node": "auth_collect_contact",
            "awaiting_input": True
        }
    
    elif normalized_input == "2":
        return {
            "last_message": "Thank you for visiting SunBun. Have a great day! 👋",
            "current_node": "end",
            "awaiting_input": False
        }
        
    else:
        return {
            "last_message": "Please choose an option:\n  1 → Retry authentication\n  2 → Exit",
            "current_node": "auth_failed",
            "awaiting_input": True
        }

# Routers
def route_after_entry(state: State) -> str:
    """Router after entry_node"""
    return state.get("current_node", "entry_node")

def route_after_auth(state: State) -> str:
    """Router for auth flow"""
    return state.get("current_node", "auth_collect_contact")
