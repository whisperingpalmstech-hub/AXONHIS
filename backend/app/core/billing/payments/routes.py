import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from sqlalchemy import select
from .schemas import PaymentCreate, PaymentOut
from .models import Payment
from .services import PaymentService

router = APIRouter(tags=["payments"])

@router.post("/payment", response_model=PaymentOut)
async def create_payment(data: PaymentCreate, db: DBSession, user: CurrentUser):
    svc = PaymentService(db)
    return await svc.process_payment(data, user.id)

@router.get("/payments", response_model=list[PaymentOut])
async def list_payments(db: DBSession, _: CurrentUser):
    res = await db.execute(select(Payment))
    return res.scalars().all()
