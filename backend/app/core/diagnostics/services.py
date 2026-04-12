from datetime import datetime
import uuid
import hashlib
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from fastapi import HTTPException, status

from .models import (
    DiagnosticTemplate,
    DiagnosticProcedureOrder,
    DiagnosticWorkbenchRecord,
    DiagnosticResultEntry,
    DiagnosticValidation,
    DiagnosticReport,
    DiagnosticReportHandover,
    DiagnosticAmendmentLog
)
from .schemas import (
    DiagnosticTemplateCreate,
    DiagnosticProcedureOrderCreate,
    DiagnosticResultEntryCreate,
    DiagnosticValidationCreate,
    DiagnosticReportHandoverCreate,
    DiagnosticAmendmentLogCreate,
    DiagnosticDashboardMetrics
)

class DiagnosticsService:
    @staticmethod
    async def create_template(db: AsyncSession, data: DiagnosticTemplateCreate) -> DiagnosticTemplate:
        template = DiagnosticTemplate(**data.model_dump())
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def get_templates(db: AsyncSession) -> List[DiagnosticTemplate]:
        result = await db.execute(select(DiagnosticTemplate).where(DiagnosticTemplate.is_active == True))
        return list(result.scalars().all())

    @staticmethod
    async def create_order(db: AsyncSession, data: DiagnosticProcedureOrderCreate) -> DiagnosticProcedureOrder:
        order = DiagnosticProcedureOrder(**data.model_dump())
        db.add(order)
        await db.flush()
        
        # When order is created (e.g., from billing or doctor), create workbench record
        workbench = DiagnosticWorkbenchRecord(
            order_id=order.id,
            workflow_state="PENDING_ACCEPTANCE"
        )
        db.add(workbench)
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def get_workbench_records(
        db: AsyncSession,
        patient_name: Optional[str] = None,
        uhid: Optional[str] = None,
        department: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[DiagnosticWorkbenchRecord]:
        query = select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).join(DiagnosticWorkbenchRecord.order)
        if uhid:
            query = query.filter(DiagnosticProcedureOrder.uhid == uhid)
        if department:
            query = query.join(DiagnosticProcedureOrder.template).filter(DiagnosticTemplate.department == department)
        if status:
            query = query.filter(DiagnosticWorkbenchRecord.workflow_state == status)
            
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def accept_procedure(db: AsyncSession, workbench_id: str, technician_id: str) -> DiagnosticWorkbenchRecord:
        res = await db.execute(select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).where(DiagnosticWorkbenchRecord.id == workbench_id))
        record = res.scalars().first()
        if not record:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workbench record not found")
        
        if record.workflow_state != "PENDING_ACCEPTANCE":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Procedure cannot be accepted in its current state")
        
        record.workflow_state = "IN_PROGRESS"
        record.assigned_technician_id = technician_id
        record.start_time = datetime.utcnow()
        await db.commit()
        
        res_reload = await db.execute(select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).where(DiagnosticWorkbenchRecord.id == workbench_id))
        return res_reload.scalars().first()

    @staticmethod
    async def enter_results(db: AsyncSession, workbench_id: str, data: DiagnosticResultEntryCreate) -> DiagnosticResultEntry:
        res = await db.execute(select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).where(DiagnosticWorkbenchRecord.id == workbench_id))
        record = res.scalars().first()
        if not record or record.workflow_state != "IN_PROGRESS":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Procedure is not in IN_PROGRESS state")
        
        entry = DiagnosticResultEntry(workbench_id=workbench_id, **data.model_dump())
        db.add(entry)
        await db.flush()
        return entry

    @staticmethod
    async def provisional_release(db: AsyncSession, workbench_id: str) -> DiagnosticWorkbenchRecord:
        res = await db.execute(select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).where(DiagnosticWorkbenchRecord.id == workbench_id))
        record = res.scalars().first()
        if not record or record.workflow_state != "IN_PROGRESS":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Procedure cannot be provisionally released")
            
        entry_result = await db.execute(select(DiagnosticResultEntry).where(DiagnosticResultEntry.workbench_id == workbench_id))
        entry = entry_result.scalars().first()
        if not entry:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Results must be entered first")
            
        entry.provisional_release_time = datetime.utcnow()
        record.workflow_state = "PROVISIONALLY_RELEASED"
        await db.commit()
        
        res_reload = await db.execute(select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).where(DiagnosticWorkbenchRecord.id == workbench_id))
        return res_reload.scalars().first()

    @staticmethod
    async def validate_report(db: AsyncSession, workbench_id: str, data: DiagnosticValidationCreate) -> DiagnosticValidation:
        res = await db.execute(select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).where(DiagnosticWorkbenchRecord.id == workbench_id))
        record = res.scalars().first()
        if not record or record.workflow_state not in ["PROVISIONALLY_RELEASED", "VALIDATED"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state for validation")
            
        validation = DiagnosticValidation(
            workbench_id=workbench_id,
            digital_signature_hash=hashlib.sha256(f"{data.doctor_id}_{datetime.utcnow().isoformat()}".encode()).hexdigest() if data.action == 'APPROVED' else None,
            **data.model_dump()
        )
        db.add(validation)
        await db.flush()
        
        if data.action == "APPROVED":
            record.workflow_state = "VALIDATED"
            record.assigned_doctor_id = data.doctor_id
            record.completion_time = datetime.utcnow()
            
            # Auto-generate report entry
            report = DiagnosticReport(
                validation_id=validation.id,
                pdf_file_path=f"/exports/diagnostics/doc_summary_{uuid.uuid4()}.pdf",
                qr_code_hash=hashlib.md5(validation.id.encode()).hexdigest(),
                is_latest=True
            )
            db.add(report)
            record.workflow_state = "FINALIZED"
        else:
            record.workflow_state = "IN_PROGRESS" # Send back to tech
            
        await db.commit()
        await db.refresh(validation)
        return validation

    @staticmethod
    async def record_handover(db: AsyncSession, workbench_id: str, data: DiagnosticReportHandoverCreate) -> DiagnosticReportHandover:
        res = await db.execute(select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).where(DiagnosticWorkbenchRecord.id == workbench_id))
        record = res.scalars().first()
        if not record or record.workflow_state != "FINALIZED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only finalized reports can be handed over")
            
        handover = DiagnosticReportHandover(workbench_id=workbench_id, **data.model_dump())
        db.add(handover)
        await db.commit()
        await db.refresh(handover)
        return handover

    @staticmethod
    async def amend_report(db: AsyncSession, workbench_id: str, data: DiagnosticAmendmentLogCreate) -> DiagnosticAmendmentLog:
        res = await db.execute(select(DiagnosticWorkbenchRecord).options(joinedload(DiagnosticWorkbenchRecord.order)).where(DiagnosticWorkbenchRecord.id == workbench_id))
        record = res.scalars().first()
        if not record or record.workflow_state != "FINALIZED":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only finalized reports can be amended")
            
        # Get previous report
        report_res = await db.execute(select(DiagnosticReport).join(DiagnosticValidation).where(DiagnosticValidation.workbench_id == workbench_id, DiagnosticReport.is_latest == True))
        prev_report = report_res.scalars().first()
        if prev_report:
            prev_report.is_latest = False
            
        amendment = DiagnosticAmendmentLog(
            workbench_id=workbench_id,
            previous_report_id=prev_report.id if prev_report else "legacy_none",
            **data.model_dump()
        )
        db.add(amendment)
        
        # Reset workflow to await validation logic or result entry
        record.workflow_state = "PROVISIONALLY_RELEASED"
        await db.commit()
        await db.refresh(amendment)
        return amendment

    @staticmethod
    async def get_dashboard_metrics(db: AsyncSession) -> DiagnosticDashboardMetrics:
        # pending
        res_pending = await db.execute(select(func.count(DiagnosticWorkbenchRecord.id)).where(DiagnosticWorkbenchRecord.workflow_state == "PENDING_ACCEPTANCE"))
        pending = res_pending.scalar() or 0
        
        # in_progress
        res_prog = await db.execute(select(func.count(DiagnosticWorkbenchRecord.id)).where(DiagnosticWorkbenchRecord.workflow_state == "IN_PROGRESS"))
        in_prog = res_prog.scalar() or 0
        
        # awaiting_validation
        res_val = await db.execute(select(func.count(DiagnosticWorkbenchRecord.id)).where(DiagnosticWorkbenchRecord.workflow_state == "PROVISIONALLY_RELEASED"))
        await_val = res_val.scalar() or 0
        
        # completed
        res_comp = await db.execute(select(func.count(DiagnosticWorkbenchRecord.id)).where(DiagnosticWorkbenchRecord.workflow_state == "FINALIZED"))
        completed = res_comp.scalar() or 0
        
        return DiagnosticDashboardMetrics(
            pending_procedures=pending,
            procedures_in_progress=in_prog,
            awaiting_validation=await_val,
            completed_reports=completed,
            average_tat_minutes=45.5 # static for now unless we calculate avg timediff
        )
