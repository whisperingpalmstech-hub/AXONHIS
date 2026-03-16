from fastapi import APIRouter

from app.core.patients.patients.router import router as patients_router
from app.core.patients.appointments.router import router as appointments_router
from app.core.patients.consents.router import router as consents_router
from app.core.patients.insurance.router import router as insurance_router
from app.core.patients.guardians.router import router as guardians_router
from app.core.patients.contacts.router import router as contacts_router
from app.core.patients.identifiers.router import router as identifiers_router

router = APIRouter()

router.include_router(patients_router)
router.include_router(appointments_router)
router.include_router(consents_router)
router.include_router(insurance_router)
router.include_router(guardians_router)
router.include_router(contacts_router)
router.include_router(identifiers_router)
