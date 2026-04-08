from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from enum import Enum


class ConfigScope(str, Enum):
    GLOBAL = "GLOBAL"
    FACILITY = "FACILITY"
    SPECIALTY = "SPECIALTY"
    USER = "USER"
    ENCOUNTER = "ENCOUNTER"


class ConfigDataType(str, Enum):
    STRING = "STRING"
    NUMBER = "NUMBER"
    BOOLEAN = "BOOLEAN"
    JSON = "JSON"
    ARRAY = "ARRAY"


class ConfigItemCreate(BaseModel):
    config_key: str
    config_value: Any
    data_type: ConfigDataType
    scope: ConfigScope
    scope_id: Optional[UUID] = None
    category: str
    description: Optional[str] = None
    is_sensitive: bool = False
    is_required: bool = False
    default_value: Optional[Any] = None
    validation_rules: dict = Field(default_factory=dict)
    created_by: str
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ConfigItemUpdate(BaseModel):
    config_value: Optional[Any] = None
    description: Optional[str] = None
    validation_rules: Optional[dict] = None
    updated_by: Optional[str] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None


class ConfigItemResponse(BaseModel):
    config_id: UUID
    config_key: str
    config_value: Any
    data_type: str
    scope: str
    scope_id: Optional[UUID]
    category: str
    description: Optional[str]
    is_sensitive: bool
    is_required: bool
    default_value: Optional[Any]
    validation_rules: dict
    version: int
    created_by: str
    updated_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    effective_from: Optional[datetime]
    effective_to: Optional[datetime]

    class Config:
        from_attributes = True


class ConfigHistoryResponse(BaseModel):
    history_id: UUID
    config_id: UUID
    config_key: str
    old_value: Optional[Any]
    new_value: Optional[Any]
    change_reason: Optional[str]
    changed_by: str
    changed_at: datetime
    version: int

    class Config:
        from_attributes = True


class ConfigGroupCreate(BaseModel):
    group_name: str
    group_code: str
    description: Optional[str] = None
    category: str
    parent_group_id: Optional[UUID] = None
    sort_order: int = 0


class ConfigGroupResponse(BaseModel):
    group_id: UUID
    group_name: str
    group_code: str
    description: Optional[str]
    category: str
    parent_group_id: Optional[UUID]
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConfigSearchQuery(BaseModel):
    config_key: Optional[str] = None
    scope: Optional[ConfigScope] = None
    scope_id: Optional[UUID] = None
    category: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ConfigSearchResponse(BaseModel):
    configs: List[ConfigItemResponse]
    total_count: int
    has_more: bool
