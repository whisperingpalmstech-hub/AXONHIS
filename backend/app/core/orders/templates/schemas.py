"""Order Templates & Sets schemas."""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class OrderTemplateItemCreate(BaseModel):
    item_type: str
    item_name: str
    item_code: str | None = None
    default_quantity: float = 1.0
    default_instructions: str | None = None


class OrderTemplateCreate(BaseModel):
    template_name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    order_type: str
    is_public: bool = True
    items: list[OrderTemplateItemCreate] = Field(default_factory=list)


class OrderTemplateItemOut(BaseModel):
    id: uuid.UUID
    item_type: str
    item_name: str
    item_code: str | None
    default_quantity: float
    default_instructions: str | None
    model_config = {"from_attributes": True}


class OrderTemplateOut(BaseModel):
    id: uuid.UUID
    template_name: str
    description: str | None
    order_type: str
    is_public: bool
    created_by: uuid.UUID
    created_at: datetime
    items: list[OrderTemplateItemOut]
    model_config = {"from_attributes": True}


class OrderSetItemCreate(BaseModel):
    order_type: str
    item_name: str
    item_code: str | None = None
    default_quantity: float = 1.0
    default_instructions: str | None = None
    sort_order: int = 0


class OrderSetCreate(BaseModel):
    set_name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    clinical_context: str | None = None
    is_public: bool = True
    items: list[OrderSetItemCreate] = Field(default_factory=list)


class OrderSetItemOut(BaseModel):
    id: uuid.UUID
    order_type: str
    item_name: str
    item_code: str | None
    default_quantity: float
    default_instructions: str | None
    sort_order: int
    model_config = {"from_attributes": True}


class OrderSetOut(BaseModel):
    id: uuid.UUID
    set_name: str
    description: str | None
    clinical_context: str | None
    is_public: bool
    created_by: uuid.UUID
    created_at: datetime
    items: list[OrderSetItemOut]
    model_config = {"from_attributes": True}
