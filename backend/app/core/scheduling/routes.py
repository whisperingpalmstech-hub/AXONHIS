"""
Enterprise Scheduling – API Routes
===================================
Prefix: /api/v1/scheduling
"""

import uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from app.dependencies import CurrentUser, DBSession

from app.core.scheduling.schemas import (
    DoctorCalendarCreate, DoctorCalendarUpdate, DoctorCalendarOut,
    SlotCreate, SlotBulkGenerate, SlotOut, SlotStatusUpdate,
    BookingCreate, BookingUpdate, BookingOut, EmergencyOverrideRequest,
    OverbookingConfigCreate, OverbookingConfigOut,
    CyclicScheduleCreate, CyclicScheduleOut,
    ModalityResourceCreate, ModalityResourceOut, ModalitySlotOut,
    ModalitySlotBook, ModalitySlotGenerate,
    ReminderCreate, ReminderOut,
    FollowUpRuleCreate, FollowUpRuleOut,
    SchedulingAnalyticsOut,
)
from app.core.scheduling.services import (
    DoctorCalendarService, SlotService, BookingService,
    OverbookingConfigService, CyclicScheduleService,
    ModalitySchedulingService, ReminderService, FollowUpService,
    WorkloadBalancingService, SchedulingAnalyticsService,
)

router = APIRouter(prefix="/scheduling", tags=["Enterprise Scheduling"])


# ─────────────────────── Doctor Calendars ────────────────────────────────────

@router.post("/calendars", response_model=DoctorCalendarOut, status_code=201)
async def create_calendar(data: DoctorCalendarCreate, db: DBSession, _: CurrentUser):
    svc = DoctorCalendarService(db)
    return await svc.create_calendar(data)


@router.get("/calendars", response_model=list[DoctorCalendarOut])
async def list_calendars(db: DBSession, _: CurrentUser, department: str | None = None):
    svc = DoctorCalendarService(db)
    return await svc.list_calendars(department)


@router.get("/calendars/{calendar_id}", response_model=DoctorCalendarOut)
async def get_calendar(calendar_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = DoctorCalendarService(db)
    cal = await svc.get_calendar(calendar_id)
    if not cal:
        raise HTTPException(404, "Calendar not found")
    return cal


@router.get("/calendars/doctor/{doctor_id}", response_model=DoctorCalendarOut)
async def get_doctor_calendar(doctor_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = DoctorCalendarService(db)
    cal = await svc.get_doctor_calendar(doctor_id)
    if not cal:
        raise HTTPException(404, "No active calendar for this doctor")
    return cal


@router.put("/calendars/{calendar_id}", response_model=DoctorCalendarOut)
async def update_calendar(calendar_id: uuid.UUID, data: DoctorCalendarUpdate, db: DBSession, _: CurrentUser):
    svc = DoctorCalendarService(db)
    try:
        return await svc.update_calendar(calendar_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ─────────────────────── Slots ───────────────────────────────────────────────

@router.post("/slots", response_model=SlotOut, status_code=201)
async def create_slot(data: SlotCreate, db: DBSession, _: CurrentUser):
    svc = SlotService(db)
    return await svc.create_slot(data)


@router.post("/slots/generate", response_model=list[SlotOut], status_code=201)
async def generate_slots(data: SlotBulkGenerate, db: DBSession, _: CurrentUser):
    """Generate slots from cyclic schedule templates."""
    svc = SlotService(db)
    try:
        slots = await svc.generate_slots_from_cyclic(data)
        return [SlotOut.model_validate(s) for s in slots]
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/slots/doctor/{doctor_id}", response_model=list[SlotOut])
async def get_doctor_slots(
    doctor_id: uuid.UUID, db: DBSession, _: CurrentUser,
    slot_date: date = Query(...), status: str | None = None,
):
    svc = SlotService(db)
    return await svc.get_doctor_slots(doctor_id, slot_date, status)


@router.get("/slots/available/{doctor_id}", response_model=list[SlotOut])
async def get_available_slots(
    doctor_id: uuid.UUID, db: DBSession, _: CurrentUser,
    from_date: date = Query(...), to_date: date = Query(...),
):
    svc = SlotService(db)
    return await svc.get_available_slots(doctor_id, from_date, to_date)


@router.put("/slots/{slot_id}/status", response_model=SlotOut)
async def update_slot_status(slot_id: uuid.UUID, data: SlotStatusUpdate, db: DBSession, _: CurrentUser):
    svc = SlotService(db)
    try:
        return await svc.update_slot_status(slot_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ─────────────────────── Bookings ────────────────────────────────────────────

@router.post("/bookings", response_model=BookingOut, status_code=201)
async def create_booking(data: BookingCreate, db: DBSession, _: CurrentUser):
    svc = BookingService(db)
    try:
        return await svc.book_slot(data)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/bookings/emergency", response_model=BookingOut, status_code=201)
async def emergency_override(data: EmergencyOverrideRequest, db: DBSession, _: CurrentUser):
    """Emergency slot override – bypasses capacity limits."""
    svc = BookingService(db)
    try:
        return await svc.emergency_override(data)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/bookings/{booking_id}", response_model=BookingOut)
async def get_booking(booking_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = BookingService(db)
    booking = await svc.get_booking(booking_id)
    if not booking:
        raise HTTPException(404, "Booking not found")
    return booking


@router.put("/bookings/{booking_id}", response_model=BookingOut)
async def update_booking(booking_id: uuid.UUID, data: BookingUpdate, db: DBSession, _: CurrentUser):
    svc = BookingService(db)
    try:
        return await svc.update_booking(booking_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))


@router.get("/bookings", response_model=list[BookingOut])
async def list_bookings(
    db: DBSession, _: CurrentUser,
    doctor_id: uuid.UUID | None = None, patient_id: uuid.UUID | None = None,
    from_date: date | None = None, to_date: date | None = None,
    status: str | None = None,
):
    svc = BookingService(db)
    return await svc.list_bookings(doctor_id, patient_id, from_date, to_date, status)


# ─────────────────────── Overbooking Config ──────────────────────────────────

@router.post("/overbooking", response_model=OverbookingConfigOut, status_code=201)
async def create_overbooking_config(data: OverbookingConfigCreate, db: DBSession, _: CurrentUser):
    svc = OverbookingConfigService(db)
    return await svc.create_config(data)


@router.get("/overbooking", response_model=list[OverbookingConfigOut])
async def list_overbooking_configs(db: DBSession, _: CurrentUser):
    svc = OverbookingConfigService(db)
    return await svc.list_configs()


# ─────────────────────── Cyclic Schedules ────────────────────────────────────

@router.post("/cyclic-schedules", response_model=CyclicScheduleOut, status_code=201)
async def create_cyclic_schedule(data: CyclicScheduleCreate, db: DBSession, _: CurrentUser):
    svc = CyclicScheduleService(db)
    return await svc.create_schedule(data)


@router.get("/cyclic-schedules/{calendar_id}", response_model=list[CyclicScheduleOut])
async def list_cyclic_schedules(calendar_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = CyclicScheduleService(db)
    return await svc.list_schedules(calendar_id)


@router.delete("/cyclic-schedules/{schedule_id}", status_code=204)
async def deactivate_cyclic_schedule(schedule_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = CyclicScheduleService(db)
    try:
        await svc.deactivate_schedule(schedule_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ─────────────────────── Modality Scheduling ─────────────────────────────────

@router.post("/modalities/resources", response_model=ModalityResourceOut, status_code=201)
async def create_modality_resource(data: ModalityResourceCreate, db: DBSession, _: CurrentUser):
    svc = ModalitySchedulingService(db)
    return await svc.create_resource(data)


@router.get("/modalities/resources", response_model=list[ModalityResourceOut])
async def list_modality_resources(
    db: DBSession, _: CurrentUser, modality_type: str | None = None,
):
    svc = ModalitySchedulingService(db)
    return await svc.list_resources(modality_type)


@router.post("/modalities/slots/generate", response_model=list[ModalitySlotOut], status_code=201)
async def generate_modality_slots(data: ModalitySlotGenerate, db: DBSession, _: CurrentUser):
    svc = ModalitySchedulingService(db)
    try:
        slots = await svc.generate_modality_slots(data)
        return [ModalitySlotOut.model_validate(s) for s in slots]
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/modalities/slots/{resource_id}", response_model=list[ModalitySlotOut])
async def get_modality_slots(
    resource_id: uuid.UUID, db: DBSession, _: CurrentUser,
    slot_date: date = Query(...),
):
    svc = ModalitySchedulingService(db)
    return await svc.get_modality_slots(resource_id, slot_date)


@router.post("/modalities/slots/book", response_model=ModalitySlotOut, status_code=201)
async def book_modality_slot(data: ModalitySlotBook, db: DBSession, _: CurrentUser):
    svc = ModalitySchedulingService(db)
    try:
        return await svc.book_modality_slot(data)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ─────────────────────── Reminders ───────────────────────────────────────────

@router.post("/reminders", response_model=ReminderOut, status_code=201)
async def create_reminder(data: ReminderCreate, db: DBSession, _: CurrentUser):
    svc = ReminderService(db)
    try:
        return await svc.create_reminder(data)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/reminders/{booking_id}", response_model=list[ReminderOut])
async def list_reminders(booking_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = ReminderService(db)
    return await svc.list_reminders(booking_id)


# ─────────────────────── Follow-Up Rules ─────────────────────────────────────

@router.post("/follow-up-rules", response_model=FollowUpRuleOut, status_code=201)
async def create_follow_up_rule(data: FollowUpRuleCreate, db: DBSession, _: CurrentUser):
    svc = FollowUpService(db)
    return await svc.create_rule(data)


@router.get("/follow-up-rules", response_model=list[FollowUpRuleOut])
async def list_follow_up_rules(db: DBSession, _: CurrentUser, department: str | None = None):
    svc = FollowUpService(db)
    return await svc.list_rules(department)


@router.post("/follow-up/{booking_id}/schedule", response_model=BookingOut | None)
async def schedule_follow_up(booking_id: uuid.UUID, department: str, db: DBSession, _: CurrentUser):
    svc = FollowUpService(db)
    result = await svc.schedule_follow_up(booking_id, department)
    if not result:
        raise HTTPException(404, "No available slot for follow-up")
    return result


# ─────────────────────── Workload Balancing ──────────────────────────────────

@router.get("/workload/{department}")
async def get_workload(
    department: str, db: DBSession, _: CurrentUser,
    target_date: date = Query(...),
):
    svc = WorkloadBalancingService(db)
    return await svc.get_doctor_workload(department, target_date)


@router.get("/workload/{department}/suggest-doctor")
async def suggest_doctor(
    department: str, db: DBSession, _: CurrentUser,
    target_date: date = Query(...),
):
    svc = WorkloadBalancingService(db)
    doctor_id = await svc.suggest_doctor(department, target_date)
    if not doctor_id:
        raise HTTPException(404, "No doctors available")
    return {"suggested_doctor_id": str(doctor_id)}


# ─────────────────────── Analytics ───────────────────────────────────────────

@router.post("/analytics/compute", response_model=SchedulingAnalyticsOut)
async def compute_analytics(
    db: DBSession, _: CurrentUser,
    target_date: date = Query(...),
    doctor_id: uuid.UUID | None = None,
):
    svc = SchedulingAnalyticsService(db)
    return await svc.compute_daily_analytics(target_date, doctor_id)


@router.get("/analytics", response_model=list[SchedulingAnalyticsOut])
async def get_analytics(
    db: DBSession, _: CurrentUser,
    from_date: date = Query(...), to_date: date = Query(...),
    doctor_id: uuid.UUID | None = None,
):
    svc = SchedulingAnalyticsService(db)
    return await svc.get_analytics(from_date, to_date, doctor_id)


@router.get("/analytics/summary")
async def get_analytics_summary(
    db: DBSession, _: CurrentUser,
    from_date: date = Query(...), to_date: date = Query(...),
):
    svc = SchedulingAnalyticsService(db)
    return await svc.get_summary(from_date, to_date)
