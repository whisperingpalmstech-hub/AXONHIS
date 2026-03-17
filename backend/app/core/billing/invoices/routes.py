import uuid
from fastapi import APIRouter, HTTPException
from app.dependencies import DBSession, CurrentUser
from sqlalchemy import select
from .schemas import InvoiceCreate, InvoiceOut
from .models import Invoice
from .services import InvoiceService

router = APIRouter(tags=["invoices"])

@router.post("/invoice", response_model=InvoiceOut)
async def generate_invoice(data: InvoiceCreate, db: DBSession, user: CurrentUser):
    svc = InvoiceService(db)
    return await svc.generate_invoice(data.patient_id, data.encounter_id, user.id)

@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(invoice_id: uuid.UUID, db: DBSession, _: CurrentUser):
    inv = await db.get(Invoice, invoice_id)
    if not inv:
        raise HTTPException(status_code=404)
    return inv

@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(db: DBSession, _: CurrentUser):
    res = await db.execute(select(Invoice))
    return res.scalars().all()
