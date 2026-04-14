import requests
import uuid
import sys

BASE_URL = "http://localhost:9500/api/v1"
TOKEN = "YOUR_TOKEN_HERE" # Need to get this from environment or login

def get_token():
    # Attempt to get token from a recent login or environment
    return "TEST_TOKEN" # Placeholder

def test_inventory_endpoints():
    headers = {"Authorization": f"Bearer {TOKEN}"}
    
    endpoints = [
        ("GET", "/inventory/stores"),
        ("GET", "/inventory/items"),
        ("GET", "/inventory/stock-levels"),
        ("GET", "/inventory/stock-movements"),
        ("GET", "/inventory/expiry-alerts"),
        ("GET", "/inventory/indents"),
        ("GET", "/inventory/issues"),
    ]
    
    for method, path in endpoints:
        url = f"{BASE_URL}{path}"
        try:
            if method == "GET":
                resp = requests.get(url, headers=headers)
            print(f"{method} {path} -> {resp.status_code}")
            if resp.status_code != 200:
                print(f"Error: {resp.text}")
        except Exception as e:
            print(f"Failed {path}: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        TOKEN = sys.argv[1]
    test_inventory_endpoints()
