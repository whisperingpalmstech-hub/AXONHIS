import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from sqlalchemy import select
from .schemas import ServiceTariffCreate, ServiceTariffOut
from .models import ServiceTariff

router = APIRouter(tags=["billing-tariffs"])

@router.post("/tariffs", response_model=ServiceTariffOut)
async def create_tariff(data: ServiceTariffCreate, db: DBSession, _: CurrentUser):
    tariff = ServiceTariff(**data.model_dump())
    db.add(tariff)
    await db.flush()
    return tariff

@router.get("/tariffs", response_model=list[ServiceTariffOut])
async def list_tariffs(db: DBSession, _: CurrentUser):
    res = await db.execute(select(ServiceTariff))
    return res.scalars().all()
