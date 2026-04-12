import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.core.ot.surgery_schedule.models import SurgerySchedule, SurgeryStatus, SurgeryPriority
from app.core.ot.surgery_schedule.schemas import SurgeryScheduleCreate
from app.core.ot.surgery_schedule.services import SurgeryScheduleService
from app.core.encounters.models import Encounter, EncounterStatus
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_schedule_surgery_success(db):
    # Setup: Create patient and encounter (mocked or actual if db is real)
    # For this test, we assume db provides a session and we manually insert dependency records
    patient_id = uuid.uuid4()
    encounter = Encounter(
        patient_id=patient_id,
        encounter_type="IPD",
        status=EncounterStatus.ACTIVE
    )
    db.add(encounter)
    await db.commit()
    await db.refresh(encounter)

    # Room and Procedure IDs (placeholders)
    room_id = uuid.uuid4()
    procedure_id = uuid.uuid4()

    schedule_in = SurgeryScheduleCreate(
        patient_id=patient_id,
        encounter_id=encounter.id,
        procedure_id=procedure_id,
        operating_room_id=room_id,
        scheduled_start_time=datetime.now(timezone.utc) + timedelta(days=1),
        scheduled_end_time=datetime.now(timezone.utc) + timedelta(days=1, hours=2),
        priority=SurgeryPriority.ELECTIVE,
        status=SurgeryStatus.SCHEDULED
    )

    # We need to mock the overlap check or ensure no overlaps exist
    # Since it's a fresh DB for tests, it should be fine.
    
    # Note: We'd also need an OperatingRoom record if foreign keys are enforced
    from app.core.ot.operating_rooms.models import OperatingRoom
    room = OperatingRoom(
        id=room_id,
        room_code="OR-101",
        room_name="Test OR 1",
        department="Surgery"
    )
    db.add(room)
    
    from app.core.ot.surgical_procedures.models import SurgicalProcedure
    proc = SurgicalProcedure(
        id=procedure_id,
        procedure_code="APP",
        procedure_name="Appendectomy",
        specialty="General",
        expected_duration=60,
        billing_code="B001"
    )
    db.add(proc)
    await db.commit()

    schedule = await SurgeryScheduleService.schedule_surgery(db, schedule_in)
    assert schedule.id is not None
    assert schedule.status == SurgeryStatus.SCHEDULED


@pytest.mark.asyncio
async def test_schedule_surgery_overlap_conflict(db):
    # Setup similar to above
    patient_id = uuid.uuid4()
    encounter_id = uuid.uuid4()
    room_id = uuid.uuid4()
    procedure_id = uuid.uuid4()
    
    start_time = datetime.now(timezone.utc) + timedelta(days=2)
    end_time = start_time + timedelta(hours=2)

    # Create existing schedule
    existing = SurgerySchedule(
        patient_id=patient_id,
        encounter_id=encounter_id,
        procedure_id=procedure_id,
        operating_room_id=room_id,
        scheduled_start_time=start_time,
        scheduled_end_time=end_time,
        status=SurgeryStatus.SCHEDULED
    )
    db.add(existing)
    await db.commit()

    # Try to schedule overlapping
    new_schedule_in = SurgeryScheduleCreate(
        patient_id=patient_id,
        encounter_id=encounter_id,
        procedure_id=procedure_id,
        operating_room_id=room_id,
        scheduled_start_time=start_time + timedelta(minutes=30),
        scheduled_end_time=end_time + timedelta(minutes=30),
        priority=SurgeryPriority.ELECTIVE
    )

    with pytest.raises(HTTPException) as excinfo:
        await SurgeryScheduleService.schedule_surgery(db, new_schedule_in)
    assert excinfo.value.status_code == 409
