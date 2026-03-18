import uuid
from fastapi import APIRouter, status
from app.dependencies import DBSession, CurrentUser
from .schemas import ChannelCreate, ChannelOut, ChannelMessageCreate, ChannelMessageOut
from .services import ChannelService

router = APIRouter(prefix="/channel", tags=["Communication - Channels"])

@router.post("/", response_model=ChannelOut, status_code=status.HTTP_201_CREATED)
async def create_channel(data: ChannelCreate, db: DBSession, user: CurrentUser) -> ChannelOut:
    return await ChannelService.create_channel(db, data, created_by=user.id)

@router.get("/", response_model=list[ChannelOut])
async def get_channels(db: DBSession, _: CurrentUser) -> list[ChannelOut]:
    return await ChannelService.get_channels(db)

@router.get("/{channel_id}", response_model=ChannelOut)
async def get_channel(channel_id: uuid.UUID, db: DBSession, _: CurrentUser) -> ChannelOut:
    return await ChannelService.get_channel(db, channel_id)

@router.post("/message", response_model=ChannelMessageOut, status_code=status.HTTP_201_CREATED)
async def send_channel_message(data: ChannelMessageCreate, db: DBSession, user: CurrentUser) -> ChannelMessageOut:
    return await ChannelService.send_message(db, data, sender_id=user.id)

@router.get("/{channel_id}/messages", response_model=list[ChannelMessageOut])
async def get_channel_messages(channel_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[ChannelMessageOut]:
    return await ChannelService.get_messages(db, channel_id)
