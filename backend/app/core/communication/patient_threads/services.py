import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import PatientThread
from .schemas import PatientThreadCreate


class PatientThreadService:
    @staticmethod
    async def get_or_create_thread(db: AsyncSession, patient_id: uuid.UUID, created_by: uuid.UUID) -> PatientThread:
        stmt = select(PatientThread).where(PatientThread.patient_id == patient_id)
        result = await db.execute(stmt)
        thread = result.scalar_one_or_none()
        
        if not thread:
            thread = PatientThread(patient_id=patient_id, created_by=created_by)
            db.add(thread)
            await db.commit()
            await db.refresh(thread)
            
        return thread
