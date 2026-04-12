import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.patients.guardians.models import PatientGuardian
from app.core.patients.guardians.schemas import PatientGuardianCreate

class GuardianService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_guardian(self, patient_id: uuid.UUID, data: PatientGuardianCreate) -> PatientGuardian:
        guardian = PatientGuardian(
            patient_id=patient_id,
            guardian_name=data.guardian_name,
            relationship_type=data.relationship_type,
            phone_number=data.phone_number,
            address=data.address
        )
        self.db.add(guardian)
        await self.db.flush()
        return guardian

    async def list_guardians(self, patient_id: uuid.UUID) -> Sequence[PatientGuardian]:
        stmt = select(PatientGuardian).where(PatientGuardian.patient_id == patient_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
