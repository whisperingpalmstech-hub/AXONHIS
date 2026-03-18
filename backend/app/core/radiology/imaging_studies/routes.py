import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import ImagingStudyCreate, ImagingStudyOut
from .services import ImagingStudyService
from typing import List

router = APIRouter()

@router.post("/studies", response_model=ImagingStudyOut, status_code=201)
async def create_imaging_study(data: ImagingStudyCreate, db: DBSession, user: CurrentUser):
    return await ImagingStudyService(db).create_study(data)


@router.post("/start-study", response_model=ImagingStudyOut)
async def start_study(study_id: uuid.UUID, machine_id: str, db: DBSession, user: CurrentUser):
    return await ImagingStudyService(db).start_study(study_id, machine_id, user.id)

@router.post("/complete-study", response_model=ImagingStudyOut)
async def complete_study(study_id: uuid.UUID, db: DBSession, user: CurrentUser):
    return await ImagingStudyService(db).complete_study(study_id, user.id)

@router.get("/studies", response_model=List[ImagingStudyOut])
async def list_imaging_studies(db: DBSession, user: CurrentUser, skip: int = 0, limit: int = 100):
    return await ImagingStudyService(db).list_studies(skip, limit)
