import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import RadiologyReport
from .schemas import RadiologyReportCreate
from app.core.radiology.imaging_studies.models import ImagingStudy
from app.core.radiology.imaging_orders.models import ImagingOrder
from app.core.radiology.radiology_results.models import RadiologyResult

class RadiologyReportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_draft(self, data: RadiologyReportCreate, user_id: uuid.UUID) -> RadiologyReport:
        # Prevent double-assignment of status
        params = data.model_dump()
        params.pop("status", None)
        report = RadiologyReport(**params, status="draft", reported_by=user_id)
        self.db.add(report)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def finalize_report(self, report_id: uuid.UUID, impression: str, critical_flag: bool, user_id: uuid.UUID) -> RadiologyReport:
        res = await self.db.execute(select(RadiologyReport).where(RadiologyReport.id == report_id))
        report = res.scalar_one_or_none()
        if not report:
            return None
            
        report.status = "final"
        report.reported_at = datetime.now(timezone.utc)
        
        # Update study status
        res_study = await self.db.execute(select(ImagingStudy).where(ImagingStudy.id == report.study_id))
        study = res_study.scalar_one_or_none()
        if study:
            study.status = "reported"
            
            # --- Result Publishing ---
            result = RadiologyResult(
                study_id=study.id,
                impression=impression,
                critical_flag=critical_flag,
                published_at=datetime.now(timezone.utc)
            )
            self.db.add(result)
            
            # --- Notification (Critical finding) ---
            if critical_flag:
                from app.core.notifications.services import NotificationService
                from app.core.notifications.schemas import NotificationCreate
                
                # Fetch order to find patient/clinician
                res_ord = await self.db.execute(select(ImagingOrder).where(ImagingOrder.id == study.imaging_order_id))
                order = res_ord.scalar_one_or_none()
                if order:
                    target_recipient = order.ordered_by # Let's notify the ordering clinician
                    ns = NotificationService(self.db)
                    await ns.create_notification(NotificationCreate(
                        user_id=target_recipient,
                        title="CRITICAL RADIOLOGY RESULT",
                        message=f"Critical find reported for patient in study {study.modality}: {order.requested_study}",
                        priority="urgent",
                        delivery_method="system"
                    ))

            # --- Timeline Update ---
            from app.core.encounters.timeline.services import TimelineService
            from app.core.encounters.timeline.schemas import EncounterTimelineCreate
            ts = TimelineService(self.db)
            res_ord = await self.db.execute(select(ImagingOrder).where(ImagingOrder.id == study.imaging_order_id))
            order = res_ord.scalar_one_or_none()
            if order:
                await ts.add_event(order.encounter_id, user_id, EncounterTimelineCreate(
                    event_type="REPORT_FINALIZED",
                    description=f"Radiology report finalized for {order.requested_study}",
                    metadata_json={"study_id": str(study.id), "critical_flag": critical_flag}
                ))

        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(report)
        return report

    async def get_report_by_id(self, report_id: uuid.UUID) -> RadiologyReport:
        result = await self.db.execute(select(RadiologyReport).where(RadiologyReport.id == report_id))
        return result.scalar_one_or_none()

    async def list_reports(self, skip: int = 0, limit: int = 100) -> list[RadiologyReport]:
        result = await self.db.execute(select(RadiologyReport).offset(skip).limit(limit))
        return list(result.scalars().all())
