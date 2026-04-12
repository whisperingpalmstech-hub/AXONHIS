import uuid
from fastapi import APIRouter, status
from app.dependencies import DBSession, CurrentUser
from .schemas import ClinicalAlertCreate, ClinicalAlertOut
from .services import AlertService

router = APIRouter(prefix="/alert", tags=["Communication - Alerts"])

@router.post("/", response_model=ClinicalAlertOut, status_code=status.HTTP_201_CREATED)
async def create_alert(data: ClinicalAlertCreate, db: DBSession, _: CurrentUser) -> ClinicalAlertOut:
    return await AlertService.create_alert(db, data)

@router.get("/", response_model=list[ClinicalAlertOut])
async def get_alerts(db: DBSession, _: CurrentUser) -> list[ClinicalAlertOut]:
    return await AlertService.get_alerts(db)

@router.get("/patient/{patient_id}", response_model=list[ClinicalAlertOut])
async def get_patient_alerts(patient_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[ClinicalAlertOut]:
    return await AlertService.get_patient_alerts(db, patient_id)

@router.put("/{alert_id}/acknowledge", response_model=ClinicalAlertOut)
async def acknowledge_alert(alert_id: uuid.UUID, db: DBSession, user: CurrentUser) -> ClinicalAlertOut:
    return await AlertService.acknowledge_alert(db, alert_id, user.id)
