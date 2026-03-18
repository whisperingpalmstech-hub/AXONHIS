import pytest
import uuid
from datetime import datetime, timezone, timedelta
from app.core.ot.surgery_schedule.models import SurgeryStatus
from app.core.ot.surgery_schedule.schemas import SurgeryScheduleCreate
from app.core.ot.surgery_schedule.services import SurgeryScheduleService
from app.core.ot.surgical_teams.schemas import SurgicalTeamCreate
from app.core.ot.surgical_teams.services import SurgicalTeamService
from app.core.ot.surgery_events.schemas import SurgeryEventCreate
from app.core.ot.surgery_events.models import SurgeryEventType
from app.core.ot.surgery_events.services import SurgeryEventService
from app.core.encounters.models import Encounter, EncounterStatus
from app.core.ot.operating_rooms.models import OperatingRoom
from app.core.ot.surgical_procedures.models import SurgicalProcedure


@pytest.mark.asyncio
async def test_full_surgery_workflow(db):
    # 1. Setup Environment
    patient_id = uuid.uuid4()
    encounter = Encounter(patient_id=patient_id, encounter_type="IPD", status=EncounterStatus.ACTIVE)
    db.add(encounter)
    room = OperatingRoom(room_code="OR-Workflow", room_name="Workflow Room", department="Surgery")
    db.add(room)
    proc = SurgicalProcedure(procedure_code="WF", procedure_name="Workflow Proc", specialty="General", expected_duration=60, billing_code="WF1")
    db.add(proc)
    await db.commit()
    await db.refresh(encounter)
    await db.refresh(room)
    await db.refresh(proc)

    # 2. Schedule Surgery
    schedule_in = SurgeryScheduleCreate(
        patient_id=patient_id,
        encounter_id=encounter.id,
        procedure_id=proc.id,
        operating_room_id=room.id,
        scheduled_start_time=datetime.now(timezone.utc) + timedelta(hours=1),
        scheduled_end_time=datetime.now(timezone.utc) + timedelta(hours=2)
    )
    schedule = await SurgeryScheduleService.schedule_surgery(db, schedule_in)
    assert schedule.status == SurgeryStatus.SCHEDULED

    # 3. Assign Team
    team_in = SurgicalTeamCreate(
        schedule_id=schedule.id,
        lead_surgeon_id=uuid.uuid4() # Mock surgeon
    )
    team = await SurgicalTeamService.assign_team(db, team_in)
    assert team.schedule_id == schedule.id

    # 4. Start Procedure (Patient In Room)
    event_in = SurgeryEventCreate(
        schedule_id=schedule.id,
        event_type=SurgeryEventType.PATIENT_IN_ROOM
    )
    await SurgeryEventService.record_event(db, event_in)
    await db.refresh(schedule)
    assert schedule.status == "preparing"

    # 5. Incision Made
    event_incision = SurgeryEventCreate(
        schedule_id=schedule.id,
        event_type=SurgeryEventType.INCISION_MADE
    )
    await SurgeryEventService.record_event(db, event_incision)
    await db.refresh(schedule)
    assert schedule.status == "in_progress"

    # 6. Complete Procedure
    event_complete = SurgeryEventCreate(
        schedule_id=schedule.id,
        event_type=SurgeryEventType.PROCEDURE_COMPLETED
    )
    await SurgeryEventService.record_event(db, event_complete)
    await db.refresh(schedule)
    assert schedule.status == "completed"

    # 7. Verify Side Effects (Timeline, Billing)
    # Check if billing entries were created
    from app.core.billing.billing_entries.models import BillingEntry
    from sqlalchemy import select
    result = await db.execute(select(BillingEntry).where(BillingEntry.encounter_id == encounter.id))
    charges = result.scalars().all()
    assert len(charges) > 0
