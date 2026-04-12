import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.encounters.clinical_flags.models import ClinicalFlag
from app.core.encounters.clinical_flags.schemas import ClinicalFlagCreate

class ClinicalFlagService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_flag(self, patient_id: uuid.UUID, data: ClinicalFlagCreate) -> ClinicalFlag:
        flag = ClinicalFlag(
            patient_id=patient_id,
            flag_type=data.flag_type,
            flag_description=data.flag_description
        )
        self.db.add(flag)
        await self.db.flush()
        return flag

    async def get_patient_flags(self, patient_id: uuid.UUID) -> Sequence[ClinicalFlag]:
        stmt = select(ClinicalFlag).where(ClinicalFlag.patient_id == patient_id).order_by(ClinicalFlag.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
