import uuid
from fastapi import APIRouter, status, HTTPException
from app.core.encounters.diagnoses.schemas import EncounterDiagnosisCreate, EncounterDiagnosisOut
from app.core.encounters.diagnoses.services import DiagnosisService
from app.core.encounters.timeline.services import TimelineService
from app.core.encounters.timeline.schemas import EncounterTimelineCreate
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/encounters/{encounter_id}/diagnoses", tags=["encounters-diagnoses"])

@router.post("/", response_model=EncounterDiagnosisOut, status_code=status.HTTP_201_CREATED)
async def add_diagnosis(encounter_id: uuid.UUID, data: EncounterDiagnosisCreate, db: DBSession, user: CurrentUser):
    service = DiagnosisService(db)
    diagnosis = await service.add_diagnosis(encounter_id, data)
    
    ts = TimelineService(db)
    await ts.add_event(encounter_id, user.id, EncounterTimelineCreate(
        event_type="diagnosis_assigned",
        description=f"Assigned {data.diagnosis_type} diagnosis: {data.diagnosis_description} ({data.diagnosis_code})"
    ))

    return diagnosis

@router.get("/", response_model=list[EncounterDiagnosisOut])
async def list_diagnoses(encounter_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await DiagnosisService(db).list_diagnoses(encounter_id)
