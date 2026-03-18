import uuid
from datetime import datetime
from pydantic import BaseModel


class TaskEscalationBase(BaseModel):
    task_id: uuid.UUID
    escalated_to: uuid.UUID
    reason: str


class TaskEscalationCreate(TaskEscalationBase):
    pass


class TaskEscalationOut(TaskEscalationBase):
    id: uuid.UUID
    escalated_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
