from fastapi import APIRouter
from .patient_accounts.routes import router as account_router
from .appointments.routes import router as appointment_router
from .teleconsultations.routes import router as tele_router
from .medical_records.routes import router as records_router
from .patient_payments.routes import router as payments_router

portal_router = APIRouter(prefix="/portal")

portal_router.include_router(account_router)
portal_router.include_router(appointment_router)
portal_router.include_router(tele_router)
portal_router.include_router(records_router)
portal_router.include_router(payments_router)
