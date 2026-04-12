from datetime import date
from pydantic import BaseModel, ConfigDict
import uuid
from typing import Any

class HospitalPredictionOut(BaseModel):
    id: uuid.UUID
    target_date: date
    prediction_type: str
    predicted_value: float
    confidence_interval_low: float | None
    confidence_interval_high: float | None
    factors: dict[str, Any]
    model_config = ConfigDict(from_attributes=True)
