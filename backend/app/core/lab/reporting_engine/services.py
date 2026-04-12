from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, func
from datetime import datetime
from typing import List, Dict, Any, Optional

from .models import LabReport, ReportRelease, ReportVersion, ReportAuditLog, ReportCommentTemplate
from .schemas import SignReportRequest, ReleaseReportRequest, BulkReleaseRequest, AmendReportRequest

class ReportingService:
    @staticmethod
    async def get_reports(db: AsyncSession, status: Optional[str] = None, department: Optional[str] = None, patient_uhid: Optional[str] = None) -> List[LabReport]:
        q = select(LabReport)
        if status:
            q = q.where(LabReport.status == status)
        if department:
            q = q.where(LabReport.department == department)
        if patient_uhid:
            q = q.where(LabReport.patient_uhid == patient_uhid)
            
        result = await db.execute(q.order_by(LabReport.created_at.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_report_by_id(db: AsyncSession, rep_id: str) -> Optional[LabReport]:
        q = select(LabReport).where(LabReport.id == rep_id)
        result = await db.execute(q)
        return result.scalars().first()
        
    @staticmethod
    async def log_audit(db: AsyncSession, report_id: str, action: str, actor_id: str, actor_name: str, details: Dict = None):
        log = ReportAuditLog(
            report_id=report_id, action_type=action, actor_id=actor_id, actor_name=actor_name, details=details
        )
        db.add(log)

    @staticmethod
    async def sign_report(db: AsyncSession, report_id: str, req: SignReportRequest) -> LabReport:
        rep = await ReportingService.get_report_by_id(db, report_id)
        if not rep: raise ValueError("Report not found.")
        if rep.status != "PENDING_RELEASE": raise ValueError("Report is not ready for signature.")
        
        rep.is_signed = True
        rep.signed_by_id = req.signer_id
        rep.signed_by_name = req.signer_name
        rep.signed_by_designation = req.signer_designation
        rep.signed_at = datetime.utcnow()
        # Remains PENDING_RELEASE until explicitly released. But allows it to be released now.
        
        await ReportingService.log_audit(db, rep.id, "SIGNED", req.signer_id, req.signer_name, {"designation": req.signer_designation})
        await db.commit()
        await db.refresh(rep)
        return rep

    @staticmethod
    async def release_report(db: AsyncSession, report_id: str, req: ReleaseReportRequest) -> LabReport:
        rep = await ReportingService.get_report_by_id(db, report_id)
        if not rep: raise ValueError("Report not found.")
        if not rep.is_signed: raise ValueError("Report must be digitally signed before release.")
        if rep.status == "RELEASED": raise ValueError("Report is already released.")
        
        rep.status = "RELEASED"
        
        release = ReportRelease(
            report_id=rep.id,
            released_by_id=req.releaser_id,
            released_by_name=req.releaser_name,
            distribution_channels=req.channels,
            recipients=req.recipients
        )
        db.add(release)
        
        await ReportingService.log_audit(db, rep.id, "RELEASED", req.releaser_id, req.releaser_name, {"channels": req.channels})
        
        # In a real system, publish event to notification/portal microservices here
        await db.commit()
        await db.refresh(rep)
        return rep

    @staticmethod
    async def bulk_release(db: AsyncSession, req: BulkReleaseRequest) -> int:
        count = 0
        for rid in req.report_ids:
            try:
                # Basic recipients extraction from context or defaulting
                indiv_req = ReleaseReportRequest(
                    releaser_id=req.releaser_id, releaser_name=req.releaser_name, channels=req.channels, recipients=["portal_sync"]
                )
                await ReportingService.release_report(db, rid, indiv_req)
                count += 1
            except Exception as e:
                # Skip invalid
                pass
        return count

    @staticmethod
    async def amend_report(db: AsyncSession, report_id: str, req: AmendReportRequest) -> LabReport:
        rep = await ReportingService.get_report_by_id(db, report_id)
        if not rep: raise ValueError("Report not found.")
        
        # Create Version Snapshot
        snapshot = {
            "result_values": rep.result_values,
            "interpretative_comments": rep.interpretative_comments,
            "status": rep.status,
            "is_signed": rep.is_signed,
            "signed_by_name": rep.signed_by_name
        }
        
        version = ReportVersion(
            report_id=rep.id,
            version_number=rep.current_version,
            changes_made=req.changes_made,
            amended_by_id=req.amender_id,
            amended_by_name=req.amender_name,
            previous_snapshot=snapshot
        )
        db.add(version)
        
        # Apply Amendments
        rep.result_values = req.new_result_values
        if req.new_comments is not None:
             rep.interpretative_comments = req.new_comments
        rep.current_version += 1
        rep.status = "AMENDED"
        rep.is_signed = False # Requires re-signature
        rep.signed_by_name = None
        rep.signed_by_designation = None
        rep.signed_by_id = None
        
        await ReportingService.log_audit(db, rep.id, "AMENDED", req.amender_id, req.amender_name, {"reason": req.reason})
        
        await db.commit()
        await db.refresh(rep)
        return rep

    @staticmethod
    def evaluate_smart_comments(test_name: str, numeric_value: float, strings_value: str) -> Optional[str]:
        """Dummy mock of rule engine for smart comments"""
        if "HIV" in test_name and strings_value == "Reactive":
            return "Reactive result detected. Confirmatory testing recommended via Western Blot."
        if "Glucose" in test_name and numeric_value and numeric_value > 180:
            return "Result indicates hyperglycemia. Clinical correlation required."
        if "Hemoglobin" in test_name and numeric_value and numeric_value < 8.0:
            return "Critical Anemia Alert. Immediate review indicated."
        return None
