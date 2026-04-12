"""
File storage service – local filesystem in dev, S3-compatible in production.
"""
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.files.models import File

UPLOAD_DIR = Path("/app/uploads") if settings.app_env != "development" else Path("./uploads")


class FileService:
    """Manages file uploads and secure access."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def upload(
        self,
        file_data: bytes,
        original_name: str,
        file_type: str,
        uploaded_by: uuid.UUID | None = None,
        entity_type: str | None = None,
        entity_id: uuid.UUID | None = None,
        description: str | None = None,
    ) -> File:
        """Store a file and record metadata in database."""
        # Generate unique filename
        ext = Path(original_name).suffix
        file_name = f"{uuid.uuid4().hex}{ext}"
        storage_dir = UPLOAD_DIR / datetime.now(timezone.utc).strftime("%Y/%m/%d")
        storage_dir.mkdir(parents=True, exist_ok=True)
        storage_path = storage_dir / file_name

        # Write file
        with open(storage_path, "wb") as f:
            f.write(file_data)

        # Record metadata
        file_record = File(
            file_name=file_name,
            original_name=original_name,
            file_type=file_type,
            file_size=len(file_data),
            storage_path=str(storage_path),
            storage_backend="local",
            entity_type=entity_type,
            entity_id=entity_id,
            uploaded_by=uploaded_by,
            description=description,
        )
        self.db.add(file_record)
        await self.db.flush()
        return file_record

    async def get_by_id(self, file_id: uuid.UUID) -> File | None:
        result = await self.db.execute(select(File).where(File.id == file_id, File.is_deleted == False))
        return result.scalar_one_or_none()

    async def get_by_entity(self, entity_type: str, entity_id: uuid.UUID) -> list[File]:
        result = await self.db.execute(
            select(File).where(
                File.entity_type == entity_type,
                File.entity_id == entity_id,
                File.is_deleted == False,
            ).order_by(File.uploaded_at.desc())
        )
        return list(result.scalars().all())

    async def soft_delete(self, file_id: uuid.UUID) -> bool:
        file = await self.get_by_id(file_id)
        if file:
            file.is_deleted = True
            await self.db.flush()
            return True
        return False

    def get_file_path(self, file_record: File) -> Path:
        """Get the filesystem path for reading a file."""
        return Path(file_record.storage_path)
