from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import uuid

from app.core.structured_logging.config import (
    set_correlation_id,
    set_request_id,
    set_user_id,
    set_tenant_id,
    get_logger,
    clear_context
)


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs and structured logging to requests."""
    
    async def dispatch(self, request: Request, call_next: Callable):
        # Generate IDs
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        request_id = str(uuid.uuid4())
        
        # Set context
        set_correlation_id(correlation_id)
        set_request_id(request_id)
        
        # Extract user/tenant from headers if present
        user_id = request.headers.get("X-User-ID")
        tenant_id = request.headers.get("X-Tenant-ID")
        
        if user_id:
            set_user_id(user_id)
        if tenant_id:
            set_tenant_id(tenant_id)
        
        logger = get_logger("request")
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            client_host=request.client.host if request.client else None
        )
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Request-ID"] = request_id
        
        logger.info(
            f"Request completed: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code
        )
        
        # Clear context
        clear_context()
        
        return response
