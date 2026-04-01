"""IPD Enhancements — API Routes"""
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import CurrentUser
from .schemas import *
from .services import *

router = APIRouter(prefix="/ipd-enhanced", tags=["IPD Enhancements"])

# Estimates
@router.post("/estimates", response_model=AdmissionEstimateOut)
async def create_estimate(data: AdmissionEstimateCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await AdmissionEstimateService(db).create(data, user.id, user.org_id)

@router.get("/estimates", response_model=List[AdmissionEstimateOut])
async def list_estimates(user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await AdmissionEstimateService(db).list_estimates(user.org_id)

# Pre-Auth
@router.post("/pre-auth", response_model=PreAuthOut)
async def create_preauth(data: PreAuthCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await PreAuthService(db).create(data, user.id, user.org_id)

@router.post("/pre-auth/{pa_id}/respond", response_model=PreAuthOut)
async def respond_preauth(pa_id: uuid.UUID, data: PreAuthResponse, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await PreAuthService(db).respond(pa_id, data, user.org_id)

@router.get("/pre-auth", response_model=List[PreAuthOut])
async def list_preauths(user: CurrentUser, status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    return await PreAuthService(db).list_preauths(user.org_id, status)

# Discharge Summaries
@router.post("/discharge-summaries", response_model=DischargeSummaryOut)
async def create_discharge_summary(data: DischargeSummaryCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await DischargeSummaryService(db).create(data, user.id, user.org_id)

@router.post("/discharge-summaries/{ds_id}/approve", response_model=DischargeSummaryOut)
async def approve_discharge_summary(ds_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await DischargeSummaryService(db).approve(ds_id, user.id, user.org_id)

@router.get("/discharge-summaries/{admission_id}", response_model=DischargeSummaryOut)
async def get_discharge_summary(admission_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await DischargeSummaryService(db).get_by_admission(admission_id, user.org_id)

# Diet Orders
@router.post("/diet-orders", response_model=DietOrderOut)
async def create_diet_order(data: DietOrderCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    name = getattr(user, 'full_name', None) or getattr(user, 'email', 'Staff')
    return await DietOrderService(db).create(data, user.id, str(name), user.org_id)

@router.get("/diet-orders/{admission_id}", response_model=List[DietOrderOut])
async def list_diet_orders(admission_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await DietOrderService(db).list_active(admission_id, user.org_id)

# Consent Forms
@router.post("/consents", response_model=ConsentFormOut)
async def create_consent(data: ConsentFormCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    name = getattr(user, 'full_name', None) or getattr(user, 'email', 'Staff')
    return await ConsentFormService(db).create(data, user.id, str(name), user.org_id)

@router.get("/consents/{admission_id}", response_model=List[ConsentFormOut])
async def list_consents(admission_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)):
    return await ConsentFormService(db).list_consents(admission_id, user.org_id)
