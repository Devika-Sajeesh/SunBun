"""
Sales Agent Review Interrupt Nodes
This module contains the Human-in-Loop implementation for the sales proposal workflow.
"""

from langchain_core.messages import AIMessage
from graph.state_aegra import StateAegra

def sales_agent_review_interrupt(state: StateAegra, user_input: str | None) -> dict:
    """
    Human-in-loop node for sales agent to review proposals
    
    This node INTERRUPTS the graph, requiring approval before proceeding
    """
    proposals = state.get("proposals", [])
    
    if not proposals:
        return {
            "current_node": "sales_info_capture",
            "awaiting_input": False,
            "messages": [AIMessage(content="⚠️ No proposals to review. Returning to info capture.")]
        }
    
    # Format proposals for agent review
    review_text = f"""🔍 **SALES AGENT REVIEW REQUIRED**

Generated {len(proposals)} proposal(s) for {state.get('customer_name', 'prospect')}

"""
    
    for i, p in enumerate(proposals, 1):
        review_text += f"""
**Option {i}**: {p['name']}
  • Size: {p['system_size']}
  • Tier: {p['tier']}
  • Price: ₹{p['price']:,}
  • Savings: ₹{p['yearly_savings']:,}/year

"""
    
    review_text += """
**Agent Actions**:
  1 → ✅ Approve and send to customer
  2 → 🔄 Regenerate with different parameters
  3 → ✏️ Add custom notes
  4 → 📋 View top 5 similar options
  5 → ❌ Cancel and start over
"""
    
    return {
        "current_node": "sales_agent_decision",
        "awaiting_input": True,
        "user_role": "sales_executive",  # Switch to agent mode
        "messages": [AIMessage(
            content=review_text,
            additional_kwargs={
                "metadata": {
                    "options": [
                        {"label": "✅ Approve and send", "value": "1"},
                        {"label": "🔄 Regenerate", "value": "2"},
                        {"label": "✏️ Add notes", "value": "3"},
                        {"label": "📋 Top 5 options", "value": "4"},
                        {"label": "❌ Cancel", "value": "5"}
                    ]
                }
            }
        )]
    }


def sales_agent_decision(state: StateAegra, user_input: str | None) -> dict:
    """Handle sales agent's decision after review"""
    
    if user_input == "1":
        # Approve - proceed to customer
        return {
            "current_node": "sales_proposal_select",
            "user_role": "customer",  # Switch back to customer
            "awaiting_input": True,
            "messages": [AIMessage(content="✅ Proposals approved by sales team!\n\nPresenting to customer...")]
        }
    
    elif user_input == "2":
        # Regenerate
        return {
            "current_node": "sales_info_capture",
            "sales_step": "segment",  # Restart from beginning
            "user_role": "sales_executive",
            "messages": [AIMessage(content="🔄 Let's regenerate. Please provide new parameters:\n\nCustomer segment:\n  1 → Residential\n  2 → Commercial\n  3 → Industrial")]
        }
    
    elif user_input == "3":
        # Add notes
        return {
            "current_node": "sales_add_notes",
            "user_role": "sales_executive",
            "messages": [AIMessage(content="✏️ Enter custom notes to add to the proposal:")]
        }
    
    elif user_input == "4":
        # Top 5 options (use DataService to get more templates)
        from services.data_service import get_instance
        ds = get_instance()
        
        # Get more options from template
        all_templates = ds.df_proposal_template.head(5)
        options_text = "📋 **Top 5 Available Options**:\n"
        options = []
        
        for i, (idx, row) in enumerate(all_templates.iterrows(), 1):
            label = f"{row['proposal_name']} (₹{row['approx_price']:,})"
            options_text += f"  {i} \u2192 {label}\n"
            options.append({"label": label, "value": str(i)})
        
        options_text += "\nSelect an option to add to the customer's list:"
        
        return {
            "current_node": "sales_select_from_top5",
            "user_role": "sales_executive",
            "awaiting_input": True,
            "messages": [create_button_message(options_text, options)]
        }
    
    elif user_input == "5":
        # Cancel
        return {
            "current_node": "end",
            "messages": [AIMessage(content="❌ Proposal process cancelled by sales agent.")]
        }
    
    else:
        # Invalid choice
        return {
            "current_node": "sales_agent_decision",
            "messages": [AIMessage(content="Invalid choice. Please select 1-5.")]
        }


def sales_select_from_top5(state: StateAegra, user_input: str | None) -> dict:
    """Handle agent selection from top 5 templates"""
    if not user_input or not user_input.isdigit():
        return {"current_node": "sales_select_from_top5", "awaiting_input": True}
    
    idx = int(user_input) - 1
    from services.data_service import get_instance
    ds = get_instance()
    all_templates = ds.df_proposal_template.head(5)
    
    if 0 <= idx < len(all_templates):
        template = all_templates.iloc[idx]
        new_p = {
            "proposal_id": f"prop-{uuid.uuid4().hex[:6]}",
            "name": template["proposal_name"],
            "system_size": f"{template['system_size_kw']} kWp",
            "inverter_brand": "Growatt",
            "module_brand": "Waaree",
            "tier": "Premium",
            "price": int(template["approx_price"]),
            "yearly_savings": int(template["estimated_yearly_savings"]),
            "agent_notes": "Added by sales expert"
        }
        
        proposals = state.get("proposals", [])
        proposals.append(new_p)
        
        return {
            "proposals": proposals,
            "current_node": "sales_agent_review_interrupt",
            "messages": [AIMessage(content=f"✅ Added '{new_p['name']}' to the proposal list.\n\nReturning to review...")]
        }
    
    return {"current_node": "sales_select_from_top5", "awaiting_input": True}


def sales_add_notes(state: StateAegra, user_input: str | None) -> dict:
    """Add custom notes from sales agent to proposals"""
    
    if not user_input:
        return {
            "current_node": "sales_add_notes",
            "messages": [AIMessage(content="Please enter your notes:")]
        }
    
    # Add notes to all proposals
    proposals = state.get("proposals", [])
    for p in proposals:
        p["agent_notes"] = user_input
    
    return {
        "proposals": proposals,
        "current_node": "sales_agent_review_interrupt",  # Loop back to review
        "messages": [AIMessage(content=f"✅ Notes added: \"{user_input}\"\n\nReturning to review...")]
    }
