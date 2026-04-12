"""
Enterprise Scheduling – Service Layer
======================================
Implements all business logic for:
  - Doctor calendar management
  - Slot generation (manual + cyclic)
  - Slot booking with conflict detection
  - Overbooking engine
  - Emergency slot override
  - QR appointment slip
  - Modality scheduling (MRI / CT / XRay / US)
  - Appointment reminders
  - Automated follow-up scheduling
  - Doctor workload balancing
  - Scheduling analytics
"""

import uuid
import json
import hashlib
from datetime import datetime, date, time, timedelta, timezone
from typing import Sequence

from sqlalchemy import select, func, and_, or_, case, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scheduling.models import (
    DoctorCalendar, CalendarSlot, SlotBooking, OverbookingConfig,
    CyclicSchedule, ModalityResource, ModalitySlot,
    AppointmentReminder, FollowUpRule, SchedulingAnalytics,
    SlotStatus, AppointmentType, ReminderStatus, DayOfWeek,
)
from app.core.scheduling.schemas import (
    DoctorCalendarCreate, DoctorCalendarUpdate,
    SlotCreate, SlotBulkGenerate, SlotStatusUpdate,
    BookingCreate, BookingUpdate, EmergencyOverrideRequest,
    OverbookingConfigCreate,
    CyclicScheduleCreate,
    ModalityResourceCreate, ModalitySlotBook, ModalitySlotGenerate,
    ReminderCreate, FollowUpRuleCreate,
)

DAY_MAP = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Doctor Calendar Service
# ═══════════════════════════════════════════════════════════════════════════════

class DoctorCalendarService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_calendar(self, data: DoctorCalendarCreate) -> DoctorCalendar:
        cal = DoctorCalendar(**data.model_dump())
        self.db.add(cal)
        await self.db.flush()
        await self.db.refresh(cal)
        return cal

    async def get_calendar(self, calendar_id: uuid.UUID) -> DoctorCalendar | None:
        stmt = select(DoctorCalendar).where(DoctorCalendar.id == calendar_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_doctor_calendar(self, doctor_id: uuid.UUID) -> DoctorCalendar | None:
        stmt = select(DoctorCalendar).where(
            DoctorCalendar.doctor_id == doctor_id,
            DoctorCalendar.is_active == True,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_calendar(self, calendar_id: uuid.UUID, data: DoctorCalendarUpdate) -> DoctorCalendar:
        cal = await self.get_calendar(calendar_id)
        if not cal:
            raise ValueError("Calendar not found")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(cal, k, v)
        await self.db.flush()
        await self.db.refresh(cal)
        return cal

    async def list_calendars(self, department: str | None = None) -> Sequence[DoctorCalendar]:
        stmt = select(DoctorCalendar).where(DoctorCalendar.is_active == True)
        if department:
            stmt = stmt.where(DoctorCalendar.department == department)
        stmt = stmt.order_by(DoctorCalendar.department)
        result = await self.db.execute(stmt)
        return result.scalars().all()


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Slot Management Service
# ═══════════════════════════════════════════════════════════════════════════════

class SlotService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_slot(self, data: SlotCreate) -> CalendarSlot:
        slot = CalendarSlot(**data.model_dump())
        self.db.add(slot)
        await self.db.flush()
        await self.db.refresh(slot)
        return slot

    async def get_slot(self, slot_id: uuid.UUID) -> CalendarSlot | None:
        stmt = select(CalendarSlot).where(CalendarSlot.id == slot_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_doctor_slots(
        self, doctor_id: uuid.UUID, slot_date: date, status: str | None = None
    ) -> Sequence[CalendarSlot]:
        stmt = select(CalendarSlot).where(
            CalendarSlot.doctor_id == doctor_id,
            CalendarSlot.slot_date == slot_date,
        )
        if status:
            stmt = stmt.where(CalendarSlot.status == status)
        stmt = stmt.order_by(CalendarSlot.start_time)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_available_slots(
        self, doctor_id: uuid.UUID, from_date: date, to_date: date
    ) -> Sequence[CalendarSlot]:
        stmt = select(CalendarSlot).where(
            CalendarSlot.doctor_id == doctor_id,
            CalendarSlot.slot_date >= from_date,
            CalendarSlot.slot_date <= to_date,
            CalendarSlot.status.in_([SlotStatus.AVAILABLE, SlotStatus.OVERBOOKED]),
        ).order_by(CalendarSlot.slot_date, CalendarSlot.start_time)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def update_slot_status(self, slot_id: uuid.UUID, data: SlotStatusUpdate) -> CalendarSlot:
        slot = await self.get_slot(slot_id)
        if not slot:
            raise ValueError("Slot not found")
        slot.status = data.status
        if data.notes is not None:
            slot.notes = data.notes
        await self.db.flush()
        await self.db.refresh(slot)
        return slot

    async def generate_slots_from_cyclic(self, data: SlotBulkGenerate) -> list[CalendarSlot]:
        """Generate slots for a date range using cyclic schedule templates."""
        stmt = select(CyclicSchedule).where(
            CyclicSchedule.calendar_id == data.calendar_id,
            CyclicSchedule.is_active == True,
        )
        result = await self.db.execute(stmt)
        templates = list(result.scalars().all())
        if not templates:
            raise ValueError("No active cyclic schedules found for this calendar")

        created_slots: list[CalendarSlot] = []
        current_date = data.start_date
        while current_date <= data.end_date:
            weekday = current_date.weekday()
            for tmpl in templates:
                tmpl_day = DAY_MAP.get(tmpl.day_of_week, -1)
                if tmpl_day != weekday:
                    continue
                if tmpl.effective_from and current_date < tmpl.effective_from:
                    continue
                if tmpl.effective_until and current_date > tmpl.effective_until:
                    continue

                # Generate slots for this template
                slot_start = datetime.combine(current_date, tmpl.start_time)
                slot_end_boundary = datetime.combine(current_date, tmpl.end_time)
                duration = timedelta(minutes=tmpl.slot_duration_min)

                while slot_start + duration <= slot_end_boundary:
                    s_end = slot_start + duration
                    # Check if slot already exists
                    existing = await self.db.execute(
                        select(CalendarSlot).where(
                            CalendarSlot.calendar_id == data.calendar_id,
                            CalendarSlot.slot_date == current_date,
                            CalendarSlot.start_time == slot_start.time(),
                        )
                    )
                    if not existing.scalar_one_or_none():
                        new_slot = CalendarSlot(
                            calendar_id=data.calendar_id,
                            doctor_id=data.doctor_id,
                            slot_date=current_date,
                            start_time=slot_start.time(),
                            end_time=s_end.time(),
                            appointment_type=tmpl.appointment_type,
                            max_bookings=tmpl.max_patients_per_slot,
                        )
                        self.db.add(new_slot)
                        created_slots.append(new_slot)
                    slot_start = s_end
            current_date += timedelta(days=1)

        await self.db.flush()
        return created_slots


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Booking Service
# ═══════════════════════════════════════════════════════════════════════════════

class BookingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def book_slot(self, data: BookingCreate) -> SlotBooking:
        """Book a slot – handles capacity, overbooking, and QR generation."""
        slot = await self.db.execute(select(CalendarSlot).where(CalendarSlot.id == data.slot_id))
        slot_obj = slot.scalar_one_or_none()
        if not slot_obj:
            raise ValueError("Slot not found")

        # Check capacity
        if slot_obj.status == SlotStatus.BLOCKED:
            raise ValueError("This slot is blocked and cannot be booked")

        if slot_obj.current_bookings >= slot_obj.max_bookings:
            # Check overbooking config
            config = await self._get_overbook_config(data.doctor_id, data.department)
            if config and config.allow_emergency_override and slot_obj.current_bookings < slot_obj.max_bookings + config.max_overbook_per_slot:
                slot_obj.status = SlotStatus.OVERBOOKED
            else:
                raise ValueError("Slot is fully booked. No overbooking allowed.")

        # Create booking
        booking = SlotBooking(
            slot_id=data.slot_id,
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            department=data.department,
            booking_date=slot_obj.slot_date,
            appointment_type=data.appointment_type,
            reason=data.reason,
            is_follow_up=data.is_follow_up,
            parent_booking_id=data.parent_booking_id,
        )

        # Generate QR code data
        booking.qr_code_data = self._generate_qr_data(booking, slot_obj)

        self.db.add(booking)
        slot_obj.current_bookings += 1
        if slot_obj.current_bookings >= slot_obj.max_bookings:
            if slot_obj.status != SlotStatus.OVERBOOKED:
                slot_obj.status = SlotStatus.BOOKED

        await self.db.flush()
        await self.db.refresh(booking)
        return booking

    async def emergency_override(self, data: EmergencyOverrideRequest) -> SlotBooking:
        """Force-book an emergency slot, overriding capacity limits."""
        # Find the best available slot near preferred time
        stmt = select(CalendarSlot).where(
            CalendarSlot.doctor_id == data.doctor_id,
            CalendarSlot.slot_date == data.slot_date,
        ).order_by(CalendarSlot.start_time)
        result = await self.db.execute(stmt)
        slots = list(result.scalars().all())

        target_slot = None
        if data.preferred_time:
            # Find closest slot to preferred time
            for s in slots:
                if s.start_time >= data.preferred_time:
                    target_slot = s
                    break
            if not target_slot and slots:
                target_slot = slots[-1]
        elif slots:
            # Find slot with least bookings
            target_slot = min(slots, key=lambda s: s.current_bookings)

        if not target_slot:
            raise ValueError("No slots available for emergency override on this date")

        target_slot.is_emergency_override = True
        target_slot.status = SlotStatus.OVERBOOKED

        booking = SlotBooking(
            slot_id=target_slot.id,
            patient_id=data.patient_id,
            doctor_id=data.doctor_id,
            department=data.department,
            booking_date=data.slot_date,
            appointment_type=AppointmentType.EMERGENCY,
            reason=f"EMERGENCY: {data.reason}",
            status="confirmed",
        )
        booking.qr_code_data = self._generate_qr_data(booking, target_slot)
        self.db.add(booking)
        target_slot.current_bookings += 1
        await self.db.flush()
        await self.db.refresh(booking)
        return booking

    async def update_booking(self, booking_id: uuid.UUID, data: BookingUpdate) -> SlotBooking:
        stmt = select(SlotBooking).where(SlotBooking.id == booking_id)
        result = await self.db.execute(stmt)
        booking = result.scalar_one_or_none()
        if not booking:
            raise ValueError("Booking not found")

        old_status = booking.status
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(booking, k, v)

        # Handle status transitions
        if data.status == "checked_in" and old_status != "checked_in":
            booking.check_in_time = datetime.now(timezone.utc)
        elif data.status == "completed" and old_status != "completed":
            booking.completion_time = datetime.now(timezone.utc)
        elif data.status == "cancelled" and old_status != "cancelled":
            # Free the slot
            slot = await self.db.execute(select(CalendarSlot).where(CalendarSlot.id == booking.slot_id))
            slot_obj = slot.scalar_one_or_none()
            if slot_obj:
                slot_obj.current_bookings = max(0, slot_obj.current_bookings - 1)
                if slot_obj.current_bookings < slot_obj.max_bookings:
                    slot_obj.status = SlotStatus.AVAILABLE if slot_obj.current_bookings == 0 else SlotStatus.BOOKED

        await self.db.flush()
        await self.db.refresh(booking)
        return booking

    async def get_booking(self, booking_id: uuid.UUID) -> SlotBooking | None:
        stmt = select(SlotBooking).where(SlotBooking.id == booking_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_bookings(
        self, doctor_id: uuid.UUID | None = None, patient_id: uuid.UUID | None = None,
        from_date: date | None = None, to_date: date | None = None, status: str | None = None,
    ) -> Sequence[SlotBooking]:
        stmt = select(SlotBooking)
        if doctor_id:
            stmt = stmt.where(SlotBooking.doctor_id == doctor_id)
        if patient_id:
            stmt = stmt.where(SlotBooking.patient_id == patient_id)
        if from_date:
            stmt = stmt.where(SlotBooking.booking_date >= from_date)
        if to_date:
            stmt = stmt.where(SlotBooking.booking_date <= to_date)
        if status:
            stmt = stmt.where(SlotBooking.status == status)
        stmt = stmt.order_by(SlotBooking.booking_date.desc(), SlotBooking.created_at.desc())
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def _get_overbook_config(self, doctor_id: uuid.UUID, department: str) -> OverbookingConfig | None:
        stmt = select(OverbookingConfig).where(
            or_(
                OverbookingConfig.doctor_id == doctor_id,
                OverbookingConfig.department == department,
            ),
            OverbookingConfig.is_active == True,
        ).limit(1)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _generate_qr_data(booking: SlotBooking, slot: CalendarSlot) -> str:
        payload = {
            "booking_id": str(booking.id) if booking.id else str(uuid.uuid4()),
            "patient_id": str(booking.patient_id),
            "doctor_id": str(booking.doctor_id),
            "department": booking.department,
            "date": str(slot.slot_date),
            "time": str(slot.start_time),
            "type": booking.appointment_type,
        }
        return json.dumps(payload)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Overbooking Config Service
# ═══════════════════════════════════════════════════════════════════════════════

class OverbookingConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_config(self, data: OverbookingConfigCreate) -> OverbookingConfig:
        config = OverbookingConfig(**data.model_dump())
        self.db.add(config)
        await self.db.flush()
        await self.db.refresh(config)
        return config

    async def list_configs(self) -> Sequence[OverbookingConfig]:
        stmt = select(OverbookingConfig).where(OverbookingConfig.is_active == True)
        result = await self.db.execute(stmt)
        return result.scalars().all()


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Cyclic Schedule Service
# ═══════════════════════════════════════════════════════════════════════════════

class CyclicScheduleService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_schedule(self, data: CyclicScheduleCreate) -> CyclicSchedule:
        sched = CyclicSchedule(**data.model_dump())
        self.db.add(sched)
        await self.db.flush()
        await self.db.refresh(sched)
        return sched

    async def list_schedules(self, calendar_id: uuid.UUID) -> Sequence[CyclicSchedule]:
        stmt = select(CyclicSchedule).where(
            CyclicSchedule.calendar_id == calendar_id,
            CyclicSchedule.is_active == True,
        ).order_by(CyclicSchedule.day_of_week)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def deactivate_schedule(self, schedule_id: uuid.UUID) -> CyclicSchedule:
        stmt = select(CyclicSchedule).where(CyclicSchedule.id == schedule_id)
        result = await self.db.execute(stmt)
        sched = result.scalar_one_or_none()
        if not sched:
            raise ValueError("Schedule not found")
        sched.is_active = False
        await self.db.flush()
        return sched


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Modality Scheduling Service
# ═══════════════════════════════════════════════════════════════════════════════

class ModalitySchedulingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_resource(self, data: ModalityResourceCreate) -> ModalityResource:
        res = ModalityResource(**data.model_dump())
        self.db.add(res)
        await self.db.flush()
        await self.db.refresh(res)
        return res

    async def list_resources(self, modality_type: str | None = None) -> Sequence[ModalityResource]:
        stmt = select(ModalityResource).where(ModalityResource.is_active == True)
        if modality_type:
            stmt = stmt.where(ModalityResource.modality_type == modality_type)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def generate_modality_slots(self, data: ModalitySlotGenerate) -> list[ModalitySlot]:
        """Generate time slots for a modality resource over a date range."""
        res_result = await self.db.execute(
            select(ModalityResource).where(ModalityResource.id == data.resource_id)
        )
        resource = res_result.scalar_one_or_none()
        if not resource:
            raise ValueError("Resource not found")

        created: list[ModalitySlot] = []
        current_date = data.start_date
        while current_date <= data.end_date:
            slot_start = datetime.combine(current_date, resource.operating_start)
            slot_end_boundary = datetime.combine(current_date, resource.operating_end)
            duration = timedelta(minutes=resource.slot_duration_min)
            buffer = timedelta(minutes=resource.buffer_min)

            while slot_start + duration <= slot_end_boundary:
                s_end = slot_start + duration
                # Check if slot already exists
                existing = await self.db.execute(
                    select(ModalitySlot).where(
                        ModalitySlot.resource_id == data.resource_id,
                        ModalitySlot.slot_date == current_date,
                        ModalitySlot.start_time == slot_start.time(),
                    )
                )
                if not existing.scalar_one_or_none():
                    slot = ModalitySlot(
                        resource_id=data.resource_id,
                        slot_date=current_date,
                        start_time=slot_start.time(),
                        end_time=s_end.time(),
                    )
                    self.db.add(slot)
                    created.append(slot)
                slot_start = s_end + buffer
            current_date += timedelta(days=1)

        await self.db.flush()
        return created

    async def get_modality_slots(
        self, resource_id: uuid.UUID, slot_date: date
    ) -> Sequence[ModalitySlot]:
        stmt = select(ModalitySlot).where(
            ModalitySlot.resource_id == resource_id,
            ModalitySlot.slot_date == slot_date,
        ).order_by(ModalitySlot.start_time)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def book_modality_slot(self, data: ModalitySlotBook) -> ModalitySlot:
        """Book a specific modality slot for a patient."""
        stmt = select(ModalitySlot).where(
            ModalitySlot.resource_id == data.resource_id,
            ModalitySlot.slot_date == data.slot_date,
            ModalitySlot.start_time == data.start_time,
            ModalitySlot.status == SlotStatus.AVAILABLE,
        )
        result = await self.db.execute(stmt)
        slot = result.scalar_one_or_none()
        if not slot:
            raise ValueError("Modality slot not available")

        slot.patient_id = data.patient_id
        slot.imaging_order_id = data.imaging_order_id
        slot.technician_id = data.technician_id
        slot.notes = data.notes
        slot.status = SlotStatus.BOOKED
        await self.db.flush()
        await self.db.refresh(slot)
        return slot


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Reminder Service
# ═══════════════════════════════════════════════════════════════════════════════

class ReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reminder(self, data: ReminderCreate) -> AppointmentReminder:
        # Get booking to compute scheduled_at
        booking = await self.db.execute(
            select(SlotBooking).where(SlotBooking.id == data.booking_id)
        )
        booking_obj = booking.scalar_one_or_none()
        if not booking_obj:
            raise ValueError("Booking not found")

        # Get slot for exact time
        slot = await self.db.execute(
            select(CalendarSlot).where(CalendarSlot.id == booking_obj.slot_id)
        )
        slot_obj = slot.scalar_one_or_none()

        # Compute scheduled_at based on reminder type
        appt_datetime = datetime.combine(booking_obj.booking_date, slot_obj.start_time if slot_obj else time(9, 0))
        appt_datetime = appt_datetime.replace(tzinfo=timezone.utc)

        if data.reminder_type == "24h_before":
            scheduled_at = appt_datetime - timedelta(hours=24)
        elif data.reminder_type == "2h_before":
            scheduled_at = appt_datetime - timedelta(hours=2)
        else:
            scheduled_at = appt_datetime - timedelta(hours=24)

        reminder = AppointmentReminder(
            booking_id=data.booking_id,
            channel=data.channel,
            recipient=data.recipient,
            scheduled_at=scheduled_at,
            reminder_type=data.reminder_type,
        )
        self.db.add(reminder)
        await self.db.flush()
        await self.db.refresh(reminder)
        return reminder

    async def list_reminders(self, booking_id: uuid.UUID) -> Sequence[AppointmentReminder]:
        stmt = select(AppointmentReminder).where(
            AppointmentReminder.booking_id == booking_id
        ).order_by(AppointmentReminder.scheduled_at)
        result = await self.db.execute(stmt)
        return result.scalars().all()


# ═══════════════════════════════════════════════════════════════════════════════
# 8. Follow-Up Service
# ═══════════════════════════════════════════════════════════════════════════════

class FollowUpService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rule(self, data: FollowUpRuleCreate) -> FollowUpRule:
        rule = FollowUpRule(**data.model_dump())
        self.db.add(rule)
        await self.db.flush()
        await self.db.refresh(rule)
        return rule

    async def list_rules(self, department: str | None = None) -> Sequence[FollowUpRule]:
        stmt = select(FollowUpRule).where(FollowUpRule.is_active == True)
        if department:
            stmt = stmt.where(FollowUpRule.department == department)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def schedule_follow_up(
        self, original_booking_id: uuid.UUID, department: str
    ) -> SlotBooking | None:
        """Automatically schedule a follow-up based on rules."""
        rules = await self.list_rules(department)
        if not rules:
            return None

        rule = rules[0]
        original = await self.db.execute(
            select(SlotBooking).where(SlotBooking.id == original_booking_id)
        )
        original_booking = original.scalar_one_or_none()
        if not original_booking:
            return None

        follow_up_date = original_booking.booking_date + timedelta(days=rule.follow_up_days)

        # Find best available slot on follow-up date
        slot_stmt = select(CalendarSlot).where(
            CalendarSlot.doctor_id == original_booking.doctor_id,
            CalendarSlot.slot_date == follow_up_date,
            CalendarSlot.status == SlotStatus.AVAILABLE,
        ).order_by(CalendarSlot.start_time).limit(1)
        slot_result = await self.db.execute(slot_stmt)
        target_slot = slot_result.scalar_one_or_none()

        if not target_slot:
            return None

        booking_svc = BookingService(self.db)
        follow_up = await booking_svc.book_slot(BookingCreate(
            slot_id=target_slot.id,
            patient_id=original_booking.patient_id,
            doctor_id=original_booking.doctor_id,
            department=department,
            appointment_type=AppointmentType.FOLLOW_UP,
            reason=f"Follow-up for booking {original_booking_id}",
            is_follow_up=True,
            parent_booking_id=original_booking_id,
        ))
        return follow_up


# ═══════════════════════════════════════════════════════════════════════════════
# 9. Workload Balancing Service
# ═══════════════════════════════════════════════════════════════════════════════

class WorkloadBalancingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_doctor_workload(self, department: str, target_date: date) -> list[dict]:
        """Return workload summary for all doctors in a department on a date."""
        stmt = select(
            SlotBooking.doctor_id,
            func.count(SlotBooking.id).label("total_bookings"),
            func.count(case((SlotBooking.status == "completed", 1))).label("completed"),
            func.count(case((SlotBooking.status == "no_show", 1))).label("no_shows"),
        ).where(
            SlotBooking.department == department,
            SlotBooking.booking_date == target_date,
        ).group_by(SlotBooking.doctor_id)

        result = await self.db.execute(stmt)
        rows = result.all()
        return [
            {
                "doctor_id": str(row.doctor_id),
                "total_bookings": row.total_bookings,
                "completed": row.completed,
                "no_shows": row.no_shows,
                "load_pct": round((row.total_bookings / 20) * 100, 1),  # assume 20 slots/day
            }
            for row in rows
        ]

    async def suggest_doctor(self, department: str, target_date: date) -> uuid.UUID | None:
        """Suggest the least-loaded doctor for a new booking."""
        workloads = await self.get_doctor_workload(department, target_date)
        if not workloads:
            return None
        least_loaded = min(workloads, key=lambda w: w["total_bookings"])
        return uuid.UUID(least_loaded["doctor_id"])


# ═══════════════════════════════════════════════════════════════════════════════
# 10. Analytics Service
# ═══════════════════════════════════════════════════════════════════════════════

class SchedulingAnalyticsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def compute_daily_analytics(self, target_date: date, doctor_id: uuid.UUID | None = None) -> SchedulingAnalytics:
        """Compute and store daily analytics for a doctor or all doctors."""
        # Count slots
        slot_stmt = select(
            func.count(CalendarSlot.id).label("total"),
            func.count(case((CalendarSlot.status == SlotStatus.BOOKED, 1))).label("booked"),
            func.count(case((CalendarSlot.status == SlotStatus.AVAILABLE, 1))).label("available"),
            func.count(case((CalendarSlot.status == SlotStatus.BLOCKED, 1))).label("blocked"),
            func.count(case((CalendarSlot.status == SlotStatus.OVERBOOKED, 1))).label("overbooked"),
        ).where(CalendarSlot.slot_date == target_date)
        if doctor_id:
            slot_stmt = slot_stmt.where(CalendarSlot.doctor_id == doctor_id)
        slot_result = await self.db.execute(slot_stmt)
        slot_row = slot_result.one()

        # Count bookings
        book_stmt = select(
            func.count(SlotBooking.id).label("total"),
            func.count(case((SlotBooking.status == "completed", 1))).label("completed"),
            func.count(case((SlotBooking.status == "cancelled", 1))).label("cancelled"),
            func.count(case((SlotBooking.status == "no_show", 1))).label("no_show"),
        ).where(SlotBooking.booking_date == target_date)
        if doctor_id:
            book_stmt = book_stmt.where(SlotBooking.doctor_id == doctor_id)
        book_result = await self.db.execute(book_stmt)
        book_row = book_result.one()

        total_slots = slot_row.total or 1
        total_appts = book_row.total or 0

        analytics = SchedulingAnalytics(
            analytics_date=target_date,
            doctor_id=doctor_id,
            total_slots=slot_row.total,
            booked_slots=slot_row.booked,
            available_slots=slot_row.available,
            blocked_slots=slot_row.blocked,
            overbooked_slots=slot_row.overbooked,
            total_appointments=book_row.total,
            completed_appointments=book_row.completed,
            cancelled_appointments=book_row.cancelled,
            no_show_count=book_row.no_show,
            slot_utilization_pct=round((slot_row.booked / total_slots) * 100, 2) if total_slots else 0,
            doctor_utilization_pct=round((book_row.completed / total_appts) * 100, 2) if total_appts else 0,
            no_show_rate_pct=round((book_row.no_show / total_appts) * 100, 2) if total_appts else 0,
        )
        self.db.add(analytics)
        await self.db.flush()
        await self.db.refresh(analytics)
        return analytics

    async def get_analytics(
        self, from_date: date, to_date: date, doctor_id: uuid.UUID | None = None
    ) -> Sequence[SchedulingAnalytics]:
        stmt = select(SchedulingAnalytics).where(
            SchedulingAnalytics.analytics_date >= from_date,
            SchedulingAnalytics.analytics_date <= to_date,
        )
        if doctor_id:
            stmt = stmt.where(SchedulingAnalytics.doctor_id == doctor_id)
        stmt = stmt.order_by(SchedulingAnalytics.analytics_date)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_summary(self, from_date: date, to_date: date) -> dict:
        """Get aggregated summary across all doctors."""
        analytics = await self.get_analytics(from_date, to_date)
        if not analytics:
            return {
                "period_start": str(from_date), "period_end": str(to_date),
                "total_appointments": 0, "completed": 0, "cancelled": 0,
                "no_shows": 0, "no_show_rate_pct": 0,
                "avg_slot_utilization_pct": 0, "avg_doctor_utilization_pct": 0,
            }

        total_appts = sum(a.total_appointments for a in analytics)
        completed = sum(a.completed_appointments for a in analytics)
        cancelled = sum(a.cancelled_appointments for a in analytics)
        no_shows = sum(a.no_show_count for a in analytics)

        return {
            "period_start": str(from_date),
            "period_end": str(to_date),
            "total_appointments": total_appts,
            "completed": completed,
            "cancelled": cancelled,
            "no_shows": no_shows,
            "no_show_rate_pct": round((no_shows / total_appts) * 100, 2) if total_appts else 0,
            "avg_slot_utilization_pct": round(sum(a.slot_utilization_pct for a in analytics) / len(analytics), 2),
            "avg_doctor_utilization_pct": round(sum(a.doctor_utilization_pct for a in analytics) / len(analytics), 2),
        }
