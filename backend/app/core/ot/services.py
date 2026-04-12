"""OT Module — Services. Links to IPD, billing (ChargePosting), pharmacy."""
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from .models import OTRoom, OTSchedule, OTConsumable, OTAnesthesiaRecord

def _now(): return datetime.now(timezone.utc)

class OTRoomService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create(self, data, org_id):
        # If org_id is None, use a default UUID or make it optional
        if org_id is None:
            # Create a default org_id for testing/demo purposes
            org_id = uuid.UUID('00000000-0000-0000-0000-000000000001')
        room = OTRoom(org_id=org_id, **data.model_dump())
        self.db.add(room); await self.db.commit(); await self.db.refresh(room); return room

    async def list_rooms(self, org_id):
        return list((await self.db.execute(
            select(OTRoom).where(OTRoom.org_id == org_id, OTRoom.is_active == True)
        )).scalars().all())

    async def update_status(self, room_id, status, org_id):
        room = (await self.db.execute(select(OTRoom).where(OTRoom.id == room_id, OTRoom.org_id == org_id))).scalars().first()
        if not room: raise ValueError("Room not found")
        room.status = status
        await self.db.commit(); await self.db.refresh(room); return room


class OTScheduleService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create(self, data, created_by, org_id):
        sched = OTSchedule(
            org_id=org_id, **data.model_dump(exclude={"primary_surgeon_name","anesthesiologist_name","scrub_nurse_name"}),
            primary_surgeon_id=created_by, primary_surgeon_name=data.primary_surgeon_name,
            anesthesiologist_name=data.anesthesiologist_name, scrub_nurse_name=data.scrub_nurse_name,
            scheduled_end=data.scheduled_date + timedelta(minutes=data.estimated_duration_mins),
            created_by=created_by
        )
        self.db.add(sched); await self.db.commit(); await self.db.refresh(sched); return sched

    async def list_schedules(self, org_id, date_filter=None, status=None):
        stmt = select(OTSchedule).where(OTSchedule.org_id == org_id)
        if status: stmt = stmt.where(OTSchedule.status == status)
        if date_filter:
            start = datetime.combine(date_filter, datetime.min.time()).replace(tzinfo=timezone.utc)
            end = start + timedelta(days=1)
            stmt = stmt.where(OTSchedule.scheduled_date >= start, OTSchedule.scheduled_date < end)
        return list((await self.db.execute(stmt.order_by(OTSchedule.scheduled_date.asc()))).scalars().all())

    async def get(self, schedule_id, org_id):
        s = (await self.db.execute(select(OTSchedule).where(OTSchedule.id == schedule_id, OTSchedule.org_id == org_id))).scalars().first()
        if not s: raise ValueError("Schedule not found")
        return s

    async def update_status(self, schedule_id, update, org_id):
        s = await self.get(schedule_id, org_id)
        s.status = update.status; s.updated_at = _now()
        if update.status == "patient_in_ot": s.actual_start = _now()
        if update.status == "completed": s.actual_end = _now()
        if update.post_op_diagnosis: s.post_op_diagnosis = update.post_op_diagnosis
        if update.post_op_notes: s.post_op_notes = update.post_op_notes
        if update.blood_loss_ml is not None: s.blood_loss_ml = update.blood_loss_ml
        if update.cancellation_reason: s.cancellation_reason = update.cancellation_reason; s.status = "cancelled"
        
        # Update OT room status
        room = (await self.db.execute(select(OTRoom).where(OTRoom.id == s.ot_room_id))).scalars().first()
        if room:
            if update.status in ["patient_in_ot","anesthesia_start","incision","closing"]: room.status = "in_use"
            elif update.status in ["completed","cancelled"]: room.status = "cleaning"
        
        await self.db.commit(); await self.db.refresh(s); return s


class OTConsumableService:
    def __init__(self, db: AsyncSession): self.db = db

    async def add(self, data, org_id):
        c = OTConsumable(org_id=org_id, **data.model_dump(), total_price=data.unit_price * data.quantity)
        self.db.add(c)
        # Update schedule total charges
        sched = (await self.db.execute(select(OTSchedule).where(OTSchedule.id == data.ot_schedule_id))).scalars().first()
        if sched: sched.total_charges = (sched.total_charges or Decimal("0")) + c.total_price
        await self.db.commit(); await self.db.refresh(c); return c

    async def list_consumables(self, schedule_id, org_id):
        return list((await self.db.execute(
            select(OTConsumable).where(OTConsumable.ot_schedule_id == schedule_id, OTConsumable.org_id == org_id)
        )).scalars().all())


class OTAnesthesiaService:
    def __init__(self, db: AsyncSession): self.db = db

    async def create(self, data, recorded_by, recorded_by_name, org_id):
        rec = OTAnesthesiaRecord(org_id=org_id, **data.model_dump(),
            recorded_by=recorded_by, recorded_by_name=recorded_by_name, induction_time=_now())
        self.db.add(rec); await self.db.commit(); await self.db.refresh(rec); return rec

    async def get(self, schedule_id, org_id):
        return (await self.db.execute(
            select(OTAnesthesiaRecord).where(OTAnesthesiaRecord.ot_schedule_id == schedule_id, OTAnesthesiaRecord.org_id == org_id)
        )).scalars().first()


class OTDashboardService:
    def __init__(self, db: AsyncSession): self.db = db

    async def get_stats(self, org_id):
        from .schemas import OTDashboardStats
        today_start = datetime.combine(datetime.now(timezone.utc).date(), datetime.min.time()).replace(tzinfo=timezone.utc)
        today_end = today_start + timedelta(days=1)

        rooms_total = (await self.db.execute(select(func.count()).select_from(OTRoom).where(OTRoom.org_id == org_id, OTRoom.is_active == True))).scalar() or 0
        rooms_avail = (await self.db.execute(select(func.count()).select_from(OTRoom).where(OTRoom.org_id == org_id, OTRoom.status == "available"))).scalar() or 0
        rooms_use = (await self.db.execute(select(func.count()).select_from(OTRoom).where(OTRoom.org_id == org_id, OTRoom.status == "in_use"))).scalar() or 0

        today_base = select(OTSchedule).where(OTSchedule.org_id == org_id, OTSchedule.scheduled_date >= today_start, OTSchedule.scheduled_date < today_end)
        today_total = (await self.db.execute(select(func.count()).select_from(today_base.subquery()))).scalar() or 0
        in_prog = (await self.db.execute(select(func.count()).select_from(OTSchedule).where(
            OTSchedule.org_id == org_id, OTSchedule.status.in_(["patient_in_ot","anesthesia_start","incision","closing"])
        ))).scalar() or 0
        completed = (await self.db.execute(select(func.count()).select_from(OTSchedule).where(
            OTSchedule.org_id == org_id, OTSchedule.status == "completed", OTSchedule.actual_end >= today_start
        ))).scalar() or 0

        return OTDashboardStats(total_rooms=rooms_total, rooms_available=rooms_avail, rooms_in_use=rooms_use,
            todays_surgeries=today_total, in_progress=in_prog, completed_today=completed)
