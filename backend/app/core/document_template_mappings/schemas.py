from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID


class DocumentTemplateMappingCreate(BaseModel):
    template_name: str
    template_code: str
    document_type: str
    specialty_profile_id: Optional[UUID] = None
    template_content: str
    template_variables: List[str] = Field(default_factory=list)
    output_format: str
    metadata: dict = Field(default_factory=dict)
    is_default: bool = False
    created_by: str


class DocumentTemplateMappingUpdate(BaseModel):
    template_name: Optional[str] = None
    template_content: Optional[str] = None
    template_variables: Optional[List[str]] = None
    output_format: Optional[str] = None
    metadata: Optional[dict] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class DocumentTemplateMappingResponse(BaseModel):
    mapping_id: UUID
    template_name: str
    template_code: str
    document_type: str
    specialty_profile_id: Optional[UUID]
    template_content: str
    template_variables: List[str]
    output_format: str
    metadata: dict
    is_default: bool
    is_active: bool
    version: int
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
