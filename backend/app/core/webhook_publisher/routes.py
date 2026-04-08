from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.webhook_publisher.schemas import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookDeliveryResponse,
    WebhookEventPayload
)
from app.core.webhook_publisher.services import WebhookPublisherService
from app.database import get_db

router = APIRouter(prefix="/webhook-publisher", tags=["webhook-publisher"])


@router.post("/subscriptions", response_model=WebhookSubscriptionResponse)
async def create_subscription(
    subscription_data: WebhookSubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new webhook subscription."""
    service = WebhookPublisherService(db)
    subscription = await service.create_subscription(subscription_data)
    return subscription


@router.put("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    update_data: WebhookSubscriptionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing webhook subscription."""
    service = WebhookPublisherService(db)
    subscription = await service.update_subscription(subscription_id, update_data)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.get("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_subscription(
    subscription_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific webhook subscription."""
    service = WebhookPublisherService(db)
    subscription = await service.get_subscription(subscription_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
async def list_subscriptions(
    event_type: str = Query(None),
    status: str = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """List webhook subscriptions with filters."""
    service = WebhookPublisherService(db)
    subscriptions = await service.list_subscriptions(
        event_type=event_type,
        status=status
    )
    return subscriptions


@router.post("/events/publish")
async def publish_event(
    event_type: str,
    payload: WebhookEventPayload,
    db: AsyncSession = Depends(get_db)
):
    """Publish an event to all matching webhook subscriptions."""
    service = WebhookPublisherService(db)
    results = await service.publish_event(event_type, payload)
    return results


@router.get("/subscriptions/{subscription_id}/deliveries", response_model=List[WebhookDeliveryResponse])
async def get_delivery_history(
    subscription_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get delivery history for a subscription."""
    service = WebhookPublisherService(db)
    deliveries = await service.get_delivery_history(subscription_id, limit)
    return deliveries


@router.post("/deliveries/retry-failed")
async def retry_failed_deliveries(
    db: AsyncSession = Depends(get_db)
):
    """Retry failed webhook deliveries that are due for retry."""
    service = WebhookPublisherService(db)
    results = await service.retry_failed_deliveries()
    return results
