import requests
import json
import time
import sys

BASE_URL = "http://localhost:8000/api"

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def test_endpoints():
    print_header("Testing Basic Endpoints")
    endpoints = [
        ("GET", "/config/icp"),
        ("GET", "/agents"),
        ("GET", "/triggers/sources"),
        ("GET", "/events")
    ]
    
    for method, path in endpoints:
        url = f"{BASE_URL}{path}"
        try:
            if method == "GET":
                res = requests.get(url, timeout=5)
            print(f"[{res.status_code}] {method} {path}")
            if res.status_code >= 400:
                print(f"Error payload: {res.text}")
        except Exception as e:
            print(f"[FAIL] {method} {path} - {str(e)}")

def test_prospect_streaming():
    print_header("Testing Prospect Creation & Live Streaming")
    
    # 1. Create Prospect
    payload = {
        "company_name": "E2E Test Corp",
        "website": "https://example.com",
        "simulate_failure": False
    }
    
    print("Creating prospect...")
    res = requests.post(f"{BASE_URL}/prospects", json=payload)
    if res.status_code != 200:
        print(f"Failed to create prospect: {res.text}")
        sys.exit(1)
        
    data = res.json()
    prospect_id = data.get("prospect_id")
    print(f"Success! Prospect ID: {prospect_id}")
    
    # 2. Connect to SSE stream
    stream_url = f"{BASE_URL}/prospects/{prospect_id}/stream"
    print(f"\nConnecting to SSE Stream: {stream_url}")
    print("Waiting for live agent thinking events (Timeout 30s)...\n")
    
    try:
        # We read the stream line by line
        with requests.get(stream_url, stream=True, timeout=30) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    decoded = line.decode('utf-8')
                    if decoded.startswith('data: '):
                        data_str = decoded[6:]
                        try:
                            event = json.loads(data_str)
                            agent = event.get('agent', 'SYSTEM')
                            msg = event.get('message', '')
                            evt_type = event.get('type', 'info')
                            
                            print(f"[{evt_type.upper()}] {agent}: {msg}")
                            
                            # If state_update, show current node
                            if evt_type == 'state_update':
                                payload = event.get('payload', {})
                                status = payload.get('overall_status')
                                print(f"   -> [STATE] Status: {status}, Confidence: {payload.get('confidence_score')}")
                                if status in ['APPROVED', 'REJECTED', 'FAILED']:
                                    print(f"\nWorkflow finished with status: {status}")
                                    return
                                    
                        except json.JSONDecodeError:
                            print(f"Raw event: {data_str}")
    except requests.exceptions.Timeout:
        print("\n[TIMEOUT] SSE stream timed out.")
    except Exception as e:
        print(f"\n[ERROR] Stream error: {str(e)}")

if __name__ == "__main__":
    print("Starting E2E Tests...\n")
    try:
        requests.get(f"{BASE_URL}/events", timeout=2)
    except requests.exceptions.ConnectionError:
        print(f"Cannot connect to {BASE_URL}. Ensure the backend is running.")
        sys.exit(1)
        
    test_endpoints()
    test_prospect_streaming()
    print("\nE2E Tests Complete.")
