from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, func
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from .models import ValidationWorklist, ValidationRecord, ValidationFlag, ValidationRejection, ValidationAudit
from .schemas import ApproveResultRequest, CorrectResultRequest, RejectResultRequest

class ValidationService:
    @staticmethod
    async def get_worklist(
        db: AsyncSession, 
        department: Optional[str] = None, 
        stage: Optional[str] = None, 
        priority: Optional[str] = None,
        test_type: Optional[str] = None
    ) -> List[ValidationWorklist]:
        query = select(ValidationWorklist)
        
        if department:
            query = query.where(ValidationWorklist.department == department)
        if stage:
            query = query.where(ValidationWorklist.validation_stage == stage)
        else:
            query = query.where(ValidationWorklist.validation_stage.in_(["PENDING_TECH", "PENDING_SENIOR", "PENDING_PATHOLOGIST"]))
        if priority:
            query = query.where(ValidationWorklist.priority_level == priority)
        if test_type:
            query = query.where(ValidationWorklist.test_name.ilike(f"%{test_type}%"))
            
        # Prioritize CRITICAL (Red) to the top, then URGENT (Orange), then others
        # Using a simple order by prioritizing the string value (We'd ideally map priority integer in Python if not in DB, but since it's a priority queue dashboard, we'll sort them in-memory or by specific DB field)
        # CRITICAL, URGENT, ABNORMAL, NORMAL
        result = await db.execute(query)
        items = result.scalars().all()
        
        # In-memory sort by Priority Levels (CRITICAL > URGENT > ABNORMAL > NORMAL)
        priority_order = {"CRITICAL": 0, "URGENT": 1, "ABNORMAL": 2, "NORMAL": 3}
        items_sorted = sorted(items, key=lambda x: priority_order.get(x.priority_level, 4))
        return items_sorted

    @staticmethod
    async def get_worklist_by_id(db: AsyncSession, item_id: str) -> Optional[ValidationWorklist]:
        q = select(ValidationWorklist).where(ValidationWorklist.id == item_id)
        result = await db.execute(q)
        return result.scalars().first()

    @staticmethod
    async def log_audit(db: AsyncSession, worklist_id: str, action: str, actor_id: str, actor_name: str, details: Dict = None):
        audit = ValidationAudit(
            worklist_id=worklist_id,
            action_type=action,
            actor_id=actor_id,
            actor_name=actor_name,
            details=details
        )
        db.add(audit)
        
    @staticmethod
    def determine_next_stage(current_stage: str) -> str:
        if current_stage == "PENDING_TECH":
            return "PENDING_SENIOR"
        elif current_stage == "PENDING_SENIOR":
            return "PENDING_PATHOLOGIST"
        elif current_stage == "PENDING_PATHOLOGIST":
            return "APPROVED"
        return "APPROVED"

    @staticmethod
    async def approve_result(db: AsyncSession, item_id: str, req: ApproveResultRequest) -> ValidationWorklist:
        item = await ValidationService.get_worklist_by_id(db, item_id)
        if not item:
            raise ValueError("Worklist item not found")
        
        old_stage = item.validation_stage
        new_stage = ValidationService.determine_next_stage(old_stage)
        item.validation_stage = new_stage
        
        record = ValidationRecord(
            worklist_id=item.id,
            stage_name=req.stage_name,
            validator_id=req.validator_id,
            validator_name=req.validator_name,
            action="APPROVED",
            remarks=req.remarks
        )
        db.add(record)
        
        await ValidationService.log_audit(
            db, item.id, "STAGE_ADVANCED", req.validator_id, req.validator_name,
            {"old_stage": old_stage, "new_stage": new_stage}
        )
        
        if new_stage == "APPROVED":
            from app.core.lab.reporting_engine.services import ReportingService
            await ReportingService.auto_create_report(db, item)
            
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def batch_approve(db: AsyncSession, worklist_ids: List[str], validator_id: str, validator_name: str, stage_name: str) -> int:
        count = 0
        for wid in worklist_ids:
            item = await ValidationService.get_worklist_by_id(db, wid)
            # Cannot batch approve criticals implicitly per requirements:
            # "Batch validation must only be allowed for non-critical results."
            if item and item.priority_level != "CRITICAL" and item.validation_stage != "APPROVED":
                old_stage = item.validation_stage
                new_stage = ValidationService.determine_next_stage(old_stage)
                item.validation_stage = new_stage
                
                record = ValidationRecord(
                    worklist_id=item.id,
                    stage_name=stage_name,
                    validator_id=validator_id,
                    validator_name=validator_name,
                    action="APPROVED_BATCH"
                )
                db.add(record)
                await ValidationService.log_audit(
                    db, item.id, "BATCH_APPROVED", validator_id, validator_name,
                    {"old_stage": old_stage, "new_stage": new_stage}
                )
                
                if new_stage == "APPROVED":
                    from app.core.lab.reporting_engine.services import ReportingService
                    await ReportingService.auto_create_report(db, item)
                    
                count += 1
        
        await db.commit()
        return count

    @staticmethod
    async def correct_result(db: AsyncSession, item_id: str, req: CorrectResultRequest) -> ValidationWorklist:
        item = await ValidationService.get_worklist_by_id(db, item_id)
        if not item:
            raise ValueError("Worklist item not found")
            
        old_value = item.result_value
        item.result_value = req.new_value
        
        record = ValidationRecord(
            worklist_id=item.id,
            stage_name=req.stage_name,
            validator_id=req.validator_id,
            validator_name=req.validator_name,
            action="CORRECTED",
            corrections_made={"old_value": old_value, "new_value": req.new_value},
            remarks=req.remarks
        )
        db.add(record)
        
        await ValidationService.log_audit(
            db, item.id, "RESULT_CORRECTED", req.validator_id, req.validator_name,
            {"old_value": old_value, "new_value": req.new_value}
        )
        
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def reject_result(db: AsyncSession, item_id: str, req: RejectResultRequest) -> ValidationWorklist:
        item = await ValidationService.get_worklist_by_id(db, item_id)
        if not item:
            raise ValueError("Worklist item not found")
            
        item.validation_stage = "REJECTED"
        
        rejection = ValidationRejection(
            worklist_id=item.id,
            rejected_by_id=req.validator_id,
            rejected_by_name=req.validator_name,
            rejection_reason=req.rejection_reason,
            action_taken=req.action_taken
        )
        db.add(rejection)
        
        await ValidationService.log_audit(
            db, item.id, "REJECTED", req.validator_id, req.validator_name,
            {"reason": req.rejection_reason, "action": req.action_taken}
        )
        
        await db.commit()
        await db.refresh(item)
        return item

    @staticmethod
    async def generate_critical_alert(db: AsyncSession, item_id: str, recorded_value: str, reference_range: str, alert_msg: str):
        item = await ValidationService.get_worklist_by_id(db, item_id)
        if not item:
            return
            
        item.priority_level = "CRITICAL"
        item.is_critical_alert = True
        
        flag = ValidationFlag(
            worklist_id=item_id,
            flag_type="CRITICAL",
            reference_range=reference_range,
            recorded_value=recorded_value,
            alert_message=alert_msg,
            notified_to={"targets": ["doctor", "nursing_station", "supervisor"]}
        )
        db.add(flag)
        await db.commit()

    @staticmethod
    async def get_performance_metrics(db: AsyncSession) -> Dict[str, Any]:
        """Calculates simple performance analytics for the validation phase."""
        from datetime import datetime, timedelta
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # 1. total validated in last 24h
        val_q = select(func.count(ValidationRecord.id)).where(ValidationRecord.action.in_(["APPROVED", "APPROVED_BATCH"])).where(ValidationRecord.timestamp > yesterday)
        val_res = await db.execute(val_q)
        total_validated = val_res.scalar() or 0
        
        # 2. total rejected in last 24h
        rej_q = select(func.count(ValidationRejection.id)).where(ValidationRejection.timestamp > yesterday)
        rej_res = await db.execute(rej_q)
        total_rejected = rej_res.scalar() or 0
        
        # 3. critical alerts in last 24h
        crit_q = select(func.count(ValidationFlag.id)).where(ValidationFlag.flag_type == "CRITICAL").where(ValidationFlag.created_at > yesterday)
        crit_res = await db.execute(crit_q)
        critical_alerts = crit_res.scalar() or 0
        
        # 4. workload distribution
        work_q = select(ValidationRecord.validator_name, func.count(ValidationRecord.id)).where(ValidationRecord.timestamp > yesterday).group_by(ValidationRecord.validator_name)
        work_res = await db.execute(work_q)
        distro = {row[0]: row[1] for row in work_res.all()}
        
        return {
            "total_validated": total_validated,
            "total_rejected": total_rejected,
            "critical_alerts": critical_alerts,
            "avg_turnaround_time_mins": 45.2, # Placeholder value for demonstration
            "workload_distribution": distro
        }
