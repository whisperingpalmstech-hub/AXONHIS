"""Router for order templates and order sets."""
import uuid
from fastapi import APIRouter, HTTPException, Query, status

from app.core.orders.templates.schemas import (
    OrderTemplateCreate, OrderTemplateOut,
    OrderSetCreate, OrderSetOut,
)
from app.core.orders.templates.services import OrderTemplateService, OrderSetService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(tags=["order-templates"])


# ── TEMPLATES ──────────────────────────────────────────────────────────────

@router.post("/order-templates", response_model=OrderTemplateOut, status_code=status.HTTP_201_CREATED)
async def create_template(data: OrderTemplateCreate, db: DBSession, user: CurrentUser):
    return await OrderTemplateService(db).create(data, created_by=user.id)


@router.get("/order-templates", response_model=list[OrderTemplateOut])
async def list_templates(db: DBSession, _: CurrentUser, q: str = Query(default="")):
    svc = OrderTemplateService(db)
    if q:
        return await svc.search(q)
    return await svc.list_all()


@router.get("/order-templates/{template_id}", response_model=OrderTemplateOut)
async def get_template(template_id: uuid.UUID, db: DBSession, _: CurrentUser):
    t = await OrderTemplateService(db).get_by_id(template_id)
    if not t:
        raise HTTPException(status_code=404, detail="Template not found")
    return t


# ── ORDER SETS ────────────────────────────────────────────────────────────

@router.post("/order-sets", response_model=OrderSetOut, status_code=status.HTTP_201_CREATED)
async def create_order_set(data: OrderSetCreate, db: DBSession, user: CurrentUser):
    return await OrderSetService(db).create(data, created_by=user.id)


@router.get("/order-sets", response_model=list[OrderSetOut])
async def list_order_sets(db: DBSession, _: CurrentUser):
    return await OrderSetService(db).list_all()


@router.get("/order-sets/{set_id}", response_model=OrderSetOut)
async def get_order_set(set_id: uuid.UUID, db: DBSession, _: CurrentUser):
    s = await OrderSetService(db).get_by_id(set_id)
    if not s:
        raise HTTPException(status_code=404, detail="Order set not found")
    return s
