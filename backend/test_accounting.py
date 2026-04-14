import asyncio
import os
import httpx

async def test_accounting():
    auth_url = "http://localhost:8000/api/v1/auth/login"
    login_data = {
        "email": "admin@axonhis.com",
        "password": "Admin@123"
    }

    async with httpx.AsyncClient() as client:
        # 1. Login
        response = await client.post(auth_url, json=login_data)
        if response.status_code != 200:
            print("Login failed!", response.text)
            return
        
        token = response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in successfully")

        # 2. Test Accounts API
        # Create an account
        account_data = {
            "account_code": "1001",
            "account_name": "Cash Recording Account",
            "account_type": "ASSET",
            "description": "Main cash receiving account"
        }
        res = await client.post("http://localhost:8000/api/v1/accounting/accounts", json=account_data, headers=headers)
        if res.status_code == 200:
            print("✅ Created account:", res.json().get("account_name"))
        elif res.status_code == 400 and "exists" in res.text:
            print("Account already exists, proceeding to fetch.")
        else:
            print("❌ Create account failed:", res.text)
            
        account_data_2 = {
            "account_code": "4001",
            "account_name": "Service Revenue",
            "account_type": "REVENUE",
            "description": "General service revenue"
        }
        res2 = await client.post("http://localhost:8000/api/v1/accounting/accounts", json=account_data_2, headers=headers)
        
        # Get all accounts
        res_list = await client.get("http://localhost:8000/api/v1/accounting/accounts", headers=headers)
        accounts = res_list.json()
        print(f"✅ Retrieved {len(accounts)} accounts")
        
        if len(accounts) < 2:
            print("Not enough accounts to test journal entries.")
            return
            
        acc1 = accounts[0]["id"]
        acc2 = accounts[1]["id"]

        # 3. Test Journal Entry creation
        journal_data = {
            "description": "Test Journal Entry for API validation",
            "reference_type": "TEST",
            "lines": [
                {
                    "account_id": acc1,
                    "debit_amount": "1500.00",
                    "credit_amount": "0.00",
                    "description": "Debit Cash"
                },
                {
                    "account_id": acc2,
                    "debit_amount": "0.00",
                    "credit_amount": "1500.00",
                    "description": "Credit Revenue"
                }
            ]
        }
        
        res_jrn = await client.post("http://localhost:8000/api/v1/accounting/journals", json=journal_data, headers=headers)
        if res_jrn.status_code == 200:
            entry = res_jrn.json()
            print(f"✅ Created Journal Entry: {entry['entry_number']} with status {entry['status']}")
            
            # Test posting
            res_post = await client.post(f"http://localhost:8000/api/v1/accounting/journals/{entry['id']}/post", headers=headers)
            if res_post.status_code == 200:
                print(f"✅ Posted Journal Entry successfully! New status: {res_post.json()['status']}")
            else:
                print("❌ Failed to post journal entry:", res_post.text)
        else:
            print("❌ Create journal entry failed:", res_jrn.text)

if __name__ == "__main__":
    asyncio.run(test_accounting())
