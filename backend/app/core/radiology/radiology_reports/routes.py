import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import RadiologyReportCreate, RadiologyReportOut
from .services import RadiologyReportService
from typing import List

router = APIRouter()

@router.post("/report", response_model=RadiologyReportOut)
async def create_radiology_report(data: RadiologyReportCreate, db: DBSession, user: CurrentUser):
    return await RadiologyReportService(db).create_draft(data, user.id)

@router.get("/report/{report_id}", response_model=RadiologyReportOut)
async def get_radiology_report(report_id: uuid.UUID, db: DBSession, user: CurrentUser):
    return await RadiologyReportService(db).get_report_by_id(report_id)

@router.put("/report/{report_id}/finalize", response_model=RadiologyReportOut)
async def finalize_radiology_report(report_id: uuid.UUID, impression: str, critical_flag: bool, db: DBSession, user: CurrentUser):
    return await RadiologyReportService(db).finalize_report(report_id, impression, critical_flag, user.id)

from pydantic import BaseModel
class StatusUpdate(BaseModel):
    status: str

@router.put("/reports/{report_id}/status")
async def update_report_status(report_id: uuid.UUID, data: StatusUpdate, db: DBSession, user: CurrentUser):
    from sqlalchemy import update
    from app.core.radiology.radiology_reports.models import RadiologyReport
    await db.execute(update(RadiologyReport).where(RadiologyReport.id == report_id).values(status=data.status))
    await db.commit()
    return {"message": "Status updated successfully"}

@router.get("/reports", response_model=List[RadiologyReportOut])
async def list_radiology_reports(db: DBSession, user: CurrentUser, skip: int = 0, limit: int = 100):
    return await RadiologyReportService(db).list_reports(skip, limit)
