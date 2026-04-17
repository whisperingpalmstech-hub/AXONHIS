import asyncio
import httpx
import time

async def test_endpoint(client, url, method="GET"):
    start_time = time.time()
    try:
        if method == "GET":
            response = await client.get(url)
        elif method == "POST":
            response = await client.post(url, json={})
        elif method == "PUT":
            response = await client.put(url, json={})
        elif method == "DELETE":
            response = await client.delete(url)
        else:
            response = await client.request(method, url)
        
        elapsed_time = (time.time() - start_time) * 1000
        return {
            "url": url,
            "method": method,
            "status_code": response.status_code,
            "time_ms": round(elapsed_time, 2),
            "success": response.status_code < 500
        }
    except Exception as e:
        elapsed_time = (time.time() - start_time) * 1000
        return {
            "url": url,
            "method": method,
            "status_code": None,
            "time_ms": round(elapsed_time, 2),
            "success": False,
            "error": str(e)
        }

async def main():
    # Test different ports to see where backend is running
    base_urls = [
        "http://localhost:8000",
        "http://localhost:8001", 
        "http://localhost:8002",
        "http://localhost:8003",
        "http://localhost:8004",
        "http://localhost:8005",
        "http://localhost:8006",
        "http://localhost:8007"
    ]
    
    test_endpoints = [
        "/api/v1/qa/modules",
        "/api/v1/system/health",
        "/api/v1/auth/login"
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for base_url in base_urls:
            print(f"\nTesting base URL: {base_url}")
            for endpoint in test_endpoints:
                url = base_url + endpoint
                result = await test_endpoint(client, url, "GET")
                status = "✓" if result.get("success") else "✗"
                print(f"  {status} {endpoint}: {result.get('status_code', 'N/A')} - {result.get('error', 'OK')}")

if __name__ == "__main__":
    asyncio.run(main())