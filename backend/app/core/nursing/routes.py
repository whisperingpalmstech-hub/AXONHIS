from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from .schemas import CoversheetDataOut, VitalCreate, VitalOut, NoteCreate, NoteOut
from .services import NursingService

router = APIRouter(prefix="/v1/nursing", tags=["Nursing IPD"])

@router.get("/coversheet/{admission_number}", response_model=CoversheetDataOut)
async def get_patient_coversheet(
    admission_number: str,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = NursingService(db)
    result = await service.get_coversheet(admission_number)
    return result

@router.post("/vitals", response_model=VitalOut)
async def log_patient_vitals(
    payload: VitalCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = NursingService(db)
    vital = await service.log_vitals(payload, user_uuid=current_user.id)
    return vital

@router.post("/notes", response_model=NoteOut)
async def log_clinical_note(
    payload: NoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = NursingService(db)
    note = await service.add_clinical_note(payload, user_uuid=current_user.id)
    return note
