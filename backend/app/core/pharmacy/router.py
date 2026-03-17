from fastapi import APIRouter
from app.core.pharmacy.medications.routes import router as medications_router
from app.core.pharmacy.prescriptions.routes import router as prescriptions_router
from app.core.pharmacy.dispensing.routes import router as dispensing_router
from app.core.pharmacy.inventory.routes import router as inventory_router
from app.core.pharmacy.batches.routes import router as batches_router
from app.core.pharmacy.drug_interactions.routes import router as interactions_router

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])

router.include_router(medications_router)
router.include_router(prescriptions_router)
router.include_router(dispensing_router)
router.include_router(inventory_router)
router.include_router(batches_router)
router.include_router(interactions_router)
