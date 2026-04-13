"""Health check logic for QA module."""
import httpx
import time
from typing import Dict, Any, Optional
from fastapi import HTTPException

from app.core.qa.schemas import HealthCheckResponse


async def check_endpoint_health(
    endpoint_url: str,
    http_method: str = "GET",
    expected_status: int = 200,
    auth_token: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None
) -> HealthCheckResponse:
    """
    Check if an endpoint is healthy and responding correctly.
    
    Args:
        endpoint_url: The URL to check
        http_method: HTTP method (GET, POST, etc.)
        expected_status: Expected HTTP status code
        auth_token: Optional authentication token
        headers: Optional additional headers
    
    Returns:
        HealthCheckResponse with status and details
    """
    start_time = time.time()
    
    try:
        request_headers = headers or {}
        if auth_token:
            request_headers["Authorization"] = f"Bearer {auth_token}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if http_method.upper() == "GET":
                response = await client.get(endpoint_url, headers=request_headers)
            elif http_method.upper() == "POST":
                response = await client.post(endpoint_url, headers=request_headers)
            elif http_method.upper() == "PUT":
                response = await client.put(endpoint_url, headers=request_headers)
            elif http_method.upper() == "DELETE":
                response = await client.delete(endpoint_url, headers=request_headers)
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported HTTP method: {http_method}")
        
        response_time_ms = (time.time() - start_time) * 1000
        is_healthy = response.status_code == expected_status
        
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="healthy" if is_healthy else "unhealthy",
            response_status=response.status_code,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=is_healthy,
            error_message=None if is_healthy else f"Expected status {expected_status}, got {response.status_code}"
        )
    
    except httpx.TimeoutException:
        response_time_ms = (time.time() - start_time) * 1000
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="timeout",
            response_status=None,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=False,
            error_message="Request timed out"
        )
    
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="error",
            response_status=None,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=False,
            error_message=str(e)
        )


async def check_endpoint_response_time(
    endpoint_url: str,
    http_method: str = "GET",
    max_time_ms: int = 1000,
    auth_token: Optional[str] = None
) -> HealthCheckResponse:
    """
    Check if an endpoint responds within acceptable time limits.
    
    Args:
        endpoint_url: The URL to check
        http_method: HTTP method
        max_time_ms: Maximum acceptable response time in milliseconds
        auth_token: Optional authentication token
    
    Returns:
        HealthCheckResponse with timing information
    """
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
        within_threshold = response_time_ms <= max_time_ms
        
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="within_threshold" if within_threshold else "slow",
            response_status=response.status_code,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=within_threshold,
            error_message=None if within_threshold else f"Response time {response_time_ms:.2f}ms exceeds threshold {max_time_ms}ms"
        )
    
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="error",
            response_status=None,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=False,
            error_message=str(e)
        )


async def check_endpoint_auth(
    endpoint_url: str,
    auth_token: str,
    http_method: str = "GET"
) -> HealthCheckResponse:
    """
    Check if authentication is working correctly for an endpoint.
    
    Args:
        endpoint_url: The URL to check
        auth_token: Authentication token to test
        http_method: HTTP method
    
    Returns:
        HealthCheckResponse with auth status
    """
    start_time = time.time()
    
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if http_method.upper() == "GET":
                response = await client.get(endpoint_url, headers=headers)
            else:
                response = await client.get(endpoint_url, headers=headers)
        
        response_time_ms = (time.time() - start_time) * 1000
        auth_working = response.status_code != 401 and response.status_code != 403
        
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="auth_ok" if auth_working else "auth_failed",
            response_status=response.status_code,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=auth_working,
            error_message=None if auth_working else f"Authentication failed with status {response.status_code}"
        )
    
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="error",
            response_status=None,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=False,
            error_message=str(e)
        )


async def check_endpoint_data_validation(
    endpoint_url: str,
    validation_rules: Dict[str, Any],
    http_method: str = "GET",
    auth_token: Optional[str] = None
) -> HealthCheckResponse:
    """
    Check if endpoint response data matches validation rules.
    
    Args:
        endpoint_url: The URL to check
        validation_rules: Dictionary of validation rules
        http_method: HTTP method
        auth_token: Optional authentication token
    
    Returns:
        HealthCheckResponse with validation status
    """
    start_time = time.time()
    
    try:
        headers = {}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if http_method.upper() == "GET":
                response = await client.get(endpoint_url, headers=headers)
            else:
                response = await client.get(endpoint_url, headers=headers)
        
        response_time_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            return HealthCheckResponse(
                endpoint_url=endpoint_url,
                status="validation_failed",
                response_status=response.status_code,
                response_time_ms=round(response_time_ms, 2),
                is_healthy=False,
                error_message=f"Endpoint returned status {response.status_code}"
            )
        
        response_data = response.json()
        validation_passed = True
        error_messages = []
        
        # Validate response against rules
        for field, rule in validation_rules.items():
            if "required" in rule and rule["required"]:
                if field not in response_data:
                    validation_passed = False
                    error_messages.append(f"Required field '{field}' is missing")
            
            if "type" in rule and field in response_data:
                expected_type = rule["type"]
                actual_type = type(response_data[field]).__name__
                if expected_type != actual_type:
                    validation_passed = False
                    error_messages.append(f"Field '{field}' type mismatch: expected {expected_type}, got {actual_type}")
            
            if "min_value" in rule and field in response_data:
                if response_data[field] < rule["min_value"]:
                    validation_passed = False
                    error_messages.append(f"Field '{field}' value {response_data[field]} below minimum {rule['min_value']}")
            
            if "max_value" in rule and field in response_data:
                if response_data[field] > rule["max_value"]:
                    validation_passed = False
                    error_messages.append(f"Field '{field}' value {response_data[field]} above maximum {rule['max_value']}")
        
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="validation_passed" if validation_passed else "validation_failed",
            response_status=response.status_code,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=validation_passed,
            error_message=None if validation_passed else "; ".join(error_messages)
        )
    
    except Exception as e:
        response_time_ms = (time.time() - start_time) * 1000
        return HealthCheckResponse(
            endpoint_url=endpoint_url,
            status="error",
            response_status=None,
            response_time_ms=round(response_time_ms, 2),
            is_healthy=False,
            error_message=str(e)
        )
