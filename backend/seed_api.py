import requests
import time

API_URL = "http://localhost:9500/api/v1"

def seed():
    print("Logging in...")
    try:
        # Standard login for AxonHIS backend
        res = requests.post(f"{API_URL}/auth/login", data={"username": "admin@riv-hlt1.com", "password": "Admin@2025"})
        if not res.ok:
            print("Login failed!", res.text)
            return
            
        token = res.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        
        print("Logged in. Creating categories...")
        categories = [
            {"name": "Standard Bed Sheet", "description": "White cotton blend", "expected_lifespan_washes": 100},
            {"name": "Surgical Gown", "description": "Blue sterile", "expected_lifespan_washes": 50},
            {"name": "Patient Blanket", "description": "Thermal blanket", "expected_lifespan_washes": 200},
            {"name": "Pillow Cover", "description": "White cotton", "expected_lifespan_washes": 100}
        ]
        
        for c in categories:
            r = requests.post(f"{API_URL}/linen/categories", json=c, headers=headers)
            print(f"Created {c['name']}: {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    seed()
