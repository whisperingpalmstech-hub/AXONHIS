"""Billing router – view entries, invoices, payments."""
import uuid

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.billing.services import BillingService
from app.dependencies import CurrentUser, DBSession

router = APIRouter(prefix="/billing", tags=["billing"])


class BillingEntryOut(BaseModel):
    id: uuid.UUID
    encounter_id: uuid.UUID
    order_id: uuid.UUID
    description: str
    amount: float
    status: str
    reversal_of: uuid.UUID | None
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/encounter/{encounter_id}", response_model=list[BillingEntryOut])
async def list_billing_entries(
    encounter_id: uuid.UUID, db: DBSession, _: CurrentUser
) -> list[BillingEntryOut]:
    entries = await BillingService(db).get_entries_for_encounter(encounter_id)
    return [BillingEntryOut.model_validate(e) for e in entries]
