from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime
import uuid

# ════════ STATUS TYPES ════════
BedStatus = Literal["available", "occupied", "cleaning", "maintenance"]
AssignmentStatus = Literal["active", "transferred", "released"]
CleaningStatus = Literal["pending", "in_progress", "completed"]

# ════════ WARD SCHEMAS ════════
class WardBase(BaseModel):
    ward_code: str
    ward_name: str
    department: str
    floor: Optional[str] = None
    capacity: int = 0

class WardCreate(WardBase):
    pass

class WardOut(WardBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ════════ ROOM SCHEMAS ════════
class RoomBase(BaseModel):
    ward_id: uuid.UUID
    room_number: str
    room_type: str # private, semi_private, general
    capacity: int = 1

class RoomCreate(RoomBase):
    pass

class RoomOut(RoomBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

# ════════ BED SCHEMAS ════════
class BedBase(BaseModel):
    room_id: uuid.UUID
    bed_code: str
    bed_number: str
    bed_type: str # standard, icu, isolation, pediatric
    status: str = "available"

class BedCreate(BedBase):
    pass

class BedOut(BedBase):
    id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True

# ════════ ASSIGNMENT SCHEMAS ════════
class BedAssignmentBase(BaseModel):
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    bed_id: uuid.UUID
    assigned_by: Optional[uuid.UUID] = None

class BedAssignmentCreate(BedAssignmentBase):
    pass

class BedAssignmentOut(BedAssignmentBase):
    id: uuid.UUID
    assigned_at: datetime
    status: str
    released_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# ════════ TRANSFER SCHEMAS ════════
class BedTransferCreate(BaseModel):
    patient_id: uuid.UUID
    encounter_id: uuid.UUID
    from_bed_id: uuid.UUID
    to_bed_id: uuid.UUID
    transfer_reason: Optional[str] = None
    transferred_by: Optional[uuid.UUID] = None

class BedTransferOut(BedTransferCreate):
    id: uuid.UUID
    transferred_at: datetime

    class Config:
        orm_mode = True

# ════════ CLEANING SCHEMAS ════════
class BedCleaningTaskBase(BaseModel):
    bed_id: uuid.UUID
    cleaning_status: str = "pending"
    cleaned_by: Optional[uuid.UUID] = None

class BedCleaningTaskCreate(BedCleaningTaskBase):
    pass

class BedCleaningTaskOut(BedCleaningTaskBase):
    id: uuid.UUID
    cleaning_started_at: Optional[datetime] = None
    cleaning_completed_at: Optional[datetime] = None

    class Config:
        orm_mode = True
