"""
Comprehensive test suite for SunBun Solar Assistant
Tests all flows: Auth, Service (known/unknown), Sales (existing/new)
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Note: Using orchestrator.py as it handles the graph assembly and session management
from graph.orchestrator import get_graph_instance


class TestRunner:
    """Test runner with pretty output"""
    
    def __init__(self):
        self.graph = get_graph_instance()
        self.passed = 0
        self.failed = 0
        self.test_results = []
    
    def run_conversation(self, test_name: str, session_id: str, messages: list, 
                        assertions: list = None):
        """
        Run a conversation flow and test assertions
        
        Args:
            test_name: Name of the test
            session_id: Session ID to use
            messages: List of user messages to send
            assertions: List of (state_key, expected_value) tuples to check.
                        expected_value can be a value or a callable (lambda).
        """
        print(f"\n{'='*70}")
        print(f"🧪 TEST: {test_name}")
        print(f"{'='*70}")
        
        try:
            # Reset session
            self.graph.reset_session(session_id)
            
            # Send messages
            for i, msg in enumerate(messages, 1):
                print(f"\n[Step {i}]")
                print(f"👤 User: {msg if msg is not None else '(Start)'}")
                
                result = self.graph.process_message(session_id, msg)
                
                # Truncate long responses
                response = result["response"]
                if len(response) > 200:
                    response = response[:200] + "..."
                
                print(f"🤖 Assistant: {response}")
                print(f"📍 Node: {result['current_node']}")
            
            # Check assertions
            if assertions:
                state = self.graph.get_session_state(session_id)
                print(f"\n📋 Assertions:")
                
                for key, expected in assertions:
                    actual = state.get(key)
                    
                    # Support for lambda/callable assertions
                    if callable(expected):
                        is_match = expected(actual)
                    else:
                        is_match = (actual == expected)
                        
                    status = "✅" if is_match else "❌"
                    print(f"  {status} {key}: expected={expected if not callable(expected) else '[Lambda Check]'}, actual={actual}")
                    
                    if not is_match:
                        raise AssertionError(
                            f"{key} mismatch: expected {expected}, got {actual}"
                        )
            
            print(f"\n✅ PASSED: {test_name}")
            self.passed += 1
            self.test_results.append((test_name, "PASSED", None))
            
        except Exception as e:
            print(f"\n❌ FAILED: {test_name}")
            print(f"   Error: {e}")
            import traceback
            # traceback.print_exc() # Uncomment for deep debugging
            self.failed += 1
            self.test_results.append((test_name, "FAILED", str(e)))
    
    def print_summary(self):
        """Print test summary"""
        print(f"\n{'='*70}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*70}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        
        total = self.passed + self.failed
        if total > 0:
            print(f"📈 Success Rate: {self.passed}/{total} "
                  f"({100*self.passed/total:.1f}%)")
        
        if self.failed > 0:
            print(f"\n❌ Failed Tests:")
            for name, status, error in self.test_results:
                if status == "FAILED":
                    print(f"  • {name}")
                    if error:
                        print(f"    {error}")
        
        print(f"{'='*70}\n")


def main():
    """Run all tests"""
    runner = TestRunner()
    
    # ===== AUTH TESTS =====
    
    # Test 1: Successful email OTP auth
    runner.run_conversation(
        "Auth: Email OTP Success",
        "test-auth-email",
        [
            None,  # Start
            "2",   # Service support
            "1",   # Use email
            "john.doe@example.com",  # Enter email
            "123456"  # Enter OTP (mocked)
        ],
        assertions=[
            ("auth_verified", True),
            ("is_in_db", True),
            ("customer_name", "John Doe")
        ]
    )
    
    # Test 2: Successful phone OTP auth
    runner.run_conversation(
        "Auth: Phone OTP Success",
        "test-auth-phone",
        [
            None,
            "1",   # Sales support
            "2",   # Use phone
            "555-0101",
            "123456"
        ],
        assertions=[
            ("auth_verified", True),
            ("support_type", "sales")
        ]
    )
    
    # Test 3: OTP retry then success
    runner.run_conversation(
        "Auth: OTP Retry Flow",
        "test-auth-retry",
        [
            None,
            "2",
            "1",
            "john.doe@example.com",
            "000000",  # Wrong OTP
            "111111",  # Wrong again
            "123456"   # Correct
        ],
        assertions=[
            ("auth_verified", True),
            ("otp_attempts", 2)  # Should have 2 failed attempts
        ]
    )
    
    # Test 4: Customer not found, try again
    runner.run_conversation(
        "Auth: Not Found - Retry",
        "test-auth-notfound",
        [
            None,
            "2",
            "1",
            "unknown@example.com",
            "123456",  # OTP correct but user not in DB
            "1",       # Try different email
            "1",       # Use email again
            "john.doe@example.com",
            "123456"
        ],
        assertions=[
            ("is_in_db", True),
            ("customer_name", "John Doe")
        ]
    )
    
    # ===== SERVICE TESTS - KNOWN CUSTOMER =====
    
    # Test 5: Service - Active Issue
    runner.run_conversation(
        "Service: Active Issue (Site 101)",
        "test-service-issue",
        [
            None,
            "2",   # Service
            "1",   # Email
            "john.doe@example.com",
            "123456",
            "1"    # Happy with explanation
        ],
        assertions=[
            ("support_type", "service"),
            ("issue_flag", True),
            ("issue_text", "Communication Loss"),
            ("nps_score", None)  # Hasn't provided NPS yet
        ]
    )
    
    # Test 6: Service - No Issue, Good Performance
    runner.run_conversation(
        "Service: Normal Performance",
        "test-service-normal",
        [
            None,
            "2",
            "1",
            "jane.smith@example.com",  # Customer with site 102
            "123456",
            "1",   # Happy
            "9",   # NPS score
            "Great service!"
        ],
        assertions=[
            ("nps_score", 9),
            ("ticket_id", lambda x: x is not None)  # Ticket created
        ]
    )
    
    # Test 7: Service - Escalation with Agent
    runner.run_conversation(
        "Service: Escalation - Agent Available",
        "test-service-escalation",
        [
            None,
            "2",
            "1",
            "john.doe@example.com",
            "123456",
            "2",   # Not happy, need help
            "1",   # Production Issue
            "My panels are producing very low power",
            "skip",  # No photos
            "1"    # Yes, connect to agent
        ],
        assertions=[
            ("selected_issue", "Production Issue"),
            ("description", "My panels are producing very low power")
        ]
    )
    
    # Test 8: Service - Unknown Customer
    runner.run_conversation(
        "Service: Unknown Customer Flow",
        "test-service-unknown",
        [
            None,
            "2",
            "1",
            "newuser@example.com",
            "123456",
            "2",   # Continue anyway
            "5",   # System size 5 kWp
            "Enphase",  # Inverter
            "2022",     # Year
            "1",        # Monitoring active
            "SolarCorp",  # Installer
            "2",        # System not working
            "System completely offline since yesterday",
            "skip"
        ],
        assertions=[
            ("is_in_db", False),
            ("system_info", lambda x: x is not None)
        ]
    )
    
    # ===== SALES TESTS - EXISTING CUSTOMER =====
    
    # Test 9: Sales - Review Existing Proposals
    runner.run_conversation(
        "Sales: Review Existing Proposals",
        "test-sales-existing",
        [
            None,
            "1",   # Sales
            "1",   # Email
            "john.doe@example.com",
            "123456",
            "1",   # Review existing
            "1",   # Select first proposal
            "1"    # Chat now
        ],
        assertions=[
            ("support_type", "sales"),
            ("has_proposals", True),
            ("chosen_proposal_id", lambda x: x is not None)
        ]
    )
    
    # Test 10: Sales - Create New Proposals (Existing Customer)
    runner.run_conversation(
        "Sales: New Proposals for Existing Customer",
        "test-sales-new-existing",
        [
            None,
            "1",
            "1",
            "john.doe@example.com",
            "123456",
            "2",     # Create new
            "1",     # Residential
            "8000",  # Monthly bill
            "20",    # 20% growth
            "2",     # 2 options
            "1,2",   # Premium and Standard
            "1",     # Select first option
            "2"      # Schedule call
        ],
        assertions=[
            ("sales_profile", lambda x: x.get("monthly_bill") == 8000.0),
            ("proposals", lambda x: len(x) == 2)
        ]
    )
    
    # Test 11: Sales - New Prospect
    runner.run_conversation(
        "Sales: New Prospect Flow",
        "test-sales-prospect",
        [
            None,
            "1",
            "1",
            "newprospect@example.com",
            "123456",
            "2",      # Continue anyway (not in DB)
            "2",      # Commercial
            "15000",  # Bill
            "30",     # Growth
            "1",      # 1 option
            "2",      # Standard tier
            "1"       # Select option
        ],
        assertions=[
            ("is_in_db", False),
            ("sales_profile", lambda x: x.get("segment") == "Commercial"),
            ("opportunity_id", lambda x: x is not None)
        ]
    )
    
    # ===== EDGE CASES =====
    
    # Test 12: Invalid Inputs
    runner.run_conversation(
        "Edge Case: Invalid Inputs",
        "test-invalid",
        [
            None,
            "99",   # Invalid option
            "1",    # Valid: Sales
            "1",
            "john.doe@example.com",
            "123456",
            "xyz",  # Invalid when asked for 1/2
            "1"     # Valid
        ],
        assertions=[
            ("support_type", "sales")
        ]
    )
    
    # Test 13: Conversation End and Restart
    runner.run_conversation(
        "Edge Case: End and Restart",
        "test-restart",
        [
            None,
            "1",
            "1",
            "john.doe@example.com",
            "wrong",
            "wrong",
            "wrong",
            "2",    # Exit after 3 failures
            None    # Start new conversation (should restart)
        ],
        assertions=[
            ("current_node", "entry_node")
        ]
    )
    
    # Print summary
    runner.print_summary()
    
    # Return exit code
    return 0 if runner.failed == 0 else 1


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║           🌞 SUNBUN SOLAR ASSISTANT - TEST SUITE                  ║
║                                                                    ║
║  Testing all flows: Auth, Service (known/unknown), Sales          ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
    """)
    
    exit_code = main()
    sys.exit(exit_code)
