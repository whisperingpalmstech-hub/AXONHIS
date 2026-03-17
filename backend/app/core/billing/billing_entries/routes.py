import uuid
from fastapi import APIRouter, HTTPException
from app.dependencies import DBSession, CurrentUser
from sqlalchemy import select
from .schemas import BillingEntryCreate, BillingEntryOut
from .models import BillingEntry, FinancialAuditLog
from .services import BillingEntryService

router = APIRouter(tags=["billing-entries"])

@router.post("/entries", response_model=BillingEntryOut)
async def create_entry(data: BillingEntryCreate, db: DBSession, user: CurrentUser):
    svc = BillingEntryService(db)
    entry = await svc.create_entry(data, user.id)
    return entry

@router.get("/entries/patient/{patient_id}", response_model=list[BillingEntryOut])
async def get_patient_entries(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    res = await db.execute(select(BillingEntry).where(BillingEntry.patient_id == patient_id))
    return res.scalars().all()

@router.get("/entries", response_model=list[BillingEntryOut])
async def list_entries(db: DBSession, _: CurrentUser):
    res = await db.execute(select(BillingEntry))
    return res.scalars().all()
