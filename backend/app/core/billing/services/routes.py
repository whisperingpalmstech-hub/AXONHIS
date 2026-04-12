import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from sqlalchemy import select
from .schemas import BillingServiceCreate, BillingServiceOut
from .models import BillingService

router = APIRouter(tags=["billing-services"])

@router.post("/services", response_model=BillingServiceOut)
async def create_service(data: BillingServiceCreate, db: DBSession, _: CurrentUser):
    service = BillingService(**data.model_dump())
    db.add(service)
    await db.flush()
    return service

@router.get("/services", response_model=list[BillingServiceOut])
async def list_services(db: DBSession, _: CurrentUser):
    res = await db.execute(select(BillingService))
    return res.scalars().all()
