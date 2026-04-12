"""Integration Module — API Routes. Connects all modules."""
import uuid
from typing import List, Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import CurrentUser
from .schemas import *
from .services import *

router = APIRouter(prefix="/integration", tags=["Cross-Module Integration"])

# ── Charge Posting ───────────────────────────
@router.post("/charges", response_model=ChargePostingOut)
async def post_charge(data: ChargePostingCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    """Post a charge from any clinical module (lab, pharmacy, radiology, etc.) to billing."""
    name = getattr(user, 'full_name', None) or getattr(user, 'email', 'Staff')
    return await ChargePostingService(db).post_charge(data, user.id, str(name), user.org_id)

@router.get("/charges/{patient_id}/{encounter_id}", response_model=List[ChargePostingOut])
async def get_patient_charges(patient_id: uuid.UUID, encounter_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ChargePostingService(db).get_charges(patient_id, encounter_id, user.org_id)

@router.delete("/charges/{charge_id}")
async def cancel_charge(charge_id: uuid.UUID, reason: str = "Cancelled", user: CurrentUser = None, db: AsyncSession = Depends(get_db)):
    return await ChargePostingService(db).cancel_charge(charge_id, reason, user.org_id)

@router.get("/charges/{patient_id}/{encounter_id}/unbilled-total")
async def get_unbilled_total(patient_id: uuid.UUID, encounter_id: uuid.UUID, user: CurrentUser = None, db: AsyncSession = Depends(get_db)):
    total = await ChargePostingService(db).get_unbilled_total(patient_id, encounter_id, user.org_id)
    return {"unbilled_total": float(total)}

# ── Patient Ledger ───────────────────────────
@router.get("/ledger/{patient_id}/{encounter_id}", response_model=PatientLedgerOut)
async def get_patient_ledger(patient_id: uuid.UUID, encounter_id: uuid.UUID, user: CurrentUser = None, db: AsyncSession = Depends(get_db)):
    ledger = await PatientLedgerService(db).get_ledger(patient_id, encounter_id, user.org_id)
    if not ledger: raise HTTPException(404, "No ledger for this encounter")
    return ledger

@router.post("/ledger/{patient_id}/{encounter_id}/payment", response_model=PatientLedgerOut)
async def record_payment(patient_id: uuid.UUID, encounter_id: uuid.UUID, amount: Decimal, user: CurrentUser = None, db: AsyncSession = Depends(get_db)):
    return await PatientLedgerService(db).record_payment(patient_id, encounter_id, amount, user.org_id)

@router.post("/ledger/{patient_id}/{encounter_id}/deposit", response_model=PatientLedgerOut)
async def record_deposit(patient_id: uuid.UUID, encounter_id: uuid.UUID, amount: Decimal, user: CurrentUser = None, db: AsyncSession = Depends(get_db)):
    return await PatientLedgerService(db).record_deposit(patient_id, encounter_id, amount, user.org_id)

# ── ER → IPD Transfer ───────────────────────
@router.post("/er-to-ipd")
async def transfer_er_to_ipd(data: ERToIPDTransferRequest, user: CurrentUser = None, db: AsyncSession = Depends(get_db)):
    """Transfer a patient from ER to IPD admission."""
    return await ERToIPDTransferService(db).transfer(data, user.id, user.org_id)

# ── Cross-Module Events ─────────────────────
@router.get("/events", response_model=List[CrossModuleEventOut])
async def get_integration_events(user: CurrentUser = None, source_module: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return await IntegrationEventService(db).get_events(user.org_id, source_module)

# ── Bill Summary (aggregated view) ──────────
@router.get("/bill-summary/{patient_id}/{encounter_id}", response_model=PatientBillSummary)
async def get_bill_summary(patient_id: uuid.UUID, encounter_id: uuid.UUID, user: CurrentUser = None, db: AsyncSession = Depends(get_db)):
    charges = await ChargePostingService(db).get_charges(patient_id, encounter_id, user.org_id)
    ledger = await PatientLedgerService(db).get_ledger(patient_id, encounter_id, user.org_id)
    unbilled = await ChargePostingService(db).get_unbilled_total(patient_id, encounter_id, user.org_id)
    encounter_type = charges[0].encounter_type if charges else "opd"
    return PatientBillSummary(
        patient_id=patient_id, encounter_type=encounter_type, encounter_id=encounter_id,
        charges=charges, ledger=ledger, total_unbilled=unbilled
    )
