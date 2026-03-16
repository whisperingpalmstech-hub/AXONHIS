"""Notification router – user notification management."""
import uuid

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from app.core.notifications.services import NotificationService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/notifications", tags=["notifications"])


class NotificationOut(BaseModel):
    id: uuid.UUID
    notification_type: str
    channel: str
    title: str
    message: str
    status: str
    link: str | None
    created_at: datetime
    read_at: datetime | None

    model_config = {"from_attributes": True}


class NotificationListOut(BaseModel):
    total: int
    unread_count: int
    items: list[NotificationOut]


@router.get("", response_model=NotificationListOut)
async def list_notifications(
    db: DBSession, user: CurrentUser,
    status: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100),
) -> NotificationListOut:
    service = NotificationService(db)
    notifications, total = await service.get_for_user(user.id, status=status, skip=skip, limit=limit)
    unread = await service.get_unread_count(user.id)
    return NotificationListOut(
        total=total, unread_count=unread,
        items=[NotificationOut.model_validate(n) for n in notifications],
    )


@router.get("/unread-count")
async def unread_count(db: DBSession, user: CurrentUser) -> dict:
    count = await NotificationService(db).get_unread_count(user.id)
    return {"unread_count": count}


@router.put("/{notification_id}/read", status_code=204)
async def mark_read(notification_id: uuid.UUID, db: DBSession, _: CurrentUser) -> None:
    success = await NotificationService(db).mark_read(notification_id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")


@router.put("/read-all", status_code=204)
async def mark_all_read(db: DBSession, user: CurrentUser) -> None:
    await NotificationService(db).mark_all_read(user.id)
