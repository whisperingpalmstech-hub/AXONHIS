import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.ot.surgery_events.models import SurgeryEventType
from app.core.ot.surgery_schedule.models import SurgerySchedule, SurgeryStatus
from app.core.ot.surgery_notes.models import SurgeryNote
from app.core.encounters.timeline.services import TimelineService
from app.core.encounters.timeline.schemas import EncounterTimelineCreate
from app.core.ot.billing_integration.services import SurgicalBillingService


class OTWorkflowService:
    @staticmethod
    async def log_timeline_event(db: AsyncSession, schedule_id: uuid.UUID, event_type: str, description: str, actor_id: uuid.UUID = None):
        schedule = await db.get(SurgerySchedule, schedule_id)
        if not schedule:
            return
        
        timeline_service = TimelineService(db)
        await timeline_service.add_event(
            encounter_id=schedule.encounter_id,
            actor_id=actor_id,
            data=EncounterTimelineCreate(
                event_type=f"surgery_{event_type}",
                description=description,
                metadata_json={"schedule_id": str(schedule_id)}
            )
        )

    @staticmethod
    async def process_surgery_completion(db: AsyncSession, schedule_id: uuid.UUID, user_id: uuid.UUID = None):
        # 1. Log in timeline
        await OTWorkflowService.log_timeline_event(
            db, schedule_id, "completed", "Surgical procedure completed.", user_id
        )
        
        # 2. Generate billing charges
        await SurgicalBillingService.generate_surgical_charges(db, schedule_id, user_id)
        
        await db.commit()
