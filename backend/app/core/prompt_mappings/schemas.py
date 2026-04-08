from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class PromptMappingCreate(BaseModel):
    specialty_profile_id: UUID
    prompt_category: str
    ui_element: str
    ui_location: str
    prompt_template: str
    prompt_variables: List[str] = Field(default_factory=list)
    trigger_condition: dict = Field(default_factory=dict)
    output_mapping: dict = Field(default_factory=dict)
    priority: int = 0
    created_by: str


class PromptMappingUpdate(BaseModel):
    prompt_template: Optional[str] = None
    prompt_variables: Optional[List[str]] = None
    trigger_condition: Optional[dict] = None
    output_mapping: Optional[dict] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class PromptMappingResponse(BaseModel):
    mapping_id: UUID
    specialty_profile_id: UUID
    prompt_category: str
    ui_element: str
    ui_location: str
    prompt_template: str
    prompt_variables: List[str]
    trigger_condition: dict
    output_mapping: dict
    is_active: bool
    priority: int
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptVariableCreate(BaseModel):
    variable_name: str
    variable_type: str
    description: Optional[str] = None
    default_value: Optional[str] = None
    is_required: bool = False
    validation_regex: Optional[str] = None


class PromptVariableResponse(BaseModel):
    variable_id: UUID
    variable_name: str
    variable_type: str
    description: Optional[str]
    default_value: Optional[str]
    is_required: bool
    validation_regex: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PromptExecutionCreate(BaseModel):
    mapping_id: UUID
    encounter_id: Optional[UUID] = None
    patient_id: Optional[UUID] = None
    user_id: UUID
    input_data: dict = Field(default_factory=dict)


class PromptExecutionResponse(BaseModel):
    execution_id: UUID
    mapping_id: UUID
    encounter_id: Optional[UUID]
    patient_id: Optional[UUID]
    user_id: UUID
    input_data: dict
    prompt_text: str
    ai_response: dict
    execution_time_ms: Optional[int]
    status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
