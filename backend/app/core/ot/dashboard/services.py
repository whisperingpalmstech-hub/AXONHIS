import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.ot.surgery_schedule.models import SurgerySchedule, SurgeryStatus, SurgeryPriority
from app.core.ot.operating_rooms.models import OperatingRoom


class OTDashboardService:
    @staticmethod
    async def get_dashboard_summary(db: AsyncSession) -> dict:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        # 1. Today's surgeries
        today_stmt = select(SurgerySchedule).options(
            joinedload(SurgerySchedule.procedure),
            joinedload(SurgerySchedule.operating_room)
        ).where(
            and_(
                SurgerySchedule.scheduled_start_time >= today_start,
                SurgerySchedule.scheduled_start_time < today_end,
                SurgerySchedule.status != SurgeryStatus.CANCELLED
            )
        ).order_by(SurgerySchedule.scheduled_start_time)
        today_result = await db.execute(today_stmt)
        today_list = today_result.scalars().all()

        # 2. Operating room usage
        room_stmt = select(OperatingRoom)
        room_result = await db.execute(room_stmt)
        rooms = room_result.scalars().all()
        room_usage = [
            {
                "id": room.id,
                "code": room.room_code,
                "name": room.room_name,
                "status": room.status
            } for room in rooms
        ]

        # 3. Upcoming surgeries
        upcoming_stmt = select(SurgerySchedule).options(
            joinedload(SurgerySchedule.procedure),
            joinedload(SurgerySchedule.operating_room)
        ).where(
            and_(
                SurgerySchedule.scheduled_start_time > now,
                SurgerySchedule.status == SurgeryStatus.SCHEDULED
            )
        ).order_by(SurgerySchedule.scheduled_start_time).limit(10)
        upcoming_result = await db.execute(upcoming_stmt)
        upcoming_surgeries = upcoming_result.scalars().all()

        # 4. Delayed procedures
        # Surgery is delayed if status is SCHEDULED and start_time < now
        delayed_stmt = select(SurgerySchedule).options(
            joinedload(SurgerySchedule.procedure),
            joinedload(SurgerySchedule.operating_room)
        ).where(
            and_(
                SurgerySchedule.scheduled_start_time < now,
                SurgerySchedule.status == SurgeryStatus.SCHEDULED
            )
        )
        delayed_result = await db.execute(delayed_stmt)
        delayed_surgeries = delayed_result.scalars().all()

        # 5. Emergency surgeries
        emergency_stmt = select(SurgerySchedule).where(
            and_(
                SurgerySchedule.priority == SurgeryPriority.EMERGENCY,
                SurgerySchedule.status != SurgeryStatus.COMPLETED,
                SurgerySchedule.status != SurgeryStatus.CANCELLED
            )
        )
        emergency_result = await db.execute(emergency_stmt)
        emergency_surgeries = emergency_result.scalars().all()

        return {
            "today_count": len(today_list),
            "today_surgeries": today_list,
            "room_usage": room_usage,
            "upcoming": upcoming_surgeries,
            "delayed": delayed_surgeries,
            "emergency": emergency_surgeries
        }
