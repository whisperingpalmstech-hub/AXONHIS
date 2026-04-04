from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import (
    DiagnosticTemplateCreate,
    DiagnosticTemplateOut,
    DiagnosticProcedureOrderCreate,
    DiagnosticProcedureOrderOut,
    DiagnosticWorkbenchRecordOut,
    DiagnosticResultEntryCreate,
    DiagnosticResultEntryOut,
    DiagnosticValidationCreate,
    DiagnosticValidationOut,
    DiagnosticReportHandoverCreate,
    DiagnosticReportHandoverOut,
    DiagnosticAmendmentLogCreate,
    DiagnosticAmendmentLogOut,
    DiagnosticDashboardMetrics
)
from .services import DiagnosticsService

router = APIRouter(prefix="/api/v1/diagnostics", tags=["Diagnostic Procedures"])

@router.post("/templates", response_model=DiagnosticTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(data: DiagnosticTemplateCreate, db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.create_template(db, data)

@router.get("/templates", response_model=List[DiagnosticTemplateOut])
async def get_templates(db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.get_templates(db)

@router.post("/orders", response_model=DiagnosticProcedureOrderOut, status_code=status.HTTP_201_CREATED)
async def create_procedure_order(data: DiagnosticProcedureOrderCreate, db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.create_order(db, data)

@router.get("/workbench", response_model=List[DiagnosticWorkbenchRecordOut])
async def get_workbench_records(
    patient_name: Optional[str] = Query(None),
    uhid: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    return await DiagnosticsService.get_workbench_records(db, patient_name, uhid, department, status)

@router.post("/workbench/{workbench_id}/accept", response_model=DiagnosticWorkbenchRecordOut)
async def accept_procedure(workbench_id: str, technician_id: str = Query(...), db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.accept_procedure(db, workbench_id, technician_id)

@router.post("/workbench/{workbench_id}/results", response_model=DiagnosticResultEntryOut)
async def enter_results(workbench_id: str, data: DiagnosticResultEntryCreate, db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.enter_results(db, workbench_id, data)

@router.post("/workbench/{workbench_id}/provisional-release", response_model=DiagnosticWorkbenchRecordOut)
async def provisional_release(workbench_id: str, db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.provisional_release(db, workbench_id)

@router.post("/workbench/{workbench_id}/validate", response_model=DiagnosticValidationOut)
async def validate_report(workbench_id: str, data: DiagnosticValidationCreate, db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.validate_report(db, workbench_id, data)

@router.post("/workbench/{workbench_id}/handover", response_model=DiagnosticReportHandoverOut)
async def record_handover(workbench_id: str, data: DiagnosticReportHandoverCreate, db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.record_handover(db, workbench_id, data)

@router.post("/workbench/{workbench_id}/amend", response_model=DiagnosticAmendmentLogOut)
async def amend_report(workbench_id: str, data: DiagnosticAmendmentLogCreate, db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.amend_report(db, workbench_id, data)

@router.get("/dashboard/metrics", response_model=DiagnosticDashboardMetrics)
async def get_dashboard_metrics(db: AsyncSession = Depends(get_db)):
    return await DiagnosticsService.get_dashboard_metrics(db)
