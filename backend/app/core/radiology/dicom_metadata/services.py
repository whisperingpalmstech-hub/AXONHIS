import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import DICOMMetadata
from .schemas import DICOMMetadataCreate

class DICOMMetadataService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_metadata(self, data: DICOMMetadataCreate) -> DICOMMetadata:
        metadata = DICOMMetadata(**data.model_dump())
        self.db.add(metadata)
        await self.db.flush()
        return metadata

    async def get_by_study_uid(self, study_uid: str) -> list[DICOMMetadata]:
        result = await self.db.execute(select(DICOMMetadata).where(DICOMMetadata.study_uid == study_uid))
        return list(result.scalars().all())
