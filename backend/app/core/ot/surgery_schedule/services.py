import uuid
from datetime import datetime, timezone
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from .models import SurgerySchedule, SurgeryStatus, SurgeryPriority
from .schemas import SurgeryScheduleCreate, SurgeryScheduleUpdate
from app.core.encounters.encounters.models import Encounter
from app.core.ot.workflow.services import OTWorkflowService


class SurgeryScheduleService:
    @staticmethod
    async def schedule_surgery(db: AsyncSession, schedule_in: SurgeryScheduleCreate) -> SurgerySchedule:
        # 1. Ensure patient has an active encounter
        encounter_stmt = select(Encounter).where(
            and_(
                Encounter.id == schedule_in.encounter_id,
                Encounter.patient_id == schedule_in.patient_id,
                Encounter.status.in_(["ACTIVE", "active", "in_progress"])
            )
        )
        encounter_result = await db.execute(encounter_stmt)
        encounter = encounter_result.scalar_one_or_none()
        if not encounter:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Patient does not have an active encounter."
            )

        # 2. Prevent overlapping surgeries in the same operating room
        overlap_stmt = select(SurgerySchedule).where(
            and_(
                SurgerySchedule.operating_room_id == schedule_in.operating_room_id,
                SurgerySchedule.status != SurgeryStatus.CANCELLED,
                or_(
                    and_(
                        SurgerySchedule.scheduled_start_time <= schedule_in.scheduled_start_time,
                        SurgerySchedule.scheduled_end_time > schedule_in.scheduled_start_time
                    ),
                    and_(
                        SurgerySchedule.scheduled_start_time < schedule_in.scheduled_end_time,
                        SurgerySchedule.scheduled_end_time >= schedule_in.scheduled_end_time
                    ),
                    and_(
                        SurgerySchedule.scheduled_start_time >= schedule_in.scheduled_start_time,
                        SurgerySchedule.scheduled_end_time <= schedule_in.scheduled_end_time
                    )
                )
            )
        )
        overlap_result = await db.execute(overlap_stmt)
        if overlap_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Operating room is already booked for this time period."
            )

        schedule = SurgerySchedule(**schedule_in.model_dump())
        db.add(schedule)
        await db.commit()
        await db.refresh(schedule)

        # Log in timeline
        await OTWorkflowService.log_timeline_event(
            db, schedule.id, "scheduled", f"Surgery scheduled: {schedule.procedure_id}", schedule_in.scheduled_by
        )

        return schedule

    @staticmethod
    async def get_schedule(db: AsyncSession, schedule_id: uuid.UUID) -> SurgerySchedule | None:
        return await db.get(SurgerySchedule, schedule_id)

    @staticmethod
    async def get_all_schedules(db: AsyncSession) -> list[SurgerySchedule]:
        result = await db.execute(select(SurgerySchedule))
        return list(result.scalars().all())

    @staticmethod
    async def update_schedule(db: AsyncSession, schedule_id: uuid.UUID, schedule_in: SurgeryScheduleUpdate) -> SurgerySchedule | None:
        schedule = await db.get(SurgerySchedule, schedule_id)
        if not schedule:
            return None
        
        # If updating room or time, re-check overlaps
        if schedule_in.operating_room_id or schedule_in.scheduled_start_time or schedule_in.scheduled_end_time:
            new_room_id = schedule_in.operating_room_id or schedule.operating_room_id
            new_start = schedule_in.scheduled_start_time or schedule.scheduled_start_time
            new_end = schedule_in.scheduled_end_time or schedule.scheduled_end_time
            
            overlap_stmt = select(SurgerySchedule).where(
                and_(
                    SurgerySchedule.id != schedule_id,
                    SurgerySchedule.operating_room_id == new_room_id,
                    SurgerySchedule.status != SurgeryStatus.CANCELLED,
                    or_(
                        and_(
                            SurgerySchedule.scheduled_start_time <= new_start,
                            SurgerySchedule.scheduled_end_time > new_start
                        ),
                        and_(
                            SurgerySchedule.scheduled_start_time < new_end,
                            SurgerySchedule.scheduled_end_time >= new_end
                        ),
                        and_(
                            SurgerySchedule.scheduled_start_time >= new_start,
                            SurgerySchedule.scheduled_end_time <= new_end
                        )
                    )
                )
            )
            overlap_result = await db.execute(overlap_stmt)
            if overlap_result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Operating room is already booked for this time period."
                )

        update_data = schedule_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(schedule, field, value)
        
        await db.commit()
        await db.refresh(schedule)
        return schedule

    @staticmethod
    async def cancel_surgery(db: AsyncSession, schedule_id: uuid.UUID) -> bool:
        schedule = await db.get(SurgerySchedule, schedule_id)
        if not schedule:
            return False
        schedule.status = SurgeryStatus.CANCELLED
        await db.commit()
        return True
