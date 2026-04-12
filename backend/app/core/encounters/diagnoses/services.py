import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.encounters.diagnoses.models import EncounterDiagnosis
from app.core.encounters.diagnoses.schemas import EncounterDiagnosisCreate

class DiagnosisService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_diagnosis(self, encounter_id: uuid.UUID, data: EncounterDiagnosisCreate) -> EncounterDiagnosis:
        diagnosis = EncounterDiagnosis(
            encounter_id=encounter_id,
            diagnosis_code=data.diagnosis_code,
            diagnosis_description=data.diagnosis_description,
            diagnosis_type=data.diagnosis_type
        )
        self.db.add(diagnosis)
        await self.db.flush()
        return diagnosis

    async def list_diagnoses(self, encounter_id: uuid.UUID) -> Sequence[EncounterDiagnosis]:
        stmt = select(EncounterDiagnosis).where(EncounterDiagnosis.encounter_id == encounter_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
