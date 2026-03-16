"""Audit router – query audit logs (read-only, immutable)."""
import uuid
from datetime import datetime

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Any

from app.core.audit.services import AuditService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/audit", tags=["audit"])


class AuditLogOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None
    action: str
    resource_type: str
    resource_id: str
    before_state: dict[str, Any] | None
    after_state: dict[str, Any] | None
    client_ip: str | None
    note: str | None
    occurred_at: datetime

    model_config = {"from_attributes": True}


class AuditLogListOut(BaseModel):
    total: int
    items: list[AuditLogOut]


@router.get("", response_model=AuditLogListOut)
async def query_audit_logs(
    db: DBSession, _: CurrentUser,
    user_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    entity_type: str | None = Query(None),
    entity_id: str | None = Query(None),
    from_date: datetime | None = Query(None),
    to_date: datetime | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=200),
) -> AuditLogListOut:
    """Query audit logs with filters. Logs are immutable."""
    logs, total = await AuditService(db).query(
        user_id=user_id, action=action, entity_type=entity_type,
        entity_id=entity_id, from_date=from_date, to_date=to_date,
        skip=skip, limit=limit,
    )
    return AuditLogListOut(total=total, items=[AuditLogOut.model_validate(l) for l in logs])
