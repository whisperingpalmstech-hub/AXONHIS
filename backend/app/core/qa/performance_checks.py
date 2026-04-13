"""Performance check logic for QA module."""
import time
import asyncio
import httpx
from typing import Dict, Any, List, Optional

from app.core.qa.schemas import PerformanceCheckResponse


async def measure_endpoint_performance(
    endpoint_url: str,
    http_method: str = "GET",
    iterations: int = 10,
    auth_token: Optional[str] = None
) -> PerformanceCheckResponse:
    """
    Measure endpoint performance over multiple iterations.
    
    Args:
        endpoint_url: The URL to measure
        http_method: HTTP method
        iterations: Number of iterations to run
        auth_token: Optional authentication token
    
    Returns:
        PerformanceCheckResponse with performance metrics
    """
    response_times = []
    errors = []
    
    for i in range(iterations):
        start_time = time.time()
        
        try:
            headers = {}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if http_method.upper() == "GET":
                    response = await client.get(endpoint_url, headers=headers)
                elif http_method.upper() == "POST":
                    response = await client.post(endpoint_url, headers=headers)
                else:
                    response = await client.get(endpoint_url, headers=headers)
            
            response_time_ms = (time.time() - start_time) * 1000
            response_times.append(response_time_ms)
        
        except Exception as e:
            errors.append(str(e))
    
    if not response_times:
        return PerformanceCheckResponse(
            endpoint_url=endpoint_url,
            status="error",
            avg_response_time_ms=0,
            min_response_time_ms=0,
            max_response_time_ms=0,
            within_threshold=False,
            error_message=f"All iterations failed: {'; '.join(errors)}"
        )
    
    avg_response_time_ms = sum(response_times) / len(response_times)
    min_response_time_ms = min(response_times)
    max_response_time_ms = max(response_times)
    
    # Default threshold is 1000ms if not specified
    within_threshold = avg_response_time_ms <= 1000
    
    return PerformanceCheckResponse(
        endpoint_url=endpoint_url,
        status="within_threshold" if within_threshold else "slow",
        avg_response_time_ms=round(avg_response_time_ms, 2),
        min_response_time_ms=round(min_response_time_ms, 2),
        max_response_time_ms=round(max_response_time_ms, 2),
        within_threshold=within_threshold,
        error_message=None if within_threshold else f"Average response time {avg_response_time_ms:.2f}ms exceeds threshold 1000ms"
    )


async def measure_query_performance(
    query: str,
    db,
    iterations: int = 10,
    max_time_ms: Optional[int] = None
) -> PerformanceCheckResponse:
    """
    Measure database query performance over multiple iterations.
    
    Args:
        query: SQL query to measure
        db: Database session
        iterations: Number of iterations to run
        max_time_ms: Optional maximum query time threshold
    
    Returns:
        PerformanceCheckResponse with performance metrics
    """
    from sqlalchemy import text
    
    query_times = []
    errors = []
    
    for i in range(iterations):
        start_time = time.time()
        
        try:
            result = await db.execute(text(query))
            result.fetchall()
            
            query_time_ms = (time.time() - start_time) * 1000
            query_times.append(query_time_ms)
        
        except Exception as e:
            errors.append(str(e))
    
    if not query_times:
        return PerformanceCheckResponse(
            endpoint_url="database_query",
            status="error",
            avg_response_time_ms=0,
            min_response_time_ms=0,
            max_response_time_ms=0,
            within_threshold=False,
            error_message=f"All iterations failed: {'; '.join(errors)}"
        )
    
    avg_query_time_ms = sum(query_times) / len(query_times)
    min_query_time_ms = min(query_times)
    max_query_time_ms = max(query_times)
    
    within_threshold = True
    if max_time_ms and avg_query_time_ms > max_time_ms:
        within_threshold = False
    
    return PerformanceCheckResponse(
        endpoint_url="database_query",
        status="within_threshold" if within_threshold else "slow",
        avg_response_time_ms=round(avg_query_time_ms, 2),
        min_response_time_ms=round(min_query_time_ms, 2),
        max_response_time_ms=round(max_query_time_ms, 2),
        within_threshold=within_threshold,
        error_message=None if within_threshold else f"Average query time {avg_query_time_ms:.2f}ms exceeds threshold {max_time_ms}ms"
    )


async def measure_api_throughput(
    endpoints: List[Dict[str, Any]],
    duration_seconds: int = 60,
    concurrent_requests: int = 10
) -> Dict[str, Any]:
    """
    Measure API throughput by making concurrent requests over a duration.
    
    Args:
        endpoints: List of endpoint dictionaries with 'url' and 'method' keys
        duration_seconds: Duration to run the test
        concurrent_requests: Number of concurrent requests
    
    Returns:
        Dictionary with throughput metrics
    """
    async def make_request(endpoint: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if endpoint.get("method", "GET").upper() == "GET":
                    response = await client.get(endpoint["url"])
                else:
                    response = await client.post(endpoint["url"])
            
            response_time_ms = (time.time() - start_time) * 1000
            return {
                "endpoint": endpoint["url"],
                "status": response.status_code,
                "response_time_ms": response_time_ms,
                "success": response.status_code == 200
            }
        except Exception as e:
            return {
                "endpoint": endpoint["url"],
                "status": "error",
                "response_time_ms": (time.time() - start_time) * 1000,
                "success": False,
                "error": str(e)
            }
    
    results = []
    start_time = time.time()
    request_count = 0
    
    while (time.time() - start_time) < duration_seconds:
        # Create batch of concurrent requests
        batch = []
        for endpoint in endpoints:
            for _ in range(concurrent_requests // len(endpoints)):
                batch.append(make_request(endpoint))
        
        batch_results = await asyncio.gather(*batch, return_exceptions=True)
        results.extend(batch_results)
        request_count += len(batch)
    
    # Calculate metrics
    successful_requests = sum(1 for r in results if isinstance(r, dict) and r.get("success"))
    failed_requests = len(results) - successful_requests
    avg_response_time_ms = sum(
        r.get("response_time_ms", 0) for r in results if isinstance(r, dict)
    ) / len(results) if results else 0
    
    throughput = request_count / duration_seconds
    
    return {
        "duration_seconds": duration_seconds,
        "total_requests": request_count,
        "successful_requests": successful_requests,
        "failed_requests": failed_requests,
        "success_rate": (successful_requests / request_count * 100) if request_count > 0 else 0,
        "throughput_requests_per_second": round(throughput, 2),
        "avg_response_time_ms": round(avg_response_time_ms, 2),
        "results": results
    }
