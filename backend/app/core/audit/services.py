"""
Audit services – immutable audit logging for all system actions.

Every mutating action gets an audit record that cannot be modified or deleted.
"""
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.audit.models import AuditLog


class AuditService:
    """Service for recording and querying immutable audit logs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: uuid.UUID | None = None,
        old_value: dict[str, Any] | None = None,
        new_value: dict[str, Any] | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        device_id: str | None = None,
        note: str | None = None,
    ) -> AuditLog:
        """Create an immutable audit log entry."""
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=entity_type,
            resource_id=entity_id,
            before_state=old_value,
            after_state=new_value,
            client_ip=ip_address,
            user_agent=user_agent,
            note=note,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry

    async def query(
        self,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[AuditLog], int]:
        """Query audit logs with filters."""
        stmt = select(AuditLog)

        if user_id:
            stmt = stmt.where(AuditLog.user_id == user_id)
        if action:
            stmt = stmt.where(AuditLog.action == action)
        if entity_type:
            stmt = stmt.where(AuditLog.resource_type == entity_type)
        if entity_id:
            stmt = stmt.where(AuditLog.resource_id == entity_id)
        if from_date:
            stmt = stmt.where(AuditLog.occurred_at >= from_date)
        if to_date:
            stmt = stmt.where(AuditLog.occurred_at <= to_date)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        result = await self.db.execute(
            stmt.order_by(AuditLog.occurred_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total
