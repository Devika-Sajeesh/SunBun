from typing import Dict, Any, Optional, List, Union
from graph.state import State
from services.data_service import get_instance
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# --- Helper Functions ---

def format_proposal_list(proposals: List[Dict[str, Any]]) -> str:
    """Formats a list of existing proposals for display."""
    result = ""
    for i, p in enumerate(proposals, 1):
        result += f"\n{i}. {p['proposal_name']}"
        result += f"\n   📐 Size: {p['system_size_kw']} kWp"
        result += f"\n   💰 Price: ₹{p['approx_price']:,}"
        result += f"\n   📈 Savings: ₹{p['estimated_yearly_savings']:,}/year"
        result += f"\n   📅 Created: {p['date_created']}"
        result += f"\n   📊 Status: {p['status']}\n"
    return result

def format_generated_proposals(proposals: List[Dict[str, Any]]) -> str:
    """Formats a list of freshly generated proposals for display."""
    result = ""
    for i, p in enumerate(proposals, 1):
        result += f"\n🌟 Option {i}: {p['name']}"
        result += f"\n📐 Size: {p['system_size']}"
        result += f"\n🔌 Inverter: {p['inverter_brand']}"
        result += f"\n☀️ Modules: {p['module_brand']}"
        result += f"\n🏷️ Tier: {p['tier']}"
        result += f"\n💰 Price: ₹{p['price']:,}"
        result += f"\n📈 Yearly Savings: ₹{p['yearly_savings']:,}\n"
    return result


# --- Nodes ---

def sales_existing_router(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Checks if the customer has existing proposals and routes accordingly.
    """
    data_service = get_instance()
    
    if state.get("in_db") and state.get("has_proposals"):
        proposals = data_service.get_proposals(state["customer_id"])
        
        return {
            "proposals": proposals,
            "last_message": f"""Hi {state['customer_name']}! We have {len(proposals)} existing proposal(s) for you:

{format_proposal_list(proposals)}

Reply:
  1 → Review existing proposals
  2 → Create new proposals""",
            "current_node": "sales_proposal_choice",
            "awaiting_input": True
        }
    
    else:
        # New prospect or no existing proposals
        return {
            "last_message": f"Hi {state.get('customer_name', 'there')}! Let's design the perfect solar solution for you! ☀️\n\nI'll need a few details to create customized options.",
            "sales_step": "segment",
            "current_node": "sales_info_capture",
            "awaiting_input": True
        }

def sales_proposal_choice(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Handles user choice between reviewing existing or creating new proposals.
    """
    if user_input is None:
        return {"last_message": "Please choose an option (1 or 2).", "current_node": "sales_proposal_choice", "awaiting_input": True}
        
    normalized = user_input.lower().strip()
    
    if normalized == "1" or "review" in normalized:
        return {
            "last_message": "Great! Here are your proposals in detail:\n\n" + format_proposal_list(state['proposals']) + "\nEnter proposal number to select (e.g., 1, 2, 3)\nor type 'new' to generate new options:",
            "sales_step": "reviewing",
            "current_node": "sales_review_proposals",
            "awaiting_input": True
        }
    
    elif normalized == "2" or "new" in normalized or "create" in normalized:
        return {
            "last_message": "Perfect! Let's create fresh options for you.\n\nFirst, are you a:\n  1 → Residential customer\n  2 → Commercial customer\n  3 → Industrial customer",
            "sales_step": "segment",
            "current_node": "sales_info_capture",
            "awaiting_input": True
        }
    
    else:
        return {
            "last_message": "I didn't quite get that. Please reply:\n  1 → Review existing proposals\n  2 → Create new proposals",
            "current_node": "sales_proposal_choice",
            "awaiting_input": True
        }

def sales_review_proposals(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Handles selection of an existing proposal.
    """
    if user_input is None:
        return {"current_node": "sales_review_proposals", "awaiting_input": True}
        
    normalized = user_input.lower().strip()
    
    if normalized.isdigit():
        idx = int(normalized) - 1
        proposals = state.get("proposals", [])
        if 0 <= idx < len(proposals):
            selected = proposals[idx]
            # Mapping from 'proposal_name' to 'name' for consistency if needed, but spec says use key as is
            # Node 7 uses state["chosen_proposal"]["name"]
            # format_proposal_list uses p['proposal_name']
            # So I'll ensure 'name' exists in the chosen_proposal dict for Node 7
            selected_prepared = dict(selected)
            if 'proposal_name' in selected_prepared and 'name' not in selected_prepared:
                selected_prepared['name'] = selected_prepared['proposal_name']
                
            return {
                "chosen_proposal_id": selected["proposal_id"],
                "chosen_proposal": selected_prepared,
                "last_message": f"✅ Great choice! You've selected:\n\n{selected['proposal_name']}\n\nChecking sales team availability...",
                "current_node": "sales_proposal_confirm",
                "awaiting_input": False
            }
        else:
            return {
                "last_message": f"Invalid number. Please enter a value between 1 and {len(proposals)}:",
                "current_node": "sales_review_proposals",
                "awaiting_input": True
            }

    if "new" in normalized:
        return {
            "last_message": "Perfect! Let's create fresh options.\n\nFirst, are you a:\n  1 → Residential\n  2 → Commercial\n  3 → Industrial",
            "sales_step": "segment",
            "current_node": "sales_info_capture",
            "awaiting_input": True
        }
        
    return {
        "last_message": "Please enter a proposal number or type 'new':",
        "current_node": "sales_review_proposals",
        "awaiting_input": True
    }

def sales_info_capture(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Multi-step wizard to collect details for generating new proposals.
    """
    step = state.get("sales_step")
    profile = state.get("sales_profile") or {}
    
    if step == "segment":
        segments = {"1": "Residential", "2": "Commercial", "3": "Industrial"}
        val = segments.get(user_input.strip() if user_input else "", "Residential")
        return {
            "sales_profile": {**profile, "segment": val},
            "sales_step": "monthly_bill",
            "last_message": "What is your average monthly electricity bill? (in ₹, enter number only)",
            "current_node": "sales_info_capture",
            "awaiting_input": True
        }
        
    elif step == "monthly_bill":
        try:
            bill = float(user_input.strip().replace(",", ""))
            return {
                "sales_profile": {**profile, "monthly_bill": bill},
                "sales_step": "growth_pct",
                "last_message": "By what % do you expect your electricity consumption to grow in coming years?\n(e.g., enter 20 for 20%, or 0 for no growth)",
                "current_node": "sales_info_capture",
                "awaiting_input": True
            }
        except ValueError:
            return {"last_message": "Please enter a valid number for your monthly bill:", "current_node": "sales_info_capture", "awaiting_input": True}

    elif step == "growth_pct":
        try:
            pct = float(user_input.strip())
            return {
                "sales_profile": {**profile, "growth_pct": pct},
                "sales_step": "num_options",
                "last_message": "How many solution options would you like to evaluate?\n(enter 1, 2, or 3)",
                "current_node": "sales_info_capture",
                "awaiting_input": True
            }
        except ValueError:
            return {"last_message": "Please enter a valid percentage (e.g., 10):", "current_node": "sales_info_capture", "awaiting_input": True}

    elif step == "num_options":
        if user_input and user_input.strip() in ["1", "2", "3"]:
            return {
                "sales_profile": {**profile, "num_options": int(user_input.strip())},
                "sales_step": "tier_preference",
                "last_message": "Which tier would you prefer?\n  1 → Premium\n  2 → Standard\n  3 → Budget\n(You can pick multiple, e.g., '1,2')",
                "current_node": "sales_info_capture",
                "awaiting_input": True
            }
        else:
            return {"last_message": "Please enter 1, 2, or 3:", "current_node": "sales_info_capture", "awaiting_input": True}

    elif step == "tier_preference":
        mapping = {"1": "Premium", "2": "Standard", "3": "Budget"}
        choices = [c.strip() for c in user_input.split(",")] if user_input else []
        tier_prefs = [mapping[c] for c in choices if c in mapping]
        if not tier_prefs: tier_prefs = ["Standard"]
        
        return {
            "sales_profile": {**profile, "tier_prefs": tier_prefs, "customer_id": state.get("customer_id")},
            "last_message": "⏳ Give us a moment while we design your options...",
            "current_node": "sales_proposal_generate",
            "awaiting_input": False
        }

    return {"current_node": "sales_info_capture", "awaiting_input": True}

def sales_proposal_generate(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Calls DataService to generate customized proposals and presents them.
    """
    data_service = get_instance()
    profile = state.get("sales_profile", {})
    num = profile.get("num_options", 1)
    proposals = data_service.generate_proposals(profile, num)
    
    return {
        "proposals": proposals,
        "last_message": f"""✨ Here are your customized solar options:

{format_generated_proposals(proposals)}

Enter option number to select (1/2/3):""",
        "sales_step": "select_proposal",
        "current_node": "sales_proposal_select",
        "awaiting_input": True
    }

def sales_proposal_select(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Handles user selection from the generated proposals.
    """
    if user_input and user_input.strip().isdigit():
        idx = int(user_input.strip()) - 1
        proposals = state.get("proposals", [])
        if 0 <= idx < len(proposals):
            selected = proposals[idx]
            return {
                "chosen_proposal_id": selected["proposal_id"],
                "chosen_proposal": selected,
                "last_message": f"✅ Great choice! You've selected:\n\n{selected['name']}\n\nChecking sales team availability...",
                "current_node": "sales_proposal_confirm",
                "awaiting_input": False
            }
            
    return {
        "last_message": f"Invalid selection. Please enter a number between 1 and {len(state.get('proposals', []))}:",
        "current_node": "sales_proposal_select",
        "awaiting_input": True
    }

def sales_proposal_confirm(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Checks sales agent availability to determine handoff vs opportunity creation.
    """
    data_service = get_instance()
    agent = data_service.check_agent_availability("sales_executive")
    
    if agent:
        return {
            "available_agent": agent,
            "last_message": f"👤 A sales representative is available!\n\nAgent: {agent['agent_name']}\n\nHow would you prefer to connect?\n  1 → 💬 Chat now\n  2 → 📞 Schedule a call",
            "current_node": "sales_handoff",
            "awaiting_input": True
        }
    else:
        # Create Opportunity
        opp_id = data_service.create_crm_opportunity({
            "prospect_id": state.get("customer_id", 0),
            "chosen_proposal_id": state.get("chosen_proposal_id"),
            "status": "New"
        })
        return {
            "opportunity_id": opp_id,
            "last_message": f"📋 Our sales team is unavailable right now, but we've logged your interest.\n\nOpportunity ID: {opp_id}\n\nYou'll receive a call or email from our team within 24 hours.\n\nThank you for choosing SunBun! ☀️",
            "current_node": "end",
            "awaiting_input": False
        }

def sales_handoff(state: State, user_input: Optional[str]) -> Dict[str, Any]:
    """
    Final node for sales flow. Handles live chat or callback scheduling.
    """
    data_service = get_instance()
    agent = state.get("available_agent", {})
    agent_name = agent.get("agent_name", "a representative")
    proposal = state.get("chosen_proposal", {})
    proposal_name = proposal.get("name", "Solar Solution")
    
    normalized = user_input.lower().strip() if user_input else ""
    
    if normalized == "1" or "chat" in normalized:
        opp_id = data_service.create_crm_opportunity({
            "prospect_id": state.get("customer_id", 0),
            "chosen_proposal_id": state.get("chosen_proposal_id"),
            "status": "In Chat"
        })
        return {
            "opportunity_id": opp_id,
            "last_message": f"🔗 Connecting you to {agent_name} now...\n\n[Live chat session initiated]\n\nContext shared:\n• Customer: {state.get('customer_name', 'New prospect')}\n• Proposal: {proposal_name}\n• Location: {state.get('location', 'Not specified')}\n\nHave a great conversation!",
            "current_node": "end",
            "awaiting_input": False
        }
        
    elif normalized == "2" or "call" in normalized:
        opp_id = data_service.create_crm_opportunity({
            "prospect_id": state.get("customer_id", 0),
            "chosen_proposal_id": state.get("chosen_proposal_id"),
            "status": "Call Scheduled"
        })
        identifier = state.get("contact", {}).get("email") or state.get("contact", {}).get("phone", "provided contact")
        return {
            "opportunity_id": opp_id,
            "last_message": f"📞 Noted! {agent_name} will call you within 1 hour.\n\nA confirmation will be sent to {identifier}.\n\nThank you for choosing SunBun! ☀️",
            "current_node": "end",
            "awaiting_input": False
        }
    
    return {
        "last_message": "Please choose:\n  1 → 💬 Chat now\n  2 → 📞 Schedule a call",
        "current_node": "sales_handoff",
        "awaiting_input": True
    }


# --- Routers ---

def route_sales_entry(state: State) -> str:
    """Route after customer lookup for sales support"""
    if state.get("in_db") and state.get("has_proposals"):
        return "sales_existing_router"
    else:
        return "sales_info_capture"

def route_sales_flow(state: State) -> str:
    """General sales flow router"""
    return state.get("current_node", "sales_info_capture")
