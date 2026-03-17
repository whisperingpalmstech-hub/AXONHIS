from pydantic import BaseModel, ConfigDict
import uuid

class DrugInteractionCreate(BaseModel):
    drug_a_id: uuid.UUID
    drug_b_id: uuid.UUID
    interaction_type: str
    severity: str
    description: str | None = None

class DrugInteractionOut(DrugInteractionCreate):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)
