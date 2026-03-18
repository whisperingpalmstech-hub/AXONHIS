import uuid
from fastapi import APIRouter, status
from app.dependencies import DBSession, CurrentUser
from .schemas import MessageCreate, MessageOut
from .services import MessageService

router = APIRouter(prefix="/message", tags=["Communication - Messages"])

@router.post("/", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(data: MessageCreate, db: DBSession, user: CurrentUser) -> MessageOut:
    return await MessageService.send_message(db, data, sender_id=user.id)

@router.get("/{other_user_id}", response_model=list[MessageOut])
async def get_messages(other_user_id: uuid.UUID, db: DBSession, user: CurrentUser) -> list[MessageOut]:
    return await MessageService.get_messages(db, user.id, other_user_id)

@router.put("/{message_id}/read", response_model=MessageOut)
async def mark_message_read(message_id: uuid.UUID, db: DBSession, _: CurrentUser) -> MessageOut:
    return await MessageService.mark_read(db, message_id)
