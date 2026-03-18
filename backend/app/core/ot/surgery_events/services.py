import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .models import SurgeryEvent, SurgeryEventType
from .schemas import SurgeryEventCreate
from app.core.ot.surgery_schedule.models import SurgerySchedule, SurgeryStatus
from app.core.ot.workflow.services import OTWorkflowService


class SurgeryEventService:
    @staticmethod
    async def record_event(db: AsyncSession, event_in: SurgeryEventCreate) -> SurgeryEvent:
        event = SurgeryEvent(**event_in.model_dump())
        db.add(event)
        
        # Side effect: update surgery schedule status based on event
        schedule = await db.get(SurgerySchedule, event_in.schedule_id)
        if schedule:
            if event_in.event_type == SurgeryEventType.PATIENT_IN_ROOM:
                schedule.status = SurgeryStatus.PREPARING
            elif event_in.event_type == SurgeryEventType.INCISION_MADE:
                schedule.status = SurgeryStatus.IN_PROGRESS
            elif event_in.event_type == SurgeryEventType.PROCEDURE_COMPLETED:
                schedule.status = SurgeryStatus.COMPLETED
                # Trigger completion workflow (timeline + billing)
                await OTWorkflowService.process_surgery_completion(db, event_in.schedule_id, event_in.recorded_by)
            
            # General timeline logging for all events
            await OTWorkflowService.log_timeline_event(
                db, 
                event_in.schedule_id, 
                event_in.event_type, 
                f"Surgery event recorded: {event_in.event_type}", 
                event_in.recorded_by
            )
        
        await db.commit()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_events_for_schedule(db: AsyncSession, schedule_id: uuid.UUID) -> list[SurgeryEvent]:
        stmt = select(SurgeryEvent).where(SurgeryEvent.schedule_id == schedule_id).order_by(SurgeryEvent.event_time)
        result = await db.execute(stmt)
        return list(result.scalars().all())
