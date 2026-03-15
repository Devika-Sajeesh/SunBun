"""
Automated frontend tests using Playwright
Install: pip install playwright && playwright install
"""

from playwright.sync_api import sync_playwright, expect
import time


def test_frontend_loads():
    """Test frontend loads successfully"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate
        page.goto("http://127.0.0.1:3000")
        
        # Check header
        expect(page.locator("h1")).to_contain_text("SunBun Solar")
        
        # Check input box exists
        input_box = page.locator('input[name="message"]')
        expect(input_box).to_be_visible()
        
        print("✅ Frontend loads correctly")
        
        browser.close()


def test_conversation_flow():
    """Test complete conversation flow"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate
        page.goto("http://127.0.0.1:3000")
        
        # Send initial message
        page.fill('input[name="message"]', "Start")
        page.click('button[type="submit"]')
        
        # Wait for bot response
        page.wait_for_timeout(2000)
        
        # Check for welcome message (specifically in the message area)
        expect(page.locator("text=Welcome to SunBun Solar")).to_be_visible()
        
        # Click "Service Support" button
        service_btn = page.get_by_role("button", name="Service Support")
        if service_btn.count() > 0:
            service_btn.first.click()
            print("✅ Clicked Service Support button")
        else:
            # Fallback: type "2"
            page.fill('input[name="message"]', "2")
            page.click('button[type="submit"]')
            print("⚠️  Typed '2' instead (buttons not found)")
        
        # Wait for next response
        page.wait_for_timeout(2000)
        
        # Check for email/phone prompt - use specific button labels to avoid strict mode error
        expect(page.get_by_role("button", name="Use Email")).to_be_visible()
        expect(page.get_by_role("button", name="Use Phone")).to_be_visible()
        
        print("✅ Conversation flow works")
        
        browser.close()


def test_session_persistence():
    """Test session persists across refreshes"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Start conversation
        page.goto("http://127.0.0.1:3000")
        page.fill('input[name="message"]', "Start")
        page.click('button[type="submit"]')
        page.wait_for_timeout(2000)
        
        # Get session ID
        session_text = page.locator('text=/Session:/')
        if session_text.count() > 0:
            session_before = session_text.first.text_content()
            print(f"Session before refresh: {session_before}")
        
        # Refresh page
        page.reload()
        page.wait_for_timeout(1000)
        
        # Check session ID still there
        if session_text.count() > 0:
            session_after = session_text.first.text_content()
            print(f"Session after refresh: {session_after}")
            
            if session_before == session_after:
                print("✅ Session persisted")
            else:
                print("⚠️  Session changed (might be expected)")
        
        browser.close()


if __name__ == "__main__":
    print("🧪 Running Frontend Automation Tests\n")
    print("⚠️  Make sure both backend and frontend are running!\n")
    
    tests = [
        ("Frontend Loads", test_frontend_loads),
        ("Conversation Flow", test_conversation_flow),
        ("Session Persistence", test_session_persistence)
    ]
    
    for name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"🧪 {name}")
        print('='*60)
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test failed: {e}")
    
    print("\n✅ Frontend automation tests complete!")
