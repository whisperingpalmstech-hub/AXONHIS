from fastapi import APIRouter
from app.dependencies import DBSession

router = APIRouter(prefix="/billing", tags=["Patient Portal - Billing"])

@router.get("/invoices")
async def get_invoices(db: DBSession, patient_id: str):
    return []
