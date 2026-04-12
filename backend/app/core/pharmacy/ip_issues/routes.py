import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db

from .schemas import (
    IPPendingIssueCreate, IPPendingIssueOut,
    IPDispenseSubmission, IPOrderLogOut
)
from .services import IPIssuesService

router = APIRouter(prefix="/ip-issues", tags=["Pharmacy IP Issues"])


async def get_svc(db: AsyncSession = Depends(get_db)):
    return IPIssuesService(db)


# ── List Issues ───────────────────────────────────────────────────────
@router.get("", response_model=list[IPPendingIssueOut])
async def list_issues(
    status: str = Query(None),
    svc: IPIssuesService = Depends(get_svc),
):
    return await svc.list_issues(status)


# ── Get Single Issue ──────────────────────────────────────────────────
@router.get("/{issue_id}", response_model=IPPendingIssueOut)
async def get_issue(
    issue_id: uuid.UUID,
    svc: IPIssuesService = Depends(get_svc),
):
    return await svc.get_issue(issue_id)


# ── Create IP Order (Mock Intake) ─────────────────────────────────────
@router.post("", response_model=IPPendingIssueOut)
async def create_issue(
    data: IPPendingIssueCreate,
    svc: IPIssuesService = Depends(get_svc),
):
    return await svc.create_issue(data)


# ── Dispense Submission ───────────────────────────────────────────────
@router.post("/{issue_id}/dispense")
async def process_dispense(
    issue_id: uuid.UUID,
    submission: IPDispenseSubmission,
    pharmacist_id: str = "00000000-0000-0000-0000-000000000001",  # Mock auth user
    svc: IPIssuesService = Depends(get_svc),
):
    # In a real app we'd fetch current user
    pharmacist_uuid = uuid.UUID(pharmacist_id)
    issue = await svc.process_dispense(issue_id, submission, pharmacist_uuid)
    return {
        "status": "success",
        "message": f"Successfully dispensed items for admission {issue.admission_number}"
    }


# ── Audit Trail ───────────────────────────────────────────────────────
@router.get("/{issue_id}/audit", response_model=list[IPOrderLogOut])
async def get_audit_trail(
    issue_id: uuid.UUID,
    svc: IPIssuesService = Depends(get_svc),
):
    return await svc.get_audit_trail(issue_id)


# ── Multi-Store Inventory Lookup ──────────────────────────────────────
@router.get("/config/multi-store-stock/{drug_id}")
async def check_multi_store_stock(
    drug_id: uuid.UUID,
    svc: IPIssuesService = Depends(get_svc),
):
    return await svc.lookup_stock(drug_id)


# ── Seed Mock Orders ──────────────────────────────────────────────────
@router.post("/seed-mock")
async def seed_mock(svc: IPIssuesService = Depends(get_svc)):
    """Seed test IP orders from Doctor Desk and Nursing Station."""
    mock1 = IPPendingIssueCreate(
        patient_name="Amit Patel",
        uhid="UHID1234",
        admission_number="IP-24-00100",
        ward="Surgical Ward",
        bed_number="Bed 04",
        treating_doctor_name="Dr. Mehta",
        source="Doctor Desk",
        priority="Urgent",
        items=[
            {
                "medication_name": "Ceftriaxone Injection 1g",
                "dosage": "1g",
                "frequency": "BD",
                "route": "IV",
                "prescribed_quantity": 5.0,
                "is_non_formulary": False
            },
            {
                "medication_name": "Paracetamol Infusion",
                "dosage": "1g",
                "frequency": "SOS",
                "route": "IV",
                "prescribed_quantity": 2.0,
                "is_non_formulary": False
            }
        ]
    )

    mock2 = IPPendingIssueCreate(
        patient_name="Sneha Desai",
        uhid="UHID5678",
        admission_number="IP-24-00102",
        ward="ICU",
        bed_number="ICU-02",
        treating_doctor_name="Dr. Gupta",
        source="Nursing Station",
        priority="STAT",
        items=[
            {
                "medication_name": "Noradrenaline 2mg/ml",
                "dosage": "2mg",
                "frequency": "Continuous",
                "route": "IV Infusion",
                "prescribed_quantity": 10.0,
                "is_non_formulary": False
            }
        ]
    )

    await svc.create_issue(mock1)
    await svc.create_issue(mock2)

    return {"status": "success", "message": "Seeded mock IP pending issues."}
