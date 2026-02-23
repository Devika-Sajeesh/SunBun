import requests
import time

def test_api():
    base_url = "http://localhost:8000"
    
    # 1. Health Check
    print("Testing /health...")
    try:
        response = requests.get(f"{base_url}/health")
        print(f"Health status: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # 2. Chat Test
    print("\nTesting /chat...")
    payload = {
        "session_id": "test-session-api",
        "message": "Hello"
    }
    try:
        response = requests.post(f"{base_url}/chat", json=payload)
        print(f"Chat status: {response.status_code}")
        print(response.json())
    except Exception as e:
        print(f"Chat test failed: {e}")

if __name__ == "__main__":
    test_api()
