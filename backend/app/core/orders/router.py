"""Orders router – create, approve, cancel, list orders."""
import uuid

from fastapi import APIRouter, HTTPException, Query, status

from app.core.billing.billing_entries.services import BillingEntryService as BillingService
from app.core.events.models import EventType
from app.core.events.services import EventService
from app.core.orders.catalog import search_catalog
from app.core.orders.schemas import OrderApprove, OrderCancel, OrderCreate, OrderOut
from app.core.orders.services import OrderService
from app.core.tasks.services import TaskService
from app.dependencies import CurrentUser, DBSession
from app.core.orders.templates.router import router as templates_router

router = APIRouter(prefix="/orders", tags=["orders"])
router.include_router(templates_router)

@router.get("/catalog/search")
async def search_order_catalog(
    q: str = Query(..., min_length=2),
    order_type: str | None = Query(None),
    _: CurrentUser = None
):
    """Search clinical catalog for lab tests, medications, imaging, and procedures."""
    return search_catalog(query=q, order_type=order_type)


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
async def create_order(data: OrderCreate, db: DBSession, user: CurrentUser) -> OrderOut:
    service = OrderService(db)
    order = await service.create(data, ordered_by=user.id)
    await EventService(db).emit(
        EventType.ORDER_CREATED,
        summary=f"{order.order_type} order created",
        patient_id=order.patient_id,
        encounter_id=order.encounter_id,
        actor_id=user.id,
        payload={"order_id": str(order.id), "type": order.order_type},
    )
    loaded = await service.get_by_id(order.id)
    return OrderOut.model_validate(loaded)


@router.get("/encounter/{encounter_id}", response_model=list[OrderOut])
async def list_orders(encounter_id: uuid.UUID, db: DBSession, _: CurrentUser) -> list[OrderOut]:
    orders = await OrderService(db).list_by_encounter(encounter_id)
    return [OrderOut.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderOut)
async def get_order(order_id: uuid.UUID, db: DBSession, _: CurrentUser) -> OrderOut:
    order = await OrderService(db).get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderOut.model_validate(order)


@router.post("/{order_id}/approve", response_model=OrderOut)
async def approve_order(
    order_id: uuid.UUID, data: OrderApprove, db: DBSession, user: CurrentUser
) -> OrderOut:
    """Approve an order → generates tasks + billing entries."""
    service = OrderService(db)
    order = await service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order = await service.approve(order, approved_by=user.id, notes=data.notes)

    # Trigger task generation and billing in sequence
    await TaskService(db).generate_tasks_for_order(order, user_id=user.id)
    await BillingService(db).create_entry_from_order(order)

    await EventService(db).emit(
        EventType.ORDER_APPROVED,
        summary=f"{order.order_type} order approved",
        patient_id=order.patient_id,
        encounter_id=order.encounter_id,
        actor_id=user.id,
        payload={"order_id": str(order.id)},
    )
    return OrderOut.model_validate(order)


@router.post("/{order_id}/cancel", response_model=OrderOut)
async def cancel_order(
    order_id: uuid.UUID, data: OrderCancel, db: DBSession, user: CurrentUser
) -> OrderOut:
    """Cancel an order → reverses billing entry."""
    service = OrderService(db)
    order = await service.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order = await service.cancel(order, reason=data.reason)
    await BillingService(db).reverse_entry_from_order(order)

    await EventService(db).emit(
        EventType.ORDER_CANCELLED,
        summary=f"{order.order_type} order cancelled: {data.reason}",
        patient_id=order.patient_id,
        encounter_id=order.encounter_id,
        actor_id=user.id,
        payload={"order_id": str(order.id), "reason": data.reason},
    )
    return OrderOut.model_validate(order)
