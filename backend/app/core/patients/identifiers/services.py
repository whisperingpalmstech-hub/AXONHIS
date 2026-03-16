import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.patients.identifiers.models import PatientIdentifier
from app.core.patients.identifiers.schemas import PatientIdentifierCreate

class IdentifierService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_identifier(self, patient_id: uuid.UUID, data: PatientIdentifierCreate) -> PatientIdentifier:
        identifier = PatientIdentifier(
            patient_id=patient_id,
            identifier_type=data.identifier_type,
            identifier_value=data.identifier_value,
            issuing_authority=data.issuing_authority
        )
        self.db.add(identifier)
        await self.db.flush()
        return identifier

    async def list_identifiers(self, patient_id: uuid.UUID) -> Sequence[PatientIdentifier]:
        stmt = select(PatientIdentifier).where(PatientIdentifier.patient_id == patient_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
