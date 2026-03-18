from pydantic import BaseModel, UUID4, ConfigDict, Field
from typing import Optional, List
from datetime import datetime

class PatientContext(BaseModel):
    patient_id: UUID4
    encounter_id: UUID4
    weight_kg: Optional[float] = None
    age_years: Optional[float] = None
    kidney_function_egfr: Optional[float] = None
    allergies: List[str] = []
    active_medications: List[str] = []
    diagnoses: List[str] = []

class MedicationCheckRequest(BaseModel):
    patient_context: PatientContext
    new_medication_id: str
    dose: Optional[float] = None

class CDSSAlertBase(BaseModel):
    encounter_id: UUID4
    patient_id: UUID4
    alert_type: str
    severity: str
    message: str
    recommended_action: Optional[str] = None
    is_overridden: Optional[bool] = False
    overridden_by: Optional[UUID4] = None

class CDSSAlertCreate(CDSSAlertBase):
    pass

class CDSSAlertResponse(CDSSAlertBase):
    id: UUID4
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class CDSSCheckResponse(BaseModel):
    status: str  # "approved", "warning", "blocked"
    alerts: List[CDSSAlertResponse] = []
