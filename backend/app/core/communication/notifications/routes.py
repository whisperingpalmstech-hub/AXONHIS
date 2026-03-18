import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import NotificationOut
from .services import NotificationService

router = APIRouter(prefix="/notification", tags=["Communication - Notifications"])

@router.get("/", response_model=list[NotificationOut])
async def get_my_notifications(db: DBSession, user: CurrentUser) -> list[NotificationOut]:
    return await NotificationService.get_user_notifications(db, user.id)

@router.put("/{notification_id}/read", response_model=NotificationOut)
async def mark_read(notification_id: uuid.UUID, db: DBSession, _: CurrentUser) -> NotificationOut:
    return await NotificationService.mark_as_read(db, notification_id)
