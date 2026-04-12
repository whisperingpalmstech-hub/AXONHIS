from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from .models import ReactionType, ReactionSeverity


class TransfusionReactionBase(BaseModel):
    transfusion_id: UUID
    reaction_type: ReactionType
    reaction_severity: ReactionSeverity
    symptoms: str | None = None
    reported_by: str


class TransfusionReactionCreate(TransfusionReactionBase):
    pass


class TransfusionReactionUpdate(BaseModel):
    reaction_severity: ReactionSeverity | None = None
    symptoms: str | None = None


class TransfusionReactionResponse(TransfusionReactionBase):
    id: UUID
    reported_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
