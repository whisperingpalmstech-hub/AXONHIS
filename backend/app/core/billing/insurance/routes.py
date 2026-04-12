import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from app.dependencies import DBSession, CurrentUser
from .schemas import (
    InsuranceClaimCreate, InsuranceClaimOut, InsuranceClaimUpdate,
    InsuranceProviderCreate, InsuranceProviderOut,
    InsurancePackageCreate, InsurancePackageOut,
    InsurancePolicyCreate, InsurancePolicyOut,
    PreAuthorizationCreate, PreAuthorizationOut, PreAuthorizationUpdate
)
from .services import InsuranceService
from .models import InsuranceClaim
from sqlalchemy import select
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/insurance", tags=["Insurance & Claims"])

# --- Providers ---
@router.post("/providers", response_model=InsuranceProviderOut)
async def create_provider(data: InsuranceProviderCreate, db: DBSession, _: CurrentUser):
    return await InsuranceService.create_provider(db, data.model_dump())

@router.get("/providers", response_model=List[InsuranceProviderOut])
async def list_providers(db: DBSession, _: CurrentUser):
    return await InsuranceService.list_providers(db)

# --- Packages ---
@router.post("/packages", response_model=InsurancePackageOut)
async def create_package(data: InsurancePackageCreate, db: DBSession, _: CurrentUser):
    return await InsurancePackageOut.model_validate(await InsuranceService.create_package(db, data.model_dump()))

@router.get("/packages", response_model=List[InsurancePackageOut])
async def list_packages(db: DBSession, _: CurrentUser, provider_id: Optional[uuid.UUID] = None):
    return await InsuranceService.list_packages(db, provider_id)

# --- Policies ---
@router.post("/policies", response_model=InsurancePolicyOut)
async def create_policy(data: InsurancePolicyCreate, db: DBSession, _: CurrentUser):
    return await InsuranceService.create_policy(db, data.model_dump())

@router.get("/policies/patient/{patient_id}", response_model=List[InsurancePolicyOut])
async def list_patient_policies(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    return await InsuranceService.get_patient_policies(db, patient_id)

# --- Pre-Auth ---
@router.post("/pre-auth", response_model=PreAuthorizationOut)
async def create_pre_auth(data: PreAuthorizationCreate, db: DBSession, _: CurrentUser):
    return await InsuranceService.create_pre_auth(db, data.model_dump())

@router.patch("/pre-auth/{auth_id}", response_model=PreAuthorizationOut)
async def update_pre_auth(auth_id: uuid.UUID, data: PreAuthorizationUpdate, db: DBSession, _: CurrentUser):
    return await InsuranceService.update_pre_auth(db, auth_id, data.model_dump(exclude_unset=True))

# --- Claims ---
@router.post("/claims", response_model=InsuranceClaimOut)
async def create_claim(data: InsuranceClaimCreate, db: DBSession, _: CurrentUser):
    claim_data = data.model_dump(exclude={"items"})
    items_data = [item.model_dump() for item in data.items]
    return await InsuranceService.create_claim(db, claim_data, items_data)

@router.get("/claims", response_model=List[InsuranceClaimOut])
async def list_claims(db: DBSession, _: CurrentUser):
    stmt = (
        select(InsuranceClaim)
        .options(selectinload(InsuranceClaim.items))
        .order_by(InsuranceClaim.submitted_at.desc())
    )
    res = await db.execute(stmt)
    return res.scalars().all()
