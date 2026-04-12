import uuid
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from .schemas import ImagingOrderCreate, ImagingOrderOut
from .services import ImagingOrderService
from typing import List

router = APIRouter()

@router.post("/order", response_model=ImagingOrderOut)
async def create_radiology_order(data: ImagingOrderCreate, db: DBSession, user: CurrentUser):
    return await ImagingOrderService(db).create_order(data, user.id)

@router.get("/orders", response_model=List[ImagingOrderOut])
async def list_radiology_orders(db: DBSession, user: CurrentUser, skip: int = 0, limit: int = 100):
    return await ImagingOrderService(db).list_orders(skip, limit)

@router.put("/orders/{order_id}/status", response_model=ImagingOrderOut)
async def update_radiology_order_status(order_id: uuid.UUID, status: str, db: DBSession, user: CurrentUser):
    return await ImagingOrderService(db).update_order_status(order_id, status)
