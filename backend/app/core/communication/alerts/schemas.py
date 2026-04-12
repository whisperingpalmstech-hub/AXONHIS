import uuid
from datetime import datetime
from pydantic import BaseModel
from .models import AlertType, AlertSeverity


class ClinicalAlertBase(BaseModel):
    patient_id: uuid.UUID
    alert_type: AlertType
    severity: AlertSeverity
    message: str


class ClinicalAlertCreate(ClinicalAlertBase):
    pass


class ClinicalAlertOut(ClinicalAlertBase):
    id: uuid.UUID
    created_at: datetime
    acknowledged_by: uuid.UUID | None = None
    acknowledged_at: datetime | None = None

    model_config = {"from_attributes": True}
