import uuid
from pydantic import BaseModel, Field


class SurgicalProcedureBase(BaseModel):
    procedure_code: str = Field(..., min_length=1, max_length=50)
    procedure_name: str = Field(..., min_length=1, max_length=200)
    specialty: str = Field(..., min_length=1, max_length=100)
    expected_duration: int = Field(..., gt=0) # In minutes
    billing_code: str = Field(..., min_length=1, max_length=50)


class SurgicalProcedureCreate(SurgicalProcedureBase):
    pass


class SurgicalProcedureUpdate(BaseModel):
    procedure_name: str | None = None
    specialty: str | None = None
    expected_duration: int | None = None
    billing_code: str | None = None


class SurgicalProcedureOut(SurgicalProcedureBase):
    id: uuid.UUID

    model_config = {"from_attributes": True}
