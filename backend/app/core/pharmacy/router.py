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

from app.core.pharmacy.sales_worklist.routes import router as sales_worklist_router
router.include_router(sales_worklist_router)

from app.core.pharmacy.sales_returns.routes import router as sales_returns_router
router.include_router(sales_returns_router)

from app.core.pharmacy.ip_issues.routes import router as ip_issues_router
router.include_router(ip_issues_router)

from app.core.pharmacy.ip_returns.routes import router as ip_returns_router
from app.core.pharmacy.narcotics.routes import router as narcotics_router
from app.core.pharmacy.inventory_intelligence.routes import router as inventory_intelligence_router

router.include_router(ip_issues_router, prefix="/ip-issues", tags=["IP Pharmacy"])
router.include_router(ip_returns_router, prefix="/ip-returns", tags=["IP Pharmacy"])
router.include_router(narcotics_router, prefix="/narcotics", tags=["Narcotics Store Mgmt"])
router.include_router(inventory_intelligence_router, prefix="/inventory-intelligence", tags=["Inventory Intelligence"])

from app.core.pharmacy.billing_compliance.routes import router as billing_compliance_router
router.include_router(billing_compliance_router, prefix="/billing-compliance", tags=["Pharmacy Billing & Compliance"])
