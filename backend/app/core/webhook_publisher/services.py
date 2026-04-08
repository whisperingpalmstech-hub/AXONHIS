from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
import hmac
import hashlib
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, desc

from app.core.webhook_publisher.models import (
    MdWebhookSubscription,
    MdWebhookDelivery,
    MdWebhookLog,
    WebhookStatus
)
from app.core.webhook_publisher.schemas import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
    WebhookEventPayload
)


class WebhookPublisherService:
    """Service for managing webhook subscriptions and publishing events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_subscription(
        self,
        subscription_data: WebhookSubscriptionCreate
    ) -> MdWebhookSubscription:
        """Create a new webhook subscription."""
        subscription = MdWebhookSubscription(
            subscription_name=subscription_data.subscription_name,
            subscriber_name=subscription_data.subscriber_name,
            webhook_url=subscription_data.webhook_url,
            secret_key=subscription_data.secret_key,
            event_types=subscription_data.event_types,
            headers=subscription_data.headers,
            retry_policy=subscription_data.retry_policy,
            timeout_seconds=subscription_data.timeout_seconds,
            verify_ssl=subscription_data.verify_ssl,
            filter_rules=subscription_data.filter_rules,
            rate_limit_per_minute=subscription_data.rate_limit_per_minute,
            created_by=subscription_data.created_by
        )
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        await self._log_webhook_activity(
            subscription_id=subscription.subscription_id,
            log_level="INFO",
            message=f"Webhook subscription created: {subscription.subscription_name}"
        )
        
        return subscription

    async def update_subscription(
        self,
        subscription_id: uuid.UUID,
        update_data: WebhookSubscriptionUpdate
    ) -> Optional[MdWebhookSubscription]:
        """Update an existing webhook subscription."""
        query = select(MdWebhookSubscription).where(
            MdWebhookSubscription.subscription_id == subscription_id
        )
        result = await self.db.execute(query)
        subscription = result.scalar_one_or_none()
        
        if not subscription:
            return None
        
        if update_data.subscription_name is not None:
            subscription.subscription_name = update_data.subscription_name
        if update_data.webhook_url is not None:
            subscription.webhook_url = update_data.webhook_url
        if update_data.secret_key is not None:
            subscription.secret_key = update_data.secret_key
        if update_data.event_types is not None:
            subscription.event_types = update_data.event_types
        if update_data.headers is not None:
            subscription.headers = update_data.headers
        if update_data.retry_policy is not None:
            subscription.retry_policy = update_data.retry_policy
        if update_data.timeout_seconds is not None:
            subscription.timeout_seconds = update_data.timeout_seconds
        if update_data.verify_ssl is not None:
            subscription.verify_ssl = update_data.verify_ssl
        if update_data.filter_rules is not None:
            subscription.filter_rules = update_data.filter_rules
        if update_data.rate_limit_per_minute is not None:
            subscription.rate_limit_per_minute = update_data.rate_limit_per_minute
        if update_data.status is not None:
            subscription.status = update_data.status
        
        subscription.updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(subscription)
        
        await self._log_webhook_activity(
            subscription_id=subscription.subscription_id,
            log_level="INFO",
            message=f"Webhook subscription updated: {subscription.subscription_name}"
        )
        
        return subscription

    async def get_subscription(
        self,
        subscription_id: uuid.UUID
    ) -> Optional[MdWebhookSubscription]:
        """Get a specific webhook subscription."""
        query = select(MdWebhookSubscription).where(
            MdWebhookSubscription.subscription_id == subscription_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_subscriptions(
        self,
        event_type: Optional[str] = None,
        status: Optional[WebhookStatus] = None
    ) -> List[MdWebhookSubscription]:
        """List webhook subscriptions with filters."""
        conditions = [MdWebhookSubscription.status == WebhookStatus.ACTIVE]
        
        if event_type:
            conditions.append(MdWebhookSubscription.event_types.contains([event_type]))
        
        if status:
            conditions.append(MdWebhookSubscription.status == status)
        
        query = select(MdWebhookSubscription).where(and_(*conditions))
        result = await self.db.execute(query)
        return result.scalars().all()

    async def publish_event(
        self,
        event_type: str,
        payload: WebhookEventPayload
    ) -> Dict[str, Any]:
        """Publish an event to all matching webhook subscriptions."""
        subscriptions = await self.list_subscriptions(event_type=event_type)
        
        results = {
            "event_type": event_type,
            "subscriptions_notified": 0,
            "deliveries_succeeded": 0,
            "deliveries_failed": 0
        }
        
        for subscription in subscriptions:
            try:
                # Check rate limit
                if await self._check_rate_limit(subscription):
                    await self._deliver_webhook(subscription, event_type, payload)
                    subscription.last_triggered_at = datetime.utcnow()
                    results["subscriptions_notified"] += 1
                    results["deliveries_succeeded"] += 1
                else:
                    await self._log_webhook_activity(
                        subscription_id=subscription.subscription_id,
                        log_level="WARNING",
                        message="Rate limit exceeded"
                    )
                    results["deliveries_failed"] += 1
            except Exception as e:
                await self._log_webhook_activity(
                    subscription_id=subscription.subscription_id,
                    log_level="ERROR",
                    message=f"Webhook delivery failed: {str(e)}"
                )
                results["deliveries_failed"] += 1
        
        await self.db.commit()
        return results

    async def _deliver_webhook(
        self,
        subscription: MdWebhookSubscription,
        event_type: str,
        payload: WebhookEventPayload
    ):
        """Deliver webhook to subscription endpoint."""
        # Create delivery record
        delivery = MdWebhookDelivery(
            subscription_id=subscription.subscription_id,
            event_type=event_type,
            event_id=payload.event_id,
            payload=payload.dict(),
            status="PENDING",
            max_attempts=subscription.retry_policy.get("max_attempts", 3)
        )
        self.db.add(delivery)
        await self.db.commit()
        await self.db.refresh(delivery)
        
        # Prepare request
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event_type,
            "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
            "X-Webhook-ID": str(delivery.delivery_id)
        }
        
        # Add custom headers
        headers.update(subscription.headers)
        
        # Add signature if secret key is configured
        if subscription.secret_key:
            signature = self._generate_signature(
                subscription.secret_key,
                payload.json()
            )
            headers["X-Webhook-Signature"] = signature
        
        # Send webhook
        try:
            async with httpx.AsyncClient(verify=subscription.verify_ssl) as client:
                response = await client.post(
                    subscription.webhook_url,
                    json=payload.dict(),
                    headers=headers,
                    timeout=subscription.timeout_seconds
                )
                response.raise_for_status()
            
            delivery.status = "SUCCESS"
            delivery.http_status_code = response.status_code
            delivery.response_body = response.text[:1000]  # Truncate response
            delivery.delivered_at = datetime.utcnow()
            
        except Exception as e:
            delivery.status = "FAILED"
            delivery.error_message = str(e)
            delivery.attempt_count += 1
            
            # Schedule retry if max attempts not reached
            if delivery.attempt_count < delivery.max_attempts:
                delivery.status = "RETRYING"
                retry_delay = subscription.retry_policy.get("retry_delay_seconds", 60)
                delivery.next_retry_at = datetime.utcnow() + timedelta(seconds=retry_delay)
        
        await self.db.commit()

    def _generate_signature(self, secret_key: str, payload: str) -> str:
        """Generate HMAC signature for webhook verification."""
        signature = hmac.new(
            secret_key.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    async def _check_rate_limit(
        self,
        subscription: MdWebhookSubscription
    ) -> bool:
        """Check if subscription is within rate limit."""
        one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
        
        query = select(func.count(MdWebhookDelivery.delivery_id)).where(
            and_(
                MdWebhookDelivery.subscription_id == subscription.subscription_id,
                MdWebhookDelivery.created_at >= one_minute_ago
            )
        )
        result = await self.db.execute(query)
        count = result.scalar() or 0
        
        return count < subscription.rate_limit_per_minute

    async def retry_failed_deliveries(self) -> Dict[str, int]:
        """Retry failed webhook deliveries that are due for retry."""
        now = datetime.utcnow()
        
        query = select(MdWebhookDelivery).where(
            and_(
                MdWebhookDelivery.status == "RETRYING",
                MdWebhookDelivery.next_retry_at <= now,
                MdWebhookDelivery.attempt_count < MdWebhookDelivery.max_attempts
            )
        ).limit(100)
        
        result = await self.db.execute(query)
        deliveries = result.scalars().all()
        
        retried = 0
        succeeded = 0
        
        for delivery in deliveries:
            subscription = await self.get_subscription(delivery.subscription_id)
            if subscription:
                try:
                    payload = WebhookEventPayload(**delivery.payload)
                    await self._deliver_webhook(subscription, delivery.event_type, payload)
                    retried += 1
                    if delivery.status == "SUCCESS":
                        succeeded += 1
                except Exception as e:
                    await self._log_webhook_activity(
                        subscription_id=subscription.subscription_id,
                        log_level="ERROR",
                        message=f"Webhook retry failed: {str(e)}"
                    )
        
        return {"retried": retried, "succeeded": succeeded}

    async def get_delivery_history(
        self,
        subscription_id: uuid.UUID,
        limit: int = 100
    ) -> List[MdWebhookDelivery]:
        """Get delivery history for a subscription."""
        query = select(MdWebhookDelivery).where(
            MdWebhookDelivery.subscription_id == subscription_id
        ).order_by(desc(MdWebhookDelivery.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def _log_webhook_activity(
        self,
        subscription_id: uuid.UUID,
        log_level: str,
        message: str,
        details: Dict[str, Any] = None
    ):
        """Log webhook activity."""
        log = MdWebhookLog(
            subscription_id=subscription_id,
            log_level=log_level,
            message=message,
            details=details or {}
        )
        self.db.add(log)
        await self.db.commit()
