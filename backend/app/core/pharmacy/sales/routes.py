import uuid
from typing import List
from fastapi import APIRouter
from app.dependencies import DBSession, CurrentUser
from app.core.pharmacy.medications.schemas import MedicationOut
from .schemas import SaleCreate, SaleOut, SalePaymentCreate, SalePaymentOut, PrescriptionUploadCreate, PrescriptionUploadOut, KitAddRequest
from .services import WalkInSalesService

router = APIRouter(tags=["pharmacy-sales"])

@router.post("/pharmacy/sales", response_model=SaleOut)
async def create_walkin_sale(data: SaleCreate, db: DBSession, current_user: CurrentUser):
    svc = WalkInSalesService(db)
    sale = await svc.create_sale(data, pharmacist_id=current_user.id)
    await db.commit()
    return sale

@router.post("/pharmacy/sales/{sale_id}/payment", response_model=SalePaymentOut)
async def process_payment(sale_id: uuid.UUID, data: SalePaymentCreate, db: DBSession, current_user: CurrentUser):
    svc = WalkInSalesService(db)
    payment = await svc.add_payment(sale_id, data, pharmacist_id=current_user.id)
    await db.commit()
    return payment

@router.get("/pharmacy/sales/{sale_id}", response_model=SaleOut)
async def get_sale(sale_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = WalkInSalesService(db)
    return await svc.get_sale(sale_id)

@router.post("/pharmacy/sales/prescription-upload", response_model=PrescriptionUploadOut)
async def upload_prescription(data: PrescriptionUploadCreate, db: DBSession, _: CurrentUser):
    svc = WalkInSalesService(db)
    rx = await svc.upload_prescription(data)
    await db.commit()
    return rx

@router.post("/pharmacy/sales/kits", response_model=List[MedicationOut])
async def populate_kit(req: KitAddRequest, db: DBSession, _: CurrentUser):
    svc = WalkInSalesService(db)
    return await svc.resolve_kit(req.kit_name)

@router.get("/pharmacy/sales", response_model=List[SaleOut])
async def list_sales(db: DBSession, _: CurrentUser, limit: int = 50):
    svc = WalkInSalesService(db)
    return await svc.get_recent_sales(limit)

@router.get("/pharmacy/sales/patient/{patient_id}", response_model=List[SaleOut])
async def get_patient_sales(patient_id: uuid.UUID, db: DBSession, _: CurrentUser):
    svc = WalkInSalesService(db)
    return await svc.get_patient_sales(patient_id)
