"""File storage router – upload, download, list files."""
import uuid

from fastapi import APIRouter, HTTPException, UploadFile, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from datetime import datetime

from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.files.services import FileService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/files", tags=["files"])


class FileOut(BaseModel):
    id: uuid.UUID
    file_name: str
    original_name: str
    file_type: str
    file_size: int
    entity_type: str | None
    entity_id: uuid.UUID | None
    uploaded_by: uuid.UUID | None
    uploaded_at: datetime
    description: str | None

    model_config = {"from_attributes": True}


@router.post("", response_model=FileOut, status_code=201)
async def upload_file(
    file: UploadFile,
    db: DBSession,
    user: CurrentUser,
    entity_type: str | None = Query(None),
    entity_id: uuid.UUID | None = Query(None),
    description: str | None = Query(None),
) -> FileOut:
    """Upload a file and attach it to an entity."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="File name is required")

    data = await file.read()
    if len(data) > 50 * 1024 * 1024:  # 50MB limit
        raise HTTPException(status_code=413, detail="File too large (max 50MB)")

    service = FileService(db)
    record = await service.upload(
        file_data=data,
        original_name=file.filename,
        file_type=file.content_type or "application/octet-stream",
        uploaded_by=user.id,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )

    await EventService(db).emit(
        EventType.FILE_UPLOADED,
        summary=f"File '{file.filename}' uploaded",
        actor_id=user.id,
        payload={"file_id": str(record.id), "entity_type": entity_type},
    )

    return FileOut.model_validate(record)


@router.get("/{file_id}", response_model=FileOut)
async def get_file_info(file_id: uuid.UUID, db: DBSession, _: CurrentUser) -> FileOut:
    record = await FileService(db).get_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    return FileOut.model_validate(record)


@router.get("/{file_id}/download")
async def download_file(file_id: uuid.UUID, db: DBSession, _: CurrentUser):
    """Download file with secure access."""
    service = FileService(db)
    record = await service.get_by_id(file_id)
    if not record:
        raise HTTPException(status_code=404, detail="File not found")

    path = service.get_file_path(record)
    if not path.exists():
        raise HTTPException(status_code=404, detail="File data not found on disk")

    return FileResponse(
        path=str(path),
        media_type=record.file_type,
        filename=record.original_name,
    )


@router.get("/entity/{entity_type}/{entity_id}", response_model=list[FileOut])
async def list_entity_files(
    entity_type: str, entity_id: uuid.UUID, db: DBSession, _: CurrentUser
) -> list[FileOut]:
    files = await FileService(db).get_by_entity(entity_type, entity_id)
    return [FileOut.model_validate(f) for f in files]


@router.delete("/{file_id}", status_code=204)
async def delete_file(file_id: uuid.UUID, db: DBSession, user: CurrentUser) -> None:
    success = await FileService(db).soft_delete(file_id)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
