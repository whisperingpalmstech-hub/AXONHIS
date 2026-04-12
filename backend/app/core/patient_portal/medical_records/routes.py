from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import DBSession
from .services import MedicalRecordService
import uuid

router = APIRouter(prefix="/medical-records", tags=["Patient Portal - Records"])

@router.get("/lab-results")
async def get_lab_results(db: DBSession, patient_id: str):
    try:
        records = await MedicalRecordService.get_patient_lab_records(db, uuid.UUID(patient_id))
        return [{k: str(v) for k, v in r.__dict__.items() if not k.startswith('_')} for r in records]
    except Exception as e:
        return {"error": str(e), "trace": repr(e)}

@router.get("/prescriptions")
async def get_prescriptions(db: DBSession, patient_id: str):
    records = await MedicalRecordService.get_patient_prescriptions(db, uuid.UUID(patient_id))
    return [{k: str(v) for k, v in r.__dict__.items() if not k.startswith('_')} for r in records]

@router.get("/encounters")
async def get_encounters(db: DBSession, patient_id: str):
    records = await MedicalRecordService.get_patient_encounters(db, uuid.UUID(patient_id))
    return [{k: str(v) for k, v in r.__dict__.items() if not k.startswith('_')} for r in records]

@router.get("/documents")
async def get_documents(db: DBSession, patient_id: str):
    records = await MedicalRecordService.get_patient_documents(db, uuid.UUID(patient_id))
    return [{k: str(v) for k, v in r.__dict__.items() if not k.startswith('_')} for r in records]
