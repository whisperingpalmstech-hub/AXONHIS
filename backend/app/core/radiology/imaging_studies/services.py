import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .models import ImagingStudy
from .schemas import ImagingStudyCreate
from app.core.radiology.imaging_orders.models import ImagingOrder, ImagingOrderStatus

class ImagingStudyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_study(self, data: ImagingStudyCreate) -> ImagingStudy:
        # Avoid multiple values for 'status' if it's already in data
        params = data.model_dump()
        params.pop("status", None) 
        study = ImagingStudy(**params, status="scheduled")
        self.db.add(study)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(study)
        return study

    async def start_study(self, study_id: uuid.UUID, machine_id: str, user_id: uuid.UUID) -> ImagingStudy:
        res = await self.db.execute(select(ImagingStudy).where(ImagingStudy.id == study_id))
        study = res.scalar_one_or_none()
        if not study:
            return None
        
        study.status = "scanning"
        study.machine_id = machine_id
        study.study_start_time = datetime.now(timezone.utc)
        
        # Update order status
        res_ord = await self.db.execute(select(ImagingOrder).where(ImagingOrder.id == study.imaging_order_id))
        order = res_ord.scalar_one_or_none()
        if order:
            order.status = ImagingOrderStatus.IN_PROGRESS
            
        # Timeline update
        from app.core.encounters.timeline.services import TimelineService
        from app.core.encounters.timeline.schemas import EncounterTimelineCreate
        ts = TimelineService(self.db)
        await ts.add_event(order.encounter_id, user_id, EncounterTimelineCreate(
            event_type="SCAN_STARTED",
            description=f"Radiology scan started for study {study.modality}: {order.requested_study}",
            metadata_json={"study_id": str(study_id), "modality": study.modality}
        ))
        
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(study)
        return study

    async def complete_study(self, study_id: uuid.UUID, user_id: uuid.UUID) -> ImagingStudy:
        res = await self.db.execute(select(ImagingStudy).where(ImagingStudy.id == study_id))
        study = res.scalar_one_or_none()
        if not study:
            return None
            
        study.status = "completed"
        study.study_end_time = datetime.now(timezone.utc)
        
        # Update order status
        res_ord = await self.db.execute(select(ImagingOrder).where(ImagingOrder.id == study.imaging_order_id))
        order = res_ord.scalar_one_or_none()
        if order:
            order.status = ImagingOrderStatus.COMPLETED
            
            # --- Billing Integration ---
            from app.core.billing.billing_entries.services import BillingEntryService
            from app.core.billing.billing_entries.schemas import BillingEntryCreate
            from app.core.billing.services.models import BillingService
            
            # Fetch a valid service ID to avoid crash (demo fallback)
            serv_res = await self.db.execute(select(BillingService).limit(1))
            billing_serv = serv_res.scalars().first()
            
            # For simplicity, we assume we fetch the price from a catalog or use item.unit_price from the order
            from app.core.orders.models import OrderItem
            item_res = await self.db.execute(select(OrderItem).where(OrderItem.order_id == order.order_id))
            item = item_res.scalars().first()
            price = float(item.unit_price) if item else 150.0 # Default if no order item

            if billing_serv:
                billing_service = BillingEntryService(self.db)
                await billing_service.create_entry(BillingEntryCreate(
                    encounter_id=order.encounter_id,
                    patient_id=order.patient_id,
                    order_id=order.order_id,
                    service_id=billing_serv.id,
                    quantity=1.0,
                    unit_price=price,
                    notes=f"Radiology study completed: {order.requested_study}"
                ), user_id=user_id)
            
            # --- Timeline Event ---
            from app.core.encounters.timeline.services import TimelineService
            from app.core.encounters.timeline.schemas import EncounterTimelineCreate
            ts = TimelineService(self.db)
            await ts.add_event(order.encounter_id, user_id, EncounterTimelineCreate(
                event_type="SCAN_COMPLETED",
                description=f"Radiology scan completed: {order.requested_study}",
                metadata_json={"study_id": str(study_id), "modality": study.modality}
            ))
            
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(study)
        return study
    async def list_studies(self, skip: int = 0, limit: int = 100) -> list[ImagingStudy]:
        result = await self.db.execute(select(ImagingStudy).offset(skip).limit(limit))
        return list(result.scalars().all())
