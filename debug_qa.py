#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
import asyncio

# Create a simple test app
app = FastAPI()

@app.get("/api/v1/test/endpoint")
async def test_endpoint():
    return {"message": "test"}

@app.get("/api/v1/auth/login")
async def auth_login():
    return {"message": "login"}

@app.get("/api/v1/patients")
async def patients_list():
    return {"message": "patients"}

# Test the _get_dynamic_endpoints function
from backend.app.core.qa.router import _get_dynamic_endpoints

async def test_dynamic_endpoints():
    client = TestClient(app)
    
    # Create a mock request
    with client:
        response = client.get("/api/v1/test/endpoint")
        request = Request({"type": "http", "app": app})
        
        try:
            modules = _get_dynamic_endpoints(request, app=None)
            print("Dynamic endpoints function succeeded!")
            print(f"Found {len(modules)} modules:")
            for module, endpoints in modules.items():
                print(f"  {module}: {len(endpoints)} endpoints")
                for endpoint in endpoints[:2]:  # Show first 2 endpoints
                    print(f"    - {endpoint['path']} ({endpoint['methods']})")
        except Exception as e:
            print(f"Error in _get_dynamic_endpoints: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dynamic_endpoints())