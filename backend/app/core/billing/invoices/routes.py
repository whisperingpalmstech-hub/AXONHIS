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
async def list_invoices(db: DBSession, user: CurrentUser):
    from app.core.patients.patients.models import Patient
    stmt = select(Invoice)
    if getattr(user, 'org_id', None):
        stmt = stmt.join(Patient, Invoice.patient_id == Patient.id).where(Patient.org_id == user.org_id)
    res = await db.execute(stmt)
    return res.scalars().all()
