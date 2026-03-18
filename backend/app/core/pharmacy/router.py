from fastapi import APIRouter
from app.core.pharmacy.medications.routes import router as medications_router
from app.core.pharmacy.prescriptions.routes import router as prescriptions_router
from app.core.pharmacy.dispensing.routes import router as dispensing_router
from app.core.pharmacy.inventory.routes import router as inventory_router
from app.core.pharmacy.batches.routes import router as batches_router

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])

router.include_router(medications_router, tags=["Medications"])
router.include_router(inventory_router, tags=["Pharmacy Inventory"])
router.include_router(prescriptions_router, tags=["Prescriptions"])
router.include_router(dispensing_router, tags=["Pharmacy Dispensing"])
router.include_router(batches_router, tags=["Drug Batches"])
