import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from sqlalchemy import select
from .schemas import InsuranceClaimCreate, InsuranceClaimOut, InsuranceProviderCreate, InsuranceProviderOut
from .models import InsuranceClaim, InsuranceProvider

router = APIRouter(tags=["insurance-claims"])

@router.post("/insurance/claim", response_model=InsuranceClaimOut)
async def create_claim(data: InsuranceClaimCreate, db: DBSession, _: CurrentUser):
    claim = InsuranceClaim(**data.model_dump())
    db.add(claim)
    await db.flush()
    return claim

@router.get("/insurance/claims", response_model=list[InsuranceClaimOut])
async def list_claims(db: DBSession, _: CurrentUser):
    res = await db.execute(select(InsuranceClaim))
    return res.scalars().all()

@router.post("/insurance/providers", response_model=InsuranceProviderOut)
async def create_provider(data: InsuranceProviderCreate, db: DBSession, _: CurrentUser):
    provider = InsuranceProvider(**data.model_dump())
    db.add(provider)
    await db.flush()
    return provider

@router.get("/insurance/providers", response_model=list[InsuranceProviderOut])
async def list_providers(db: DBSession, _: CurrentUser):
    res = await db.execute(select(InsuranceProvider))
    return res.scalars().all()
