from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update
from sqlalchemy.orm import selectinload

from app.core.event_bus.models import (
    MdEvent,
    MdEventSubscription,
    MdEventDelivery,
    MdEventDeadLetter,
    EventStatus,
    EventType
)
from app.core.event_bus.schemas import (
    EventCreate,
    EventSubscriptionCreate,
    EventSubscriptionUpdate,
    EventSearchQuery
)


class EventBusService:
    """Service for managing event bus operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def publish_event(
        self,
        event_data: EventCreate
    ) -> MdEvent:
        """Publish a new event to the event bus."""
        event = MdEvent(
            event_type=event_data.event_type,
            event_name=event_data.event_name,
            event_version=event_data.event_version,
            correlation_id=event_data.correlation_id,
            causation_id=event_data.causation_id,
            source_system=event_data.source_system,
            source_type=event_data.source_type,
            aggregate_id=event_data.aggregate_id,
            aggregate_type=event_data.aggregate_type,
            payload=event_data.payload,
            metadata=event_data.metadata,
            expires_at=event_data.expires_at
        )
        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)
        
        # Trigger event delivery to subscribers
        await self._deliver_event(event)
        
        return event

    async def get_event(
        self,
        event_id: uuid.UUID
    ) -> Optional[MdEvent]:
        """Get a specific event."""
        query = select(MdEvent).where(MdEvent.event_id == event_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def search_events(
        self,
        query: EventSearchQuery
    ) -> tuple[List[MdEvent], int]:
        """Search events with filters."""
        conditions = []
        
        if query.event_type:
            conditions.append(MdEvent.event_type == query.event_type)
        
        if query.status:
            conditions.append(MdEvent.status == query.status)
        
        if query.correlation_id:
            conditions.append(MdEvent.correlation_id == query.correlation_id)
        
        if query.aggregate_id:
            conditions.append(MdEvent.aggregate_id == query.aggregate_id)
        
        if query.source_system:
            conditions.append(MdEvent.source_system == query.source_system)
        
        if query.start_date:
            conditions.append(MdEvent.created_at >= query.start_date)
        
        if query.end_date:
            conditions.append(MdEvent.created_at <= query.end_date)
        
        # Get total count
        count_query = select(func.count(MdEvent.event_id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()
        
        # Get paginated results
        events_query = select(MdEvent)
        if conditions:
            events_query = events_query.where(and_(*conditions))
        
        events_query = events_query.order_by(desc(MdEvent.created_at)).offset(
            query.offset
        ).limit(query.limit)
        
        events_result = await self.db.execute(events_query)
        events = events_result.scalars().all()
        
        return list(events), total_count

    async def create_subscription(
        self,
        subscription_data: EventSubscriptionCreate
    ) -> MdEventSubscription:
        """Create a new event subscription."""
        subscription = MdEventSubscription(
            subscriber_name=subscription_data.subscriber_name,
            subscriber_type=subscription_data.subscriber_type,
            event_types=subscription_data.event_types,
            endpoint_url=subscription_data.endpoint_url,
            queue_name=subscription_data.queue_name,
            service_name=subscription_data.service_name,
            filter_rules=subscription_data.filter_rules,
            retry_policy=subscription_data.retry_policy
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def update_subscription(
        self,
        subscription_id: uuid.UUID,
        update_data: EventSubscriptionUpdate
    ) -> Optional[MdEventSubscription]:
        """Update an existing subscription."""
        query = select(MdEventSubscription).where(
            MdEventSubscription.subscription_id == subscription_id
        )
        result = await self.db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        if update_data.event_types is not None:
            subscription.event_types = update_data.event_types
        if update_data.endpoint_url is not None:
            subscription.endpoint_url = update_data.endpoint_url
        if update_data.queue_name is not None:
            subscription.queue_name = update_data.queue_name
        if update_data.service_name is not None:
            subscription.service_name = update_data.service_name
        if update_data.filter_rules is not None:
            subscription.filter_rules = update_data.filter_rules
        if update_data.retry_policy is not None:
            subscription.retry_policy = update_data.retry_policy
        if update_data.active_flag is not None:
            subscription.active_flag = update_data.active_flag
        
        subscription.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(subscription)
        return subscription

    async def get_subscriptions(
        self,
        event_type: Optional[str] = None,
        active_only: bool = True
    ) -> List[MdEventSubscription]:
        """Get subscriptions, optionally filtered by event type."""
        conditions = []
        
        if event_type:
            conditions.append(MdEventSubscription.event_types.contains([event_type]))
        
        if active_only:
            conditions.append(MdEventSubscription.active_flag == True)
        
        query = select(MdEventSubscription)
        if conditions:
            query = query.where(and_(*conditions))
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _deliver_event(
        self,
        event: MdEvent
    ) -> Dict[str, int]:
        """Deliver event to all matching subscribers."""
        # Get matching subscriptions
        subscriptions = await self.get_subscriptions(
            event_type=event.event_type,
            active_only=True
        )
        
        delivered_count = 0
        failed_count = 0
        
        for subscription in subscriptions:
            delivery = MdEventDelivery(
                event_id=event.event_id,
                subscription_id=subscription.subscription_id,
                status="PENDING"
            )
            self.db.add(delivery)
            await self.db.commit()
            await self.db.refresh(delivery)
            
            # Deliver based on subscription type
            try:
                if subscription.subscriber_type == "webhook":
                    await self._deliver_to_webhook(event, subscription, delivery)
                    delivered_count += 1
                elif subscription.subscriber_type == "service":
                    await self._deliver_to_service(event, subscription, delivery)
                    delivered_count += 1
                elif subscription.subscriber_type == "queue":
                    await self._deliver_to_queue(event, subscription, delivery)
                    delivered_count += 1
            except Exception as e:
                delivery.status = "FAILED"
                delivery.error_message = str(e)
                delivery.last_attempt_at = datetime.utcnow()
                failed_count += 1
                await self.db.commit()
        
        # Update event status
        if delivered_count > 0 and failed_count == 0:
            event.status = EventStatus.PROCESSED
            event.processed_at = datetime.utcnow()
        elif failed_count > 0:
            event.status = EventStatus.FAILED
        
        await self.db.commit()
        return {"delivered": delivered_count, "failed": failed_count}

    async def _deliver_to_webhook(
        self,
        event: MdEvent,
        subscription: MdEventSubscription,
        delivery: MdEventDelivery
    ):
        """Deliver event to webhook endpoint."""
        if not subscription.endpoint_url:
            raise ValueError("Webhook endpoint URL not configured")
        
        payload = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "event_name": event.event_name,
            "event_version": event.event_version,
            "correlation_id": event.correlation_id,
            "causation_id": event.causation_id,
            "source_system": event.source_system,
            "source_type": event.source_type,
            "aggregate_id": str(event.aggregate_id) if event.aggregate_id else None,
            "aggregate_type": event.aggregate_type,
            "payload": event.payload,
            "metadata": event.metadata,
            "created_at": event.created_at.isoformat()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                subscription.endpoint_url,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
        
        delivery.status = "DELIVERED"
        delivery.delivered_at = datetime.utcnow()
        delivery.response_data = {"status_code": response.status_code}
        await self.db.commit()

    async def _deliver_to_service(
        self,
        event: MdEvent,
        subscription: MdEventSubscription,
        delivery: MdEventDelivery
    ):
        """Deliver event to internal service (mock implementation)."""
        # In a real implementation, this would call the service directly
        # For now, we'll just mark as delivered
        delivery.status = "DELIVERED"
        delivery.delivered_at = datetime.utcnow()
        delivery.response_data = {"service": subscription.service_name}
        await self.db.commit()

    async def _deliver_to_queue(
        self,
        event: MdEvent,
        subscription: MdEventSubscription,
        delivery: MdEventDelivery
    ):
        """Deliver event to message queue (mock implementation)."""
        # In a real implementation, this would publish to a message queue like RabbitMQ, Redis, etc.
        # For now, we'll just mark as delivered
        delivery.status = "DELIVERED"
        delivery.delivered_at = datetime.utcnow()
        delivery.response_data = {"queue": subscription.queue_name}
        await self.db.commit()

    async def retry_failed_deliveries(
        self,
        max_retry_count: int = 3
    ) -> Dict[str, int]:
        """Retry failed event deliveries."""
        # Get failed deliveries with retry count < max
        query = select(MdEventDelivery).where(
            and_(
                MdEventDelivery.status == "FAILED",
                MdEventDelivery.delivery_attempts < max_retry_count
            )
        ).limit(100)
        
        result = await self.db.execute(query)
        deliveries = result.scalars().all()
        
        retried_count = 0
        success_count = 0
        
        for delivery in deliveries:
            delivery.delivery_attempts += 1
            delivery.last_attempt_at = datetime.utcnow()
            
            try:
                # Get event and subscription
                event = await self.get_event(delivery.event_id)
                subscription_query = select(MdEventSubscription).where(
                    MdEventSubscription.subscription_id == delivery.subscription_id
                )
                sub_result = await self.db.execute(subscription_query)
                subscription = sub_result.scalar_one_or_none()
                
                if event and subscription:
                    if subscription.subscriber_type == "webhook":
                        await self._deliver_to_webhook(event, subscription, delivery)
                    elif subscription.subscriber_type == "service":
                        await self._deliver_to_service(event, subscription, delivery)
                    elif subscription.subscriber_type == "queue":
                        await self._deliver_to_queue(event, subscription, delivery)
                    
                    success_count += 1
            except Exception as e:
                delivery.error_message = str(e)
            
            retried_count += 1
            await self.db.commit()
        
        return {"retried": retried_count, "success": success_count}

    async def move_to_dead_letter(
        self,
        event_id: uuid.UUID
    ) -> Optional[MdEventDeadLetter]:
        """Move a failed event to dead letter queue."""
        event = await self.get_event(event_id)
        if not event:
            return None
        
        dead_letter = MdEventDeadLetter(
            original_event_id=event.event_id,
            event_type=event.event_type,
            event_payload=event.payload,
            failure_reason=event.error_message or "Max retries exceeded",
            failure_count=event.retry_count,
            original_created_at=event.created_at
        )
        self.db.add(dead_letter)
        await self.db.commit()
        await self.db.refresh(dead_letter)
        
        return dead_letter

    async def process_pending_events(
        self,
        batch_size: int = 100
    ) -> Dict[str, int]:
        """Process pending events in batch."""
        # Get pending events
        query = select(MdEvent).where(
            and_(
                MdEvent.status == EventStatus.PENDING,
                or_(
                    MdEvent.expires_at.is_(None),
                    MdEvent.expires_at > datetime.utcnow()
                )
            )
        ).limit(batch_size)
        
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        processed_count = 0
        
        for event in events:
            await self._deliver_event(event)
            processed_count += 1
        
        return {"processed": processed_count}
