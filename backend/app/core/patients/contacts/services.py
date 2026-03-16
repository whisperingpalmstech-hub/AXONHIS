import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.patients.contacts.models import PatientContact
from app.core.patients.contacts.schemas import PatientContactCreate

class ContactService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_contact(self, patient_id: uuid.UUID, data: PatientContactCreate) -> PatientContact:
        contact = PatientContact(
            patient_id=patient_id,
            contact_type=data.contact_type,
            contact_value=data.contact_value,
            is_primary=data.is_primary
        )
        self.db.add(contact)
        await self.db.flush()
        return contact

    async def list_contacts(self, patient_id: uuid.UUID) -> Sequence[PatientContact]:
        stmt = select(PatientContact).where(PatientContact.patient_id == patient_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
