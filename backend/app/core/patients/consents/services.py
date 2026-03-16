import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.patients.consents.models import PatientConsent
from app.core.patients.consents.schemas import PatientConsentCreate

class ConsentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_consent(self, patient_id: uuid.UUID, data: PatientConsentCreate) -> PatientConsent:
        consent = PatientConsent(
            patient_id=patient_id,
            consent_type=data.consent_type,
            consent_text=data.consent_text
        )
        self.db.add(consent)
        await self.db.flush()
        return consent

    async def list_consents(self, patient_id: uuid.UUID) -> Sequence[PatientConsent]:
        stmt = select(PatientConsent).where(PatientConsent.patient_id == patient_id).order_by(PatientConsent.signed_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()
