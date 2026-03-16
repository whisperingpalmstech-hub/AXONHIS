"""Pharmacy router – dispense medication and query stock."""
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.pharmacy.models import Dispense, Medication, Stock
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


class DispenseCreate(BaseModel):
    order_id: uuid.UUID
    medication_id: uuid.UUID
    patient_id: uuid.UUID
    quantity: int
    notes: str | None = None


class DispenseOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    medication_id: uuid.UUID
    patient_id: uuid.UUID
    quantity: int
    dispensed_at: str
    notes: str | None

    model_config = {"from_attributes": True}


class MedicationOut(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    generic_name: str | None
    category: str
    form: str
    strength: str | None
    unit_price: float

    model_config = {"from_attributes": True}


@router.get("/medications", response_model=list[MedicationOut])
async def list_medications(db: DBSession, _: CurrentUser) -> list[MedicationOut]:
    result = await db.execute(select(Medication).where(Medication.is_active == True))
    return [MedicationOut.model_validate(m) for m in result.scalars().all()]


@router.post("/dispense", response_model=DispenseOut, status_code=201)
async def dispense_medication(
    data: DispenseCreate, db: DBSession, user: CurrentUser
) -> DispenseOut:
    dispense = Dispense(**data.model_dump(), dispensed_by=user.id)
    db.add(dispense)
    await db.flush()
    await EventService(db).emit(
        EventType.MEDICATION_DISPENSED,
        summary="Medication dispensed",
        patient_id=data.patient_id,
        actor_id=user.id,
        payload={"dispense_id": str(dispense.id), "order_id": str(data.order_id)},
    )
    return DispenseOut.model_validate(dispense)
