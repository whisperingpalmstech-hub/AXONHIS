from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db

from .schemas import (
    LabReportOut, SignReportRequest, ReleaseReportRequest,
    BulkReleaseRequest, AmendReportRequest
)
from .services import ReportingService
from .models import LabReport

router = APIRouter(prefix="/reports", tags=["Smart Reporting Engine"])

@router.get("/", response_model=List[LabReportOut])
async def list_reports(
    status: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    patient_uhid: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    reps = await ReportingService.get_reports(db, status, department, patient_uhid)
    return reps

@router.get("/{report_id}", response_model=LabReportOut)
async def get_report_details(report_id: str, db: AsyncSession = Depends(get_db)):
    rep = await ReportingService.get_report_by_id(db, report_id)
    if not rep:
        raise HTTPException(status_code=404, detail="Lab Report not found")
    return rep

@router.put("/{report_id}/sign", response_model=LabReportOut)
async def digitally_sign_report(report_id: str, req: SignReportRequest, db: AsyncSession = Depends(get_db)):
    try:
        updated = await ReportingService.sign_report(db, report_id, req)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{report_id}/release", response_model=LabReportOut)
async def release_individual_report(report_id: str, req: ReleaseReportRequest, db: AsyncSession = Depends(get_db)):
    try:
        updated = await ReportingService.release_report(db, report_id, req)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk-release")
async def release_batch_reports(req: BulkReleaseRequest, db: AsyncSession = Depends(get_db)):
    count = await ReportingService.bulk_release(db, req)
    return {"message": f"Successfully released {count} reports to configured channels."}

@router.put("/{report_id}/amend", response_model=LabReportOut)
async def amend_released_report(report_id: str, req: AmendReportRequest, db: AsyncSession = Depends(get_db)):
    try:
        updated = await ReportingService.amend_report(db, report_id, req)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
