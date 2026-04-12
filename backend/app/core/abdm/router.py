import uuid
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.dependencies import get_current_user
from app.core.auth.models import User
from app.core.abdm.services import AbdmService

router = APIRouter(prefix="/abdm", tags=["ABDM Compliance (India)"])

# Request Schemas
class ABHALinkRequest(BaseModel):
    patient_id: uuid.UUID
    abha_number: str
    abha_address: str

class ConsentRequest(BaseModel):
    patient_id: uuid.UUID
    hi_types: List[str]
    purpose: str

class HIERequest(BaseModel):
    transaction_id: str
    consent_id: str
    patient_id: uuid.UUID
    doctor_id: uuid.UUID | None
    request_type: str
    payload: dict

@router.post("/m2/link-abha", summary="M2: Link ABHA ID to Patient")
async def link_abha(req: ABHALinkRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Encodes and links ABHA ID and Address to the specified patient, creating a HIPAA compliant audit log."""
    svc = AbdmService(db)
    try:
        await svc.link_abha(req.patient_id, req.abha_number, req.abha_address, current_user.org_id, current_user.id)
        await db.commit()
        return {"status": "success", "message": "ABHA Linked Successfully. Sensitive data AES-encrypted."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/m2/consent", summary="M2: Request Patient Consent Artefact")
async def generate_consent(req: ConsentRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Mocks generating an ABDM standard Consent Artefact containing permission scope."""
    svc = AbdmService(db)
    artefact = await svc.generate_consent_artefact(req.patient_id, current_user.org_id, req.hi_types, req.purpose)
    await db.commit()
    return {"consent_id": artefact.consent_id, "status": artefact.status}

@router.post("/m3/fhir-exchange", summary="M3: Health Information Exchange Log")
async def log_exchange(req: HIERequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Store requests for Patient FHIR bundles conforming to HIE-CM guidelines and HIP/HIU roles."""
    svc = AbdmService(db)
    log = await svc.log_exchange(
        transaction_id=req.transaction_id,
        consent_id=req.consent_id,
        patient_id=req.patient_id,
        org_id=current_user.org_id,
        type=req.request_type,
        status="SUCCESS",
        request_payload=req.payload,
        doctor_id=req.doctor_id
    )
    await db.commit()
    return {"transaction_id": log.transaction_id, "message": "FHIR Request Logged with full compliance."}
