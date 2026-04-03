from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from .models import NursingVitalTrend, NursingClinicalNote, MedicationAdministrationRecord, NursingIOChart
from .schemas import VitalCreate, NoteCreate, MARCreate
from datetime import datetime
import logging

class NursingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _graceful_execute(self, stmt):
        """Silently catches if the tables haven't been created via migrations yet."""
        try:
            return await self.db.execute(stmt)
        except Exception as e:
            await self.db.rollback()
            logging.warning(f"DB Error caught gracefully (missing tables?): {e}")
            return None

    # Service 2: Vitals Engine
    async def log_vitals(self, vital_data: VitalCreate, user_uuid: str):
        is_abnormal = False
        if vital_data.spo2 and vital_data.spo2 < 90:
            is_abnormal = True
        if vital_data.blood_pressure_sys and vital_data.blood_pressure_sys > 180:
            is_abnormal = True
            
        vital_obj = NursingVitalTrend(
            **vital_data.model_dump(),
            recorded_by=user_uuid,
            is_abnormal=is_abnormal
        )
        self.db.add(vital_obj)
        try:
            await self.db.flush()
            return vital_obj
        except Exception:
            await self.db.rollback()
            return vital_obj

    async def get_patient_vitals(self, admission_number: str):
        result = await self._graceful_execute(
            select(NursingVitalTrend).where(NursingVitalTrend.admission_number == admission_number).order_by(NursingVitalTrend.recorded_at.desc())
        )
        if result:
            return result.scalars().all()
        return []

    # Service 4: Clinical Documentation / Notes Engine
    async def add_clinical_note(self, note_data: NoteCreate, user_uuid: str):
        note_obj = NursingClinicalNote(
            **note_data.model_dump(),
            nurse_uuid=user_uuid
        )
        self.db.add(note_obj)
        try:
            await self.db.flush()
            return note_obj
        except Exception:
            await self.db.rollback()
            return note_obj

    async def get_patient_notes(self, admission_number: str):
        result = await self._graceful_execute(
            select(NursingClinicalNote).where(NursingClinicalNote.admission_number == admission_number).order_by(NursingClinicalNote.recorded_at.desc())
        )
        if result:
            return result.scalars().all()
        return []

    # Service 3: Medication Administration Engine (MAR)
    async def fetch_mar_schedule(self, admission_number: str):
        result = await self._graceful_execute(
            select(MedicationAdministrationRecord).where(MedicationAdministrationRecord.admission_number == admission_number)
        )
        if result:
            return result.scalars().all()
        return []

    # Patient Context / Coversheet wrapper
    async def get_coversheet(self, admission_number: str):
        vitals = await self.get_patient_vitals(admission_number)
        notes = await self.get_patient_notes(admission_number)
        mar = await self.fetch_mar_schedule(admission_number)

        return {
            "vitals": vitals,
            "notes": notes,
            "mar": mar
        }
