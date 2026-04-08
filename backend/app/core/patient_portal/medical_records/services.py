import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from datetime import datetime

from app.core.lab.models import LabOrder, LabResult, LabTest
from app.core.pharmacy.prescriptions.models import Prescription, PrescriptionItem
from app.core.encounters.encounters.models import Encounter
from .models import PatientDocument

class MedicalRecordService:
    @staticmethod
    async def get_patient_lab_records(db: AsyncSession, patient_id: uuid.UUID):
        """Fetch all lab results for a patient."""
        query = (
            select(LabResult)
            .where(LabResult.patient_id == patient_id)
            .order_by(LabResult.entered_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_patient_prescriptions(db: AsyncSession, patient_id: uuid.UUID):
        """Fetch all prescriptions for a patient."""
        query = (
            select(Prescription)
            .where(Prescription.patient_id == patient_id)
            .options(joinedload(Prescription.items))
            .order_by(Prescription.prescription_time.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_patient_encounters(db: AsyncSession, patient_id: uuid.UUID):
        """Fetch all clinical encounters for a patient."""
        query = (
            select(Encounter)
            .where(Encounter.patient_id == patient_id)
            .order_by(Encounter.created_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_patient_documents(db: AsyncSession, patient_id: uuid.UUID):
        """Fetch uploaded documents for a patient."""
        query = (
            select(PatientDocument)
            .where(PatientDocument.patient_id == patient_id)
            .order_by(PatientDocument.uploaded_at.desc())
        )
        result = await db.execute(query)
        return result.scalars().all()
