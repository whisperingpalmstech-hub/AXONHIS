from pydantic import BaseModel, UUID4, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ─── Instrument Set ─────────────────────────────────────────
class InstrumentSetCreate(BaseModel):
    name: str = Field(..., max_length=150)
    set_code: str = Field(..., max_length=50)
    description: Optional[str] = None
    department: Optional[str] = None
    instrument_count: int = 0
    is_active: bool = True

class InstrumentSetOut(InstrumentSetCreate):
    id: UUID4
    condition: str
    org_id: Optional[UUID4]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Sterilization Cycle ────────────────────────────────────
class SterilizationCycleCreate(BaseModel):
    cycle_number: str = Field(..., max_length=50)
    machine_id: str = Field(..., max_length=50)
    method: str = "steam_autoclave"
    temperature_celsius: Optional[Decimal] = None
    pressure_psi: Optional[Decimal] = None
    exposure_minutes: Optional[int] = None
    notes: Optional[str] = None
    set_ids: List[UUID4] = []   # Instrument sets loaded into this cycle

class SterilizationCycleStatusUpdate(BaseModel):
    status: str
    bi_result: Optional[str] = None
    ci_result: Optional[str] = None
    end_time: Optional[datetime] = None

class SterilizationCycleOut(BaseModel):
    id: UUID4
    cycle_number: str
    machine_id: str
    method: str
    status: str
    operator_id: Optional[UUID4]
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    temperature_celsius: Optional[Decimal]
    pressure_psi: Optional[Decimal]
    exposure_minutes: Optional[int]
    bi_result: Optional[str]
    ci_result: Optional[str]
    notes: Optional[str]
    org_id: Optional[UUID4]
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Dispatch ───────────────────────────────────────────────
class CSSDDispatchCreate(BaseModel):
    set_id: UUID4
    cycle_id: Optional[UUID4] = None
    destination_department: str

class CSSDDispatchReturn(BaseModel):
    return_condition: str = "serviceable"
    notes: Optional[str] = None

class CSSDDispatchOut(BaseModel):
    id: UUID4
    set_id: UUID4
    cycle_id: Optional[UUID4]
    destination_department: str
    dispatched_by: Optional[UUID4]
    dispatched_at: datetime
    returned_at: Optional[datetime]
    return_condition: Optional[str]
    notes: Optional[str]
    org_id: Optional[UUID4]

    class Config:
        from_attributes = True
