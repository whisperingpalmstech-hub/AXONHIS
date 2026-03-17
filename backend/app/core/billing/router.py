from fastapi import APIRouter
from app.core.billing.services.routes import router as services_router
from app.core.billing.tariffs.routes import router as tariffs_router
from app.core.billing.billing_entries.routes import router as billing_entries_router
from app.core.billing.invoices.routes import router as invoices_router
from app.core.billing.payments.routes import router as payments_router
from app.core.billing.insurance.routes import router as insurance_router
from app.core.billing.discounts.routes import router as discounts_router

router = APIRouter(prefix="/billing", tags=["billing"])
router.include_router(services_router)
router.include_router(tariffs_router)
router.include_router(billing_entries_router)
router.include_router(invoices_router)
router.include_router(payments_router)
router.include_router(insurance_router)
router.include_router(discounts_router)
