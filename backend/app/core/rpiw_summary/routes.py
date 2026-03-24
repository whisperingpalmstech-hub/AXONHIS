from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.database import get_db

from .schemas import (
    RpiwPatientSummaryOut, RpiwPatientSummaryCreate,
    RpiwSummaryAlertCreate, RpiwSummaryAlertOut,
    RpiwSummaryTaskCreate, RpiwSummaryTaskOut,
    RpiwSummaryVitalCreate, RpiwSummaryVitalOut,
    RpiwSummaryMedicationCreate, RpiwSummaryMedicationOut,
    RpiwCompositeSummary
)
from .services import RPIWSummaryService

router = APIRouter(prefix="/api/v1/rpiw-summary", tags=["RPIW - Patient Summary Engine"])


# ─── Composite Summary View ──────────────────────────────────

@router.get("/{patient_uhid}", response_model=RpiwCompositeSummary)
async def get_patient_summary(
    patient_uhid: str,
    admission_number: Optional[str] = None,
    visit_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get the full 360-degree aggregated patient summary view."""
    svc = RPIWSummaryService(db)
    
    # Check if we should initialize fake data for demo purposes
    summary_obj = await svc.get_or_create_summary(patient_uhid, admission_number, visit_id)
    if summary_obj.chief_issue is None:
        # Pre-seed for the frontend demonstration
        await svc.generate_mock_summary(patient_uhid)
        
    return await svc.get_composite_summary(patient_uhid, admission_number, visit_id)

@router.put("/{summary_id}", response_model=RpiwPatientSummaryOut)
async def update_patient_summary(summary_id: str, body: dict, db: AsyncSession = Depends(get_db)):
    """Update high-level text summaries (Chief Issue, Clinical Status)."""
    svc = RPIWSummaryService(db)
    summary = await svc.update_summary(summary_id, body)
    if not summary:
        raise HTTPException(status_code=404, detail="Summary not found")
    await db.commit()
    return summary


# ─── Alerts & Risks ──────────────────────────────────

@router.post("/{summary_id}/alerts", response_model=RpiwSummaryAlertOut)
async def add_clinical_alert(summary_id: str, data: RpiwSummaryAlertCreate, db: AsyncSession = Depends(get_db)):
    """Engine triggers a critical alert for the summary."""
    svc = RPIWSummaryService(db)
    alert = await svc.add_alert(summary_id, data.model_dump())
    await db.commit()
    return alert

@router.put("/alerts/{alert_id}/resolve", response_model=RpiwSummaryAlertOut)
async def resolve_clinical_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    """Mark an alert as resolved."""
    svc = RPIWSummaryService(db)
    alert = await svc.resolve_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    await db.commit()
    return alert


# ─── Pending Tasks ──────────────────────────────────

@router.post("/{summary_id}/tasks", response_model=RpiwSummaryTaskOut)
async def add_clinical_task(summary_id: str, data: RpiwSummaryTaskCreate, db: AsyncSession = Depends(get_db)):
    """Add an incomplete task tracking item."""
    svc = RPIWSummaryService(db)
    task = await svc.add_task(summary_id, data.model_dump())
    await db.commit()
    return task

@router.put("/tasks/{task_id}/status", response_model=RpiwSummaryTaskOut)
async def update_task_status(task_id: str, status: str, db: AsyncSession = Depends(get_db)):
    """Update task progress (Pending -> Completed)."""
    svc = RPIWSummaryService(db)
    task = await svc.update_task_status(task_id, status)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.commit()
    return task


# ─── Vitals Trends ──────────────────────────────────

@router.post("/{summary_id}/vitals", response_model=RpiwSummaryVitalOut)
async def add_extracted_vital(summary_id: str, data: RpiwSummaryVitalCreate, db: AsyncSession = Depends(get_db)):
    """Extract a vital reading and push it to the summary view."""
    svc = RPIWSummaryService(db)
    vital = await svc.add_vital(summary_id, data.model_dump())
    await db.commit()
    return vital


# ─── Active Medications ──────────────────────────────────

@router.post("/{summary_id}/medications", response_model=RpiwSummaryMedicationOut)
async def add_active_medication(summary_id: str, data: RpiwSummaryMedicationCreate, db: AsyncSession = Depends(get_db)):
    """Add an active medication to the concise summary."""
    svc = RPIWSummaryService(db)
    med = await svc.add_medication(summary_id, data.model_dump())
    await db.commit()
    return med

