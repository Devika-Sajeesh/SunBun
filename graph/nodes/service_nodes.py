from typing import Dict, Any, Optional, Literal
from graph.state import State
from services.data_service import get_instance
import logging

logger = logging.getLogger(__name__)

def service_status_check(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Checks real-time status of the customer's site.
    Returns issue details if flagged, or metrics analysis if no issues.
    """
    data_service = get_instance()
    
    # Ensure site_id is valid
    if not state.get("site_id"):
        return {
            "last_message": "We couldn't find a site associated with your account. Connecting you to an agent...",
            "current_node": "service_issue_capture", # Fallback
            "service_step": "select_issue",
            "awaiting_input": True
        }

    site_status = data_service.get_site_status(state["site_id"])
    metrics = data_service.get_weekly_metrics(state["site_id"]) # Default 7 days
    
    customer_name = state.get("customer_name", "Customer")
    location = state.get("location", "your location")
    
    # CASE 1: Active Issue Flag
    if site_status.get("issue_flag"):
        return {
            "issue_flag": True,
            "issue_text": site_status.get("issue_text"),
            "action_text": site_status.get("recommended_action_text"),
            "last_message": f"""Hi {customer_name} from {location}, welcome back! 🌞

Checking your solar system status...

⚠️ Active Issue Detected

Issue: {site_status.get('issue_text')}

Recommended Action: {site_status.get('recommended_action_text')}

Does this answer your question?
  1 → Yes, I'm satisfied
  2 → No, I still need help""",
            "current_node": "service_resolution_router",
            "awaiting_input": True
        }
    
    # CASE 2: No Active Issue - Analyze Metrics
    else:
        # Check cloudiness
        if metrics.get("is_cloudy"):
             return {
                "issue_flag": False,
                "metrics": metrics,
                "last_message": f"""Hi {customer_name} from {location}, welcome back! 🌞

Checking your solar system status...

☁️ No active faults detected.

However, the past week has been unusually cloudy at your location (avg {metrics.get('avg_cloudiness')}% cloud cover), which explains lower production.

📊 Your 7-day production: {metrics.get('total_production')} kWh
🎯 Performance score: {metrics.get('avg_performance')}%

This should auto-correct as weather improves.

Does this answer your question?
  1 → Yes, I'm satisfied
  2 → No, I still need help""",
                "current_node": "service_resolution_router",
                "awaiting_input": True
            }
        
        # Check performance
        elif metrics.get("avg_performance", 0) >= 75:
            return {
                "issue_flag": False,
                "metrics": metrics,
                "last_message": f"""Hi {customer_name} from {location}, welcome back! 🌞

Checking your solar system status...

✅ Your system is performing normally!

📊 Last 7 days production: {metrics.get('total_production')} kWh
🎯 Average performance score: {metrics.get('avg_performance')}%
☁️ Average cloudiness: {metrics.get('avg_cloudiness')}%

Does this answer your question?
  1 → Yes, I'm satisfied
  2 → No, I still need help""",
                "current_node": "service_resolution_router",
                "awaiting_input": True
            }
        
        # Underperformance without cloudiness explanation
        else:
            return {
                "issue_flag": False,
                "metrics": metrics,
                "last_message": f"""Hi {customer_name} from {location}, welcome back! 🌞

Checking your solar system status...

⚡ We notice a slight underperformance trend (score: {metrics.get('avg_performance')}%), but nothing critical yet. We're monitoring it.

📊 7-day production: {metrics.get('total_production')} kWh

Does this answer your question?
  1 → Yes, I'm satisfied
  2 → No, I still need help""",
                "current_node": "service_resolution_router",
                "awaiting_input": True
            }

def service_resolution_router(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Routes based on whether the automated check satisfied the user.
    """
    if user_input is None:
         return {"last_message": "Please make a selection.", "current_node": "service_resolution_router", "awaiting_input": True}

    normalized = user_input.lower().strip()
    
    if normalized == "1" or "yes" in normalized or "satisfied" in normalized:
        return {
            "last_message": "Great! We'll log that your query has been resolved.",
            "current_node": "service_happy_close",
            "awaiting_input": False
        }
    
    elif normalized == "2" or "no" in normalized or "help" in normalized:
        return {
            "last_message": """Sorry to hear that. Let's understand the issue better.

Please select issue type:
  1 → Production Issue
  2 → System Not Working
  3 → Communication Loss
  4 → Battery Failure
  5 → Inverter Failure
  6 → Others""",
            "service_step": "select_issue",
            "current_node": "service_issue_capture",
            "awaiting_input": True
        }
    
    else:
        return {
             "last_message": "Please reply:\n  1 → Yes, satisfied\n  2 → No, need help",
             "current_node": "service_resolution_router",
             "awaiting_input": True
        }

def service_happy_close(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Creates a closed ticket and asks for NPS.
    """
    data_service = get_instance()
    ticket_id = data_service.create_service_ticket({
        "customer_id": state.get("customer_id"),
        "site_id": state.get("site_id"),
        "issue_category": "Resolved Inquiry",
        "description": "Customer satisfied with automated response",
        "status": "Closed"
    })
    
    return {
        "ticket_id": ticket_id,
        "last_message": f"✅ Great! We've logged your query as resolved.\n\n🎫 Ticket #{ticket_id}\n\nOn a scale of 1–10, how satisfied are you with this support?\n\nEnter a number (1-10):",
        "current_node": "service_nps_collect",
        "awaiting_input": True
    }

def service_nps_collect(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Validates NPS score (1-10).
    """
    if user_input is None:
        return {"last_message": "Please enter a number (1-10):", "current_node": "service_nps_collect", "awaiting_input": True}

    try:
        score = int(user_input.strip())
        if 1 <= score <= 10:
            return {
                "nps_score": score,
                "last_message": f"Thank you for the {score}/10 rating! 🙏\n\nAnything else you'd like to share about your experience?\n(Type your feedback or 'skip' to finish)",
                "current_node": "service_nps_feedback",
                "awaiting_input": True
            }
    except ValueError:
        pass
        
    return {
        "last_message": "Please enter a valid number between 1 and 10:",
        "current_node": "service_nps_collect",
        "awaiting_input": True
    }

def service_nps_feedback(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Captures optional text feedback and ends flow.
    """
    feedback = user_input.strip() if user_input and user_input.lower().strip() != "skip" else ""
    return {
        "nps_feedback": feedback,
        "last_message": f"Thank you, {state.get('customer_name', 'Customer')}! Your feedback helps us improve. ☀️\n\nHave a great day!",
        "current_node": "end",
        "awaiting_input": False
    }

def service_issue_capture(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Multi-step wizard to capture technical issues and route to agent/ticket.
    """
    step = state.get("service_step")
    
    if step == "select_issue":
        # Map input to category
        mapping = {
            "1": "Production Issue",
            "2": "System Not Working",
            "3": "Communication Loss",
            "4": "Battery Failure",
            "5": "Inverter Failure",
            "6": "Others"
        }
        category = mapping.get(user_input.strip(), "Others") if user_input else "Others"
        
        return {
            "selected_issue": category,
            "service_step": "enter_description",
            "last_message": "Please describe the issue in your own words:",
            "current_node": "service_issue_capture",
            "awaiting_input": True
        }
    
    elif step == "enter_description":
        return {
            "description": user_input,
            "service_step": "upload_photos",
            "last_message": "If you have photos or screenshots, enter file paths separated by commas.\n(or type 'skip')",
            "current_node": "service_issue_capture",
            "awaiting_input": True
        }
    
    elif step == "upload_photos":
        photos_list = [p.strip() for p in user_input.split(',')] if user_input and user_input.lower().strip() != "skip" else []
        
        data_service = get_instance()
        agent = data_service.check_agent_availability("service_executive")
        
        if agent:
            return {
                "photos": photos_list,
                "available_agent": agent,
                "last_message": f"👤 A service executive is available right now!\n\nAgent: {agent['agent_name']}\n\nWould you like to start a live chat?\n  1 → Yes, connect me\n  2 → No, just create a ticket",
                "service_step": "agent_decision",
                "current_node": "service_issue_capture",
                "awaiting_input": True
            }
        else:
            # No agent -> Create Ticket directly
            ticket_id = data_service.create_service_ticket({
                "customer_id": state.get("customer_id"),
                "site_id": state.get("site_id"),
                "issue_category": state.get("selected_issue"),
                "description": state.get("description"),
                "status": "Open"
            })
            return {
                "photos": photos_list,
                "ticket_id": ticket_id,
                "last_message": f"Our service team is currently offline.\n\nI've created a ticket with all your details.\n\n🎫 Ticket #{ticket_id}\n\nOur team will reach out to you shortly.\n\nThank you!",
                "current_node": "end",
                "awaiting_input": False
            }
            
    elif step == "agent_decision":
        data_service = get_instance()
        if user_input and user_input.strip() == "1":
             # Chat Handover (simulated)
             # Create ticket to log the request anyway
             ticket_id = data_service.create_service_ticket({
                "customer_id": state.get("customer_id"),
                "site_id": state.get("site_id"),
                "issue_category": state.get("selected_issue"),
                "description": state.get("description"),
                "status": "Agent Assigned"
            })
             agent = state.get("available_agent", {})
             return {
                 "ticket_id": ticket_id,
                 "last_message": f"🔗 Connecting you to {agent.get('agent_name', 'an agent')} now...\n\n[Live chat session initiated]\n\nContext shared: {state.get('customer_name')}, Site #{state.get('site_id')}, Issue: {state.get('selected_issue')}\n\nHave a great conversation!",
                 "current_node": "end",
                 "awaiting_input": False
             }
        else:
            # Create Ticket
            ticket_id = data_service.create_service_ticket({
                "customer_id": state.get("customer_id"),
                "site_id": state.get("site_id"),
                "issue_category": state.get("selected_issue"),
                "description": state.get("description"),
                "status": "Open"
            })
            return {
                "ticket_id": ticket_id,
                "last_message": f"Got it! We've created a ticket for you.\n\n🎫 Ticket #{ticket_id}\n\nOur team will follow up soon.",
                "current_node": "end",
                "awaiting_input": False
            }
            
    return {"current_node": "service_issue_capture", "awaiting_input": True} # Fallback

def service_unknown_customer(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Collects system info for users not in the database.
    """
    step = state.get("unknown_step")
    system_info = state.get("system_info") or {}
    
    if step is None or step == "system_size": # Entry or Step 1
        if not step:
             return {
                "unknown_step": "system_size",
                "last_message": "We don't have your system in our records, but we can still help!\n\nLet's collect a few details about your setup.\n\nApproximate system size (in kWp, e.g., 5, 7, 10):",
                "current_node": "service_unknown_customer",
                "awaiting_input": True
            }
        else:
            return {
                "system_info": {**system_info, "size": user_input},
                "unknown_step": "inverter_brand",
                "last_message": "Inverter brand/model (e.g., GoodWe, Enphase, SolarEdge):",
                "current_node": "service_unknown_customer",
                "awaiting_input": True
            }

    elif step == "inverter_brand":
        return {
            "system_info": {**system_info, "inverter": user_input},
            "unknown_step": "install_year",
            "last_message": "Year of installation (e.g., 2022):",
            "current_node": "service_unknown_customer",
            "awaiting_input": True
        }
        
    elif step == "install_year":
        return {
            "system_info": {**system_info, "year": user_input},
            "unknown_step": "monitoring",
            "last_message": "Is online monitoring active?\n  1 → Yes\n  2 → No",
            "current_node": "service_unknown_customer",
            "awaiting_input": True
        }
        
    elif step == "monitoring":
        return {
            "system_info": {**system_info, "monitoring": user_input == "1"},
            "unknown_step": "installer",
            "last_message": "Who installed your system?\n(Enter installer name or 'Don't remember')",
            "current_node": "service_unknown_customer",
            "awaiting_input": True
        }
        
    elif step == "installer":
        return {
            "system_info": {**system_info, "installer": user_input},
            "last_message": "Thank you! Now, please select the issue type:\n  1 → Production Issue\n  2 → System Not Working\n  3 → Communication Loss\n  4 → Battery Failure\n  5 → Inverter Failure\n  6 → Others",
            "service_step": "select_issue", # Handoff to issue capture
            "current_node": "service_issue_capture",
            "awaiting_input": True
        }
        
    return {"current_node": "service_unknown_customer", "awaiting_input": True}

# Routers

def route_service_entry(state: State) -> str:
    """Route after customer lookup for service support"""
    if state.get("is_in_db"):
        return "service_status_check"
    else:
        return "service_unknown_customer"

def route_service_flow(state: State) -> str:
    """General service flow router"""
    return state.get("current_node", "service_status_check")
