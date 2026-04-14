import asyncio
import httpx
from decimal import Decimal

async def setup_accounts():
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        login_res = await client.post(f"{base_url}/auth/login", json={
            "email": "admin@axonhis.com",
            "password": "Admin@123"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Basic Setup
        required_accounts = [
            {"account_code": "1001", "account_name": "Cash In Hand", "account_type": "ASSET"},
            {"account_code": "1002", "account_name": "Main Bank Account", "account_type": "ASSET"},
            {"account_code": "1005", "account_name": "Patient Receivables", "account_type": "ASSET"},
            {"account_code": "4001", "account_name": "Hospital Service Revenue", "account_type": "REVENUE"},
            {"account_code": "5001", "account_name": "Operational Expenses", "account_type": "EXPENSE"}
        ]

        for acc in required_accounts:
            existing = await client.get(f"{base_url}/accounting/accounts", headers=headers)
            if any(a["account_code"] == acc["account_code"] for a in existing.json()):
                print(f"Skipping {acc['account_code']} - exists")
                continue
            
            res = await client.post(f"{base_url}/accounting/accounts", json=acc, headers=headers)
            if res.status_code == 200:
                print(f"Created {acc['account_code']} - {acc['account_name']}")
            else:
                print(f"Failed {acc['account_code']}: {res.text}")

if __name__ == "__main__":
    asyncio.run(setup_accounts())
