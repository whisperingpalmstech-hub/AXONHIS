import uuid
from typing import List, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import (
    NarcoticsOrderCreate, NarcoticsOrderOut, NarcoticsValidation,
    NarcoticsDispensation, NarcoticsDelivery, AmpouleReturnCreate,
    AmpouleVerification, AmpouleReturnOut, NarcoticsInventoryOut
)
from .services import NarcoticsService

router = APIRouter()

@router.post("/orders", response_model=NarcoticsOrderOut, status_code=201)
async def create_order(
    data: NarcoticsOrderCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Nursing initiates a narcotics order"""
    svc = NarcoticsService(db)
    return await svc.create_order(data)

@router.get("/orders", response_model=List[NarcoticsOrderOut])
async def list_orders(
    status: str = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Pharmacy lists all real-time narcotics requests filtered by status."""
    svc = NarcoticsService(db)
    return await svc.get_orders(status)

@router.get("/orders/{order_id}", response_model=NarcoticsOrderOut)
async def get_order(
    order_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get single narcotics order context."""
    svc = NarcoticsService(db)
    return await svc.get_order(order_id)

@router.post("/orders/{order_id}/validate", response_model=NarcoticsOrderOut)
async def validate_order(
    order_id: uuid.UUID,
    data: NarcoticsValidation,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """In-Charge Pharmacist explicitly approves or rejects the narcotics order."""
    import uuid as sys_uuid
    svc = NarcoticsService(db)
    pharmacist_id = sys_uuid.uuid4() # Mock auth user context
    return await svc.validate_order(order_id, data, pharmacist_id)

@router.post("/orders/{order_id}/dispense", response_model=NarcoticsOrderOut)
async def dispense_order(
    order_id: uuid.UUID,
    data: NarcoticsDispensation,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Pharmacist allocates batch and deducts strict stock."""
    import uuid as sys_uuid
    svc = NarcoticsService(db)
    pharmacist_id = sys_uuid.uuid4()
    return await svc.dispense_order(order_id, data, pharmacist_id)

@router.post("/orders/{order_id}/deliver", response_model=NarcoticsOrderOut)
async def deliver_order(
    order_id: uuid.UUID,
    data: NarcoticsDelivery,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Pharmacy records hand-over signature/keys to duty nurse."""
    import uuid as sys_uuid
    svc = NarcoticsService(db)
    pharmacist_id = sys_uuid.uuid4()
    return await svc.deliver_order(order_id, data, pharmacist_id)

@router.post("/orders/{order_id}/returns", response_model=NarcoticsOrderOut)
async def return_ampoule(
    order_id: uuid.UUID,
    data: AmpouleReturnCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Nursing logs exactly how many empty ampoules they are bringing back."""
    svc = NarcoticsService(db)
    return await svc.return_ampoule(order_id, data)

@router.post("/returns/{return_id}/verify", response_model=AmpouleReturnOut)
async def verify_ampoule_return(
    return_id: uuid.UUID,
    data: AmpouleVerification,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Pharmacist counts and validates the physically returned empty ampoules."""
    import uuid as sys_uuid
    svc = NarcoticsService(db)
    user_id = sys_uuid.uuid4()
    data.verified_by_pharmacist = user_id
    return await svc.verify_ampoule(return_id, data, user_id)

@router.get("/inventory/stock", response_model=List[NarcoticsInventoryOut])
async def check_inventory(db: AsyncSession = Depends(get_db)) -> Any:
    """View strictly controlled narcotics stock balance."""
    svc = NarcoticsService(db)
    return await svc.get_inventory()

@router.post("/seed-mock")
async def seed_mock(db: AsyncSession = Depends(get_db)) -> Any:
    """Seed test data for Narcotics Worklist simulation"""
    from decimal import Decimal
    svc = NarcoticsService(db)
    o1 = NarcoticsOrderCreate(
        patient_name="Sunil Gavaskar",
        uhid="UHID1001",
        admission_number="IP-25-1000",
        ward="Oncology Ward",
        bed_number="Bed 5A",
        prescribing_doctor="Dr. B. K. Patel",
        medication_name="Morphine Sulfate Injection 10mg/ml",
        dosage="10mg",
        requested_quantity=Decimal("3")
    )
    o2 = NarcoticsOrderCreate(
        patient_name="Priya Sharma",
        uhid="UHID1002",
        admission_number="IP-25-1005",
        ward="ICU",
        bed_number="Bed 02",
        prescribing_doctor="Dr. K. Anant",
        medication_name="Fentanyl Citrate 50mcg",
        dosage="50mcg",
        requested_quantity=Decimal("5")
    )
    o1_res = await svc.create_order(o1)
    o2_res = await svc.create_order(o2)
    
    return {"status": "success", "message": "Seeded mock narcotics orders successfully."}
