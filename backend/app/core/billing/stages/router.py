"""Multi-stage Billing Router for Billing Module."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.core.billing.stages.schemas import (
    PartialPaymentCreate, PartialPaymentResponse,
    BillHoldCreate, BillHoldResponse,
    RefundRequestCreate, RefundRequestResponse,
    CreditNoteCreate, CreditNoteResponse,
    DebitNoteCreate, DebitNoteResponse
)
from app.core.billing.stages.services import BillingStagesService

router = APIRouter()


@router.post("/bills/{bill_id}/interim")
async def create_interim_bill(
    bill_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Create an interim bill stage."""
    service = BillingStagesService(db)
    stage = await service.create_interim_bill(bill_id, "system")
    return {"bill_id": bill_id, "stage": stage.stage_type, "stage_id": str(stage.id)}


@router.post("/bills/{bill_id}/intermediate")
async def create_intermediate_bill(
    bill_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Create an intermediate bill stage."""
    service = BillingStagesService(db)
    stage = await service.create_intermediate_bill(bill_id, "system")
    return {"bill_id": bill_id, "stage": stage.stage_type, "stage_id": str(stage.id)}


@router.post("/bills/{bill_id}/final")
async def create_final_bill(
    bill_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Create a final bill stage."""
    service = BillingStagesService(db)
    stage = await service.create_final_bill(bill_id, "system")
    return {"bill_id": bill_id, "stage": stage.stage_type, "stage_id": str(stage.id)}


@router.post("/bills/{bill_id}/partial-payment", response_model=PartialPaymentResponse)
async def process_partial_payment(
    bill_id: str,
    payment_data: PartialPaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Process a partial payment on a bill."""
    service = BillingStagesService(db)
    return await service.process_partial_payment(bill_id, payment_data, "system")


@router.post("/bills/{bill_id}/hold", response_model=BillHoldResponse)
async def set_bill_on_hold(
    bill_id: str,
    hold_data: BillHoldCreate,
    db: AsyncSession = Depends(get_db)
):
    """Set a bill on hold."""
    service = BillingStagesService(db)
    return await service.set_bill_on_hold(bill_id, hold_data, "system")


@router.post("/bills/{bill_id}/release-hold")
async def release_bill_hold(bill_id: str, db: AsyncSession = Depends(get_db)):
    """Release a bill from hold."""
    service = BillingStagesService(db)
    success = await service.release_bill_hold(bill_id, "system")
    if not success:
        raise HTTPException(status_code=404, detail="No active hold found for this bill")
    return {"success": True}


@router.post("/bills/{bill_id}/refund", response_model=RefundRequestResponse)
async def process_refund(
    bill_id: str,
    refund_data: RefundRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """Process a refund request."""
    service = BillingStagesService(db)
    return await service.process_refund(bill_id, refund_data, "system")


@router.post("/bills/{bill_id}/credit-note", response_model=CreditNoteResponse)
async def create_credit_note(
    bill_id: str,
    credit_data: CreditNoteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a credit note."""
    service = BillingStagesService(db)
    return await service.create_credit_note(bill_id, credit_data, "system")


@router.post("/bills/{bill_id}/debit-note", response_model=DebitNoteResponse)
async def create_debit_note(
    bill_id: str,
    debit_data: DebitNoteCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a debit note."""
    service = BillingStagesService(db)
    return await service.create_debit_note(bill_id, debit_data, "system")


@router.post("/bills/{bill_id}/cancel")
async def cancel_bill(bill_id: str, db: AsyncSession = Depends(get_db)):
    """Cancel a bill."""
    service = BillingStagesService(db)
    success = await service.cancel_bill(bill_id, "system")
    return {"success": True, "bill_id": bill_id}


@router.post("/bills/{bill_id}/change-stage")
async def change_bill_stage(
    bill_id: str,
    to_stage: str,
    reason: str,
    db: AsyncSession = Depends(get_db)
):
    """Change bill stage manually."""
    service = BillingStagesService(db)
    stage = await service.change_bill_stage(bill_id, to_stage, reason, "system")
    return {"bill_id": bill_id, "stage": stage.stage_type, "stage_id": str(stage.id)}
