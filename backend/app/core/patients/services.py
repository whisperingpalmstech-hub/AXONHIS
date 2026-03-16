"""Patient services – CRUD with MRN generation and fuzzy search."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.patients.models import Patient
from app.core.patients.schemas import PatientCreate, PatientUpdate


def _generate_mrn() -> str:
    """Generate a unique MRN: MRN-YYYYMMDD-XXXXX."""
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    suffix = uuid.uuid4().hex[:5].upper()
    return f"MRN-{today}-{suffix}"


class PatientService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, data: PatientCreate) -> Patient:
        patient = Patient(**data.model_dump(), mrn=_generate_mrn())
        self.db.add(patient)
        await self.db.flush()
        return patient

    async def get_by_id(self, patient_id: uuid.UUID) -> Patient | None:
        result = await self.db.execute(select(Patient).where(Patient.id == patient_id))
        return result.scalar_one_or_none()

    async def get_by_mrn(self, mrn: str) -> Patient | None:
        result = await self.db.execute(select(Patient).where(Patient.mrn == mrn))
        return result.scalar_one_or_none()

    async def update(self, patient: Patient, data: PatientUpdate) -> Patient:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(patient, field, value)
        await self.db.flush()
        return patient

    async def search(self, query: str, skip: int = 0, limit: int = 20) -> tuple[list[Patient], int]:
        """Search patients by name or MRN (case-insensitive partial match)."""
        like = f"%{query.lower()}%"
        stmt = select(Patient).where(
            or_(
                func.lower(Patient.first_name).like(like),
                func.lower(Patient.last_name).like(like),
                func.lower(Patient.mrn).like(like),
                func.lower(Patient.phone).like(like),
            )
        )
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()
        result = await self.db.execute(stmt.offset(skip).limit(limit))
        return list(result.scalars().all()), total

    async def list_all(self, skip: int = 0, limit: int = 20) -> tuple[list[Patient], int]:
        count_result = await self.db.execute(select(func.count(Patient.id)))
        total = count_result.scalar_one()
        result = await self.db.execute(select(Patient).offset(skip).limit(limit))
        return list(result.scalars().all()), total
