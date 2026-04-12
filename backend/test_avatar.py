import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def test_avatar_flow():
    print("🚀 Starting Avatar API Test...")
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("🔑 Logging in as admin...")
        login_resp = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"email": "admin@riv-hlt1.com", "password": "Admin@2025"},
            headers={"Content-Type": "application/json"}
        )
        if login_resp.status_code != 200:
            print("❌ Login Failed:", login_resp.text)
            return
        
        token = login_resp.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Login Successful!")

        # 2. Check Admin Configs
        print("⚙️ Fetching Workflow Configs...")
        config_resp = await client.get(f"{BASE_URL}/api/v1/avatar/admin/configs", headers=headers)
        if config_resp.status_code != 200:
            print("❌ Fetch Configs Failed:", config_resp.text)
            return
        print(f"✅ Found {len(config_resp.json())} Workflow Configs")

        # 3. Create Session
        print("🗣️ Creating Avatar Session...")
        session_resp = await client.post(
            f"{BASE_URL}/api/v1/avatar/sessions",
            json={"language": "en"},
            headers=headers
        )
        if session_resp.status_code != 200:
            print("❌ Session Creation Failed:", session_resp.text)
            return
        
        session_id = session_resp.json().get("id")
        print(f"✅ Session Created: {session_id}")

        # 4. Chat with Avatar
        print("💬 Sending message: 'I would like to register as a new patient'")
        chat_resp = await client.post(
            f"{BASE_URL}/api/v1/avatar/sessions/{session_id}/chat",
            json={"text": "I would like to register as a new patient"},
            headers=headers,
            timeout=30.0
        )
        
        if chat_resp.status_code != 200:
            print("❌ Chat Failed:", chat_resp.text)
            return
            
        data = chat_resp.json()
        print("✅ Received Response!")
        print(f"  🤖 Intent: {data.get('intent')}")
        print(f"  🔄 Workflow: {data.get('workflow')}")
        print(f"  📝 Text: {data.get('response_text')}")
        print(f"  🔊 Audio Base64 length: {len(data.get('audio_base64', '')) if data.get('audio_base64') else 0}")
        print(f"  📊 Workflow Status: {json.dumps(data.get('workflow_status'), indent=2)}")

        # 5. Check Analytics
        print("📈 Fetching Analytics...")
        analytics_resp = await client.get(f"{BASE_URL}/api/v1/avatar/admin/analytics", headers=headers)
        if analytics_resp.status_code == 200:
            print(f"✅ Analytics Total Sessions: {analytics_resp.json().get('total_sessions')}")
        else:
            print("❌ Analytics Failed:", analytics_resp.text)

if __name__ == "__main__":
    asyncio.run(test_avatar_flow())
