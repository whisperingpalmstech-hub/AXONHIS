import asyncio
import httpx
from decimal import Decimal

async def test_actual_data():
    base_url = "http://localhost:8000/api/v1"
    
    # 1. Login
    async with httpx.AsyncClient() as client:
        login_res = await client.post(f"{base_url}/auth/login", json={
            "email": "admin@axonhis.com",
            "password": "Admin@123"
        })
        if login_res.status_code != 200:
            print("Login failed:", login_res.text)
            return
        
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Logged in as admin@axonhis.com")

        # 2. Get existing accounts
        acc_res = await client.get(f"{base_url}/accounting/accounts", headers=headers)
        accounts = acc_res.json()
        print(f"✅ Found {len(accounts)} accounts in ledger")
        
        cash_acc = next((a for a in accounts if a["account_code"] == "1001"), None)
        rev_acc = next((a for a in accounts if a["account_code"] == "4001"), None)
        
        if not (cash_acc and rev_acc):
            print("❌ Required accounts 1001 or 4001 not found!")
            return

        initial_cash_bal = Decimal(cash_acc["current_balance"])
        initial_rev_bal = Decimal(rev_acc["current_balance"])
        print(f"Initial Balances: Cash={initial_cash_bal}, Revenue={initial_rev_bal}")

        # 3. Create a Journal Entry (Debit Cash 100, Credit Revenue 100)
        journal_data = {
            "description": "Actual data validation transaction",
            "lines": [
                {
                    "account_id": cash_acc["id"],
                    "debit_amount": "500.00",
                    "credit_amount": "0.00",
                    "description": "Consultation Fee Received"
                },
                {
                    "account_id": rev_acc["id"],
                    "debit_amount": "0.00",
                    "credit_amount": "500.00",
                    "description": "Consultation Revenue Recognition"
                }
            ]
        }
        
        create_res = await client.post(f"{base_url}/accounting/journals", json=journal_data, headers=headers)
        if create_res.status_code != 200:
            print("❌ Journal creation failed:", create_res.text)
            return
            
        entry = create_res.json()
        print(f"✅ Journal Entry {entry['entry_number']} created as DRAFT")

        # 4. Post the Journal Entry
        post_res = await client.post(f"{base_url}/accounting/journals/{entry['id']}/post", headers=headers)
        if post_res.status_code != 200:
            print("❌ Posting failed:", post_res.text)
            return
        
        print(f"✅ Journal Entry {entry['entry_number']} POSTED successfully")

        # 5. Verify Balance Update
        acc_res_new = await client.get(f"{base_url}/accounting/accounts", headers=headers)
        accounts_new = acc_res_new.json()
        cash_acc_new = next(a for a in accounts_new if a["account_code"] == "1001")
        rev_acc_new = next(a for a in accounts_new if a["account_code"] == "4001")
        
        final_cash_bal = Decimal(cash_acc_new["current_balance"])
        final_rev_bal = Decimal(rev_acc_new["current_balance"])
        
        print(f"Final Balances: Cash={final_cash_bal}, Revenue={final_rev_bal}")
        
        if final_cash_bal == initial_cash_bal + Decimal("500.00") and final_rev_bal == initial_rev_bal + Decimal("500.00"):
            print("🚀 SUCCESS: Double-entry logic verified with real DB data!")
        else:
            print("⚠️ BALANCE MISMATCH! Logic might be flawed.")

if __name__ == "__main__":
    asyncio.run(test_actual_data())
