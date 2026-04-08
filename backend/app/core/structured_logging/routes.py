from fastapi import APIRouter, Request
from typing import Optional

from app.core.structured_logging.config import (
    get_correlation_id,
    get_request_id,
    get_user_id,
    get_tenant_id
)

router = APIRouter(prefix="/logging", tags=["logging"])


@router.get("/context")
async def get_logging_context(request: Request):
    """Get current logging context for debugging."""
    return {
        "correlation_id": get_correlation_id(),
        "request_id": get_request_id(),
        "user_id": get_user_id(),
        "tenant_id": get_tenant_id(),
        "path": request.url.path,
        "method": request.method
    }
