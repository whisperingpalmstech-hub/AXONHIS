from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.event_bus.schemas import (
    EventCreate,
    EventResponse,
    EventSubscriptionCreate,
    EventSubscriptionUpdate,
    EventSubscriptionResponse,
    EventSearchQuery,
    EventSearchResponse,
    EventProcessResult
)
from app.core.event_bus.services import EventBusService
from app.database import get_db

router = APIRouter(prefix="/event-bus", tags=["event-bus"])


@router.post("/events", response_model=EventResponse)
async def publish_event(
    event_data: EventCreate,
    db: AsyncSession = Depends(get_db)
):
    """Publish a new event to the event bus."""
    service = EventBusService(db)
    event = await service.publish_event(event_data)
    return event


@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific event."""
    service = EventBusService(db)
    event = await service.get_event(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/events/search", response_model=EventSearchResponse)
async def search_events(
    query: EventSearchQuery,
    db: AsyncSession = Depends(get_db)
):
    """Search events with filters."""
    service = EventBusService(db)
    events, total_count = await service.search_events(query)
    has_more = (query.offset + query.limit) < total_count
    return EventSearchResponse(
        events=events,
        total_count=total_count,
        has_more=has_more
    )


@router.post("/subscriptions", response_model=EventSubscriptionResponse)
async def create_subscription(
    subscription_data: EventSubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new event subscription."""
    service = EventBusService(db)
    subscription = await service.create_subscription(subscription_data)
    return subscription


@router.put("/subscriptions/{subscription_id}", response_model=EventSubscriptionResponse)
async def update_subscription(
    subscription_id: UUID,
    update_data: EventSubscriptionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update an existing subscription."""
    service = EventBusService(db)
    subscription = await service.update_subscription(subscription_id, update_data)
    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return subscription


@router.get("/subscriptions", response_model=List[EventSubscriptionResponse])
async def get_subscriptions(
    event_type: str = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db)
):
    """Get subscriptions, optionally filtered by event type."""
    service = EventBusService(db)
    subscriptions = await service.get_subscriptions(
        event_type=event_type,
        active_only=active_only
    )
    return subscriptions


@router.post("/events/retry-failed")
async def retry_failed_deliveries(
    max_retry_count: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db)
):
    """Retry failed event deliveries."""
    service = EventBusService(db)
    result = await service.retry_failed_deliveries(max_retry_count)
    return result


@router.post("/events/{event_id}/dead-letter")
async def move_to_dead_letter(
    event_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Move a failed event to dead letter queue."""
    service = EventBusService(db)
    dead_letter = await service.move_to_dead_letter(event_id)
    if not dead_letter:
        raise HTTPException(status_code=404, detail="Event not found")
    return dead_letter


@router.post("/events/process-pending")
async def process_pending_events(
    batch_size: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Process pending events in batch."""
    service = EventBusService(db)
    result = await service.process_pending_events(batch_size)
    return result
