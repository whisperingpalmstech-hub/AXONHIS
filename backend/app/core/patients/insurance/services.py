import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.patients.insurance.models import PatientInsurance
from app.core.patients.insurance.schemas import PatientInsuranceCreate

class InsuranceService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_insurance(self, patient_id: uuid.UUID, data: PatientInsuranceCreate) -> PatientInsurance:
        insurance = PatientInsurance(
            patient_id=patient_id,
            insurance_provider=data.insurance_provider,
            policy_number=data.policy_number,
            coverage_type=data.coverage_type,
            valid_from=data.valid_from,
            valid_to=data.valid_to
        )
        self.db.add(insurance)
        await self.db.flush()
        return insurance

    async def list_insurance(self, patient_id: uuid.UUID) -> Sequence[PatientInsurance]:
        stmt = select(PatientInsurance).where(PatientInsurance.patient_id == patient_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()
