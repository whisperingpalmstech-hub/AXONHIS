"""Lab router – result entry and query."""
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.lab.models import LabResult
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/lab", tags=["lab"])


class LabResultCreate(BaseModel):
    order_id: uuid.UUID
    test_id: uuid.UUID
    patient_id: uuid.UUID
    value: str
    unit: str | None = None
    reference_range: str | None = None
    is_abnormal: bool = False
    notes: str | None = None


class LabResultOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    test_id: uuid.UUID
    patient_id: uuid.UUID
    value: str
    unit: str | None
    reference_range: str | None
    is_abnormal: bool
    status: str
    resulted_at: str

    model_config = {"from_attributes": True}


@router.post("/results", response_model=LabResultOut, status_code=201)
async def submit_result(data: LabResultCreate, db: DBSession, user: CurrentUser) -> LabResultOut:
    result = LabResult(**data.model_dump(), resulted_by=user.id)
    db.add(result)
    await db.flush()
    await EventService(db).emit(
        EventType.LAB_RESULT_AVAILABLE,
        summary=f"Lab result submitted for order",
        patient_id=data.patient_id,
        actor_id=user.id,
        payload={"result_id": str(result.id), "order_id": str(data.order_id)},
    )
    return LabResultOut.model_validate(result)


@router.get("/results/patient/{patient_id}", response_model=list[LabResultOut])
async def get_patient_results(patient_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[LabResultOut]:
    stmt = select(LabResult).where(LabResult.patient_id == patient_id).order_by(LabResult.resulted_at.desc())
    results = (await db.execute(stmt)).scalars().all()
    return [LabResultOut.model_validate(r) for r in results]
