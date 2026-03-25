import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from .schemas import (
    SalesReturnCreate, SalesReturnOut, ProcessRefundRequest,
    ReturnLogOut, ReturnReasonOut
)
from .services import SalesReturnsService

router = APIRouter(prefix="/sales-returns", tags=["Pharmacy Sales Returns"])


async def get_svc(db: AsyncSession = Depends(get_db)):
    return SalesReturnsService(db)


# ── List Returns ──────────────────────────────────────────────────────
@router.get("", response_model=list[SalesReturnOut])
async def list_returns(
    status: str = Query(None),
    svc: SalesReturnsService = Depends(get_svc),
):
    return await svc.list_returns(status)


# ── Get Single Return ─────────────────────────────────────────────────
@router.get("/{return_id}", response_model=SalesReturnOut)
async def get_return(
    return_id: uuid.UUID,
    svc: SalesReturnsService = Depends(get_svc),
):
    return await svc.get_return(return_id)


# ── Create Return ─────────────────────────────────────────────────────
@router.post("", response_model=SalesReturnOut)
async def create_return(
    data: SalesReturnCreate,
    svc: SalesReturnsService = Depends(get_svc),
):
    return await svc.create_return(data)


# ── Process Refund ────────────────────────────────────────────────────
@router.post("/{return_id}/refund")
async def process_refund(
    return_id: uuid.UUID,
    data: ProcessRefundRequest,
    svc: SalesReturnsService = Depends(get_svc),
):
    ret = await svc.process_refund(return_id, data)
    return {"status": "success", "message": "Refund processed successfully", "return_id": str(ret.id)}


# ── Audit Logs ────────────────────────────────────────────────────────
@router.get("/{return_id}/audit", response_model=list[ReturnLogOut])
async def get_audit_logs(
    return_id: uuid.UUID,
    svc: SalesReturnsService = Depends(get_svc),
):
    return await svc.get_audit_logs(return_id)


# ── Return Reasons ────────────────────────────────────────────────────
@router.get("/config/reasons", response_model=list[ReturnReasonOut])
async def list_reasons(svc: SalesReturnsService = Depends(get_svc)):
    return await svc.list_reasons()


# ── Seed Reasons ──────────────────────────────────────────────────────
@router.post("/config/seed-reasons")
async def seed_reasons(svc: SalesReturnsService = Depends(get_svc)):
    await svc.seed_reasons()
    return {"status": "success", "message": "Return reasons seeded"}


# ── Search Bills ──────────────────────────────────────────────────────
@router.get("/bills/search")
async def search_bills(
    query: str = Query(""),
    svc: SalesReturnsService = Depends(get_svc),
):
    return await svc.search_bills(query)


# ── Seed Mock Return ──────────────────────────────────────────────────
@router.post("/seed-mock")
async def seed_mock_return(svc: SalesReturnsService = Depends(get_svc)):
    """Create a mock return for testing."""
    data = SalesReturnCreate(
        bill_number="BILL-TEST-001",
        patient_name="Rahul Sharma",
        uhid="UHID1234",
        mobile="9876543210",
        sale_date=datetime.now(timezone.utc),
        notes="Test return",
        items=[
            {
                "medication_name": "Paracetamol 650mg",
                "quantity_sold": 10,
                "quantity_returned": 4,
                "unit_price": 20.00,
                "reason_text": "Unused medication",
            },
            {
                "medication_name": "Amoxicillin 500mg",
                "quantity_sold": 5,
                "quantity_returned": 2,
                "unit_price": 45.00,
                "reason_text": "Dosage changed by doctor",
            },
        ]
    )
    ret = await svc.create_return(data)
    return {"status": "success", "return_id": str(ret.id), "return_number": ret.return_number}
