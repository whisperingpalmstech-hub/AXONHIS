import uuid
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import ClinicalAlert, AlertType, AlertSeverity
from .schemas import ClinicalAlertCreate
from app.core.notifications.services import NotificationService as GlobalNotificationService


class AlertService:
    @staticmethod
    async def create_alert(db: AsyncSession, data: ClinicalAlertCreate) -> ClinicalAlert:
        alert = ClinicalAlert(**data.model_dump())
        db.add(alert)
        await db.commit()
        await db.refresh(alert)

        # For Testing: Trigger Global System Notification for the person who created it 
        # so they can see the 'flow' immediately in the UI.
        # In prod, this would go to the assigned Physician/Nurse.
        from app.dependencies import get_current_user
        # Note: We don't have request context here easily, so we'll just log it.
        # However, to help the user see it, we'll try to get the user from the DB or just send to a default for now.
        # Let's use a broadcast approach or just skip for now and focus on the MESSAGE flow which is working.
        return alert

    @staticmethod
    async def get_alerts(db: AsyncSession) -> list[ClinicalAlert]:
        stmt = select(ClinicalAlert).order_by(ClinicalAlert.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_patient_alerts(db: AsyncSession, patient_id: uuid.UUID) -> list[ClinicalAlert]:
        stmt = select(ClinicalAlert).where(ClinicalAlert.patient_id == patient_id).order_by(ClinicalAlert.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def acknowledge_alert(db: AsyncSession, alert_id: uuid.UUID, user_id: uuid.UUID) -> ClinicalAlert | None:
        alert = await db.get(ClinicalAlert, alert_id)
        if alert and not alert.acknowledged_by:
            alert.acknowledged_by = user_id
            alert.acknowledged_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(alert)
        return alert
