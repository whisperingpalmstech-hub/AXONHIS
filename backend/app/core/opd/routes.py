"""
AXONHIS Complete OPD Module — API Routes
=========================================
Unified OPD API providing 50+ endpoints covering the entire outpatient journey.
"""
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import CurrentUser

from .schemas import (
    # Pre-Registration
    PreRegistrationCreate, PreRegistrationOut, ConvertPreRegRequest,
    # Deposits
    DepositCreate, DepositOut, DepositRefundRequest, DepositConsumeRequest,
    # Consents
    ConsentTemplateCreate, ConsentTemplateOut,
    ConsentDocumentCreate, ConsentDocumentOut, ConsentDocumentSign,
    ConsentEmailRequest, ConsentUploadRequest,
    # Pro-Forma
    ProFormaBillCreate, ProFormaBillOut,
    # Kiosk
    KioskCheckinRequest, KioskCheckinOut,
    # Waitlist
    WaitlistCreate, WaitlistOut,
    # AI Scheduling
    AISchedulingPredictionOut,
    # Bill Cancellation
    BillCancelRequest,
    # Analytics
    OPDAnalyticsOut,
    # Journey
    PatientJourneyOut,
)
from .services import (
    PreRegistrationService, DepositService, ConsentService,
    ProFormaBillingService, KioskCheckinService, WaitlistService,
    AISchedulingService, BillCancellationService,
    OPDAnalyticsService, PatientJourneyService,
)

router = APIRouter(prefix="/opd", tags=["OPD Complete Module"])


# ═══════════════════════════════════════════════════════════════════════════════
# PRE-REGISTRATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/pre-registration", response_model=PreRegistrationOut)
async def create_pre_registration(
    data: PreRegistrationCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    """Create a pre-registration record for a new patient. Duplicate detection runs automatically."""
    svc = PreRegistrationService(db)
    return await svc.create_pre_registration(data, user.id, org_id=user.org_id)

@router.get("/pre-registration", response_model=list[PreRegistrationOut])
async def list_pre_registrations(
    user: CurrentUser,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List all pre-registrations with optional status filter."""
    svc = PreRegistrationService(db)
    return await svc.list_pre_registrations(status=status, org_id=user.org_id)

@router.get("/pre-registration/{prereg_id}", response_model=PreRegistrationOut)
async def get_pre_registration(
    prereg_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    svc = PreRegistrationService(db)
    p = await svc.get_pre_registration(prereg_id, org_id=user.org_id)
    if not p:
        raise HTTPException(404, "Pre-registration not found")
    return p

@router.post("/pre-registration/{prereg_id}/convert", response_model=PreRegistrationOut)
async def convert_to_patient(
    prereg_id: uuid.UUID,
    data: ConvertPreRegRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Convert pre-registration to a full patient record with UHID."""
    svc = PreRegistrationService(db)
    try:
        return await svc.convert_to_patient(prereg_id, data, user.id, org_id=user.org_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# DEPOSITS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/deposits", response_model=DepositOut)
async def create_deposit(
    data: DepositCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    """Create a new advance deposit for a patient."""
    svc = DepositService(db)
    return await svc.create_deposit(data, user.id, org_id=user.org_id)

@router.get("/deposits", response_model=list[DepositOut])
async def list_deposits(
    user: CurrentUser,
    patient_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = DepositService(db)
    return await svc.list_deposits(patient_id=patient_id, status=status, org_id=user.org_id)

@router.post("/deposits/{deposit_id}/consume", response_model=DepositOut)
async def consume_deposit(
    deposit_id: uuid.UUID,
    data: DepositConsumeRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Consume a portion of the deposit against a bill."""
    svc = DepositService(db)
    try:
        return await svc.consume_deposit(deposit_id, data, user.id, org_id=user.org_id)
    except ValueError as e:
        raise HTTPException(400, str(e))

@router.post("/deposits/{deposit_id}/refund", response_model=DepositOut)
async def refund_deposit(
    deposit_id: uuid.UUID,
    data: DepositRefundRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Refund remaining deposit balance to the patient."""
    svc = DepositService(db)
    try:
        return await svc.refund_deposit(deposit_id, data, user.id, org_id=user.org_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# CONSENT MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/consent-templates", response_model=ConsentTemplateOut)
async def create_consent_template(
    data: ConsentTemplateCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    svc = ConsentService(db)
    return await svc.create_template(data, user.id, org_id=user.org_id)

@router.get("/consent-templates", response_model=list[ConsentTemplateOut])
async def list_consent_templates(
    user: CurrentUser,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = ConsentService(db)
    return await svc.list_templates(category=category, org_id=user.org_id)

@router.post("/consent-documents", response_model=ConsentDocumentOut)
async def create_consent_document(
    data: ConsentDocumentCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    svc = ConsentService(db)
    return await svc.create_document(data, user.id, org_id=user.org_id)

@router.get("/consent-documents", response_model=list[ConsentDocumentOut])
async def list_consent_documents(
    user: CurrentUser,
    patient_id: Optional[uuid.UUID] = None,
    visit_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = ConsentService(db)
    return await svc.list_documents(patient_id=patient_id, visit_id=visit_id, org_id=user.org_id)

@router.post("/consent-documents/{doc_id}/sign", response_model=ConsentDocumentOut)
async def sign_consent_document(
    doc_id: uuid.UUID,
    data: ConsentDocumentSign,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Capture digital signature on a consent document."""
    svc = ConsentService(db)
    try:
        return await svc.sign_document(doc_id, data, org_id=user.org_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.post("/consent-documents/{doc_id}/email", response_model=ConsentDocumentOut)
async def email_consent_document(
    doc_id: uuid.UUID,
    data: ConsentEmailRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    svc = ConsentService(db)
    try:
        return await svc.email_document(doc_id, data, org_id=user.org_id)
    except ValueError as e:
        raise HTTPException(404, str(e))

@router.post("/consent-documents/{doc_id}/upload-scan", response_model=ConsentDocumentOut)
async def upload_scanned_consent(
    doc_id: uuid.UUID,
    data: ConsentUploadRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    svc = ConsentService(db)
    try:
        return await svc.upload_scanned(doc_id, data, org_id=user.org_id)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# PRO-FORMA BILLING
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/proforma-bills", response_model=ProFormaBillOut)
async def create_proforma_bill(
    data: ProFormaBillCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    """Generate a cost estimate (pro-forma bill) without affecting financials."""
    svc = ProFormaBillingService(db)
    return await svc.create_proforma(data, user.id, org_id=user.org_id)

@router.get("/proforma-bills", response_model=list[ProFormaBillOut])
async def list_proforma_bills(
    user: CurrentUser,
    patient_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = ProFormaBillingService(db)
    return await svc.list_proformas(patient_id=patient_id, org_id=user.org_id)


# ═══════════════════════════════════════════════════════════════════════════════
# KIOSK SELF CHECK-IN
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/kiosk-checkin", response_model=KioskCheckinOut)
async def kiosk_self_checkin(
    data: KioskCheckinRequest, db: AsyncSession = Depends(get_db)
):
    """Process self-check-in from a hospital kiosk. No auth required for patient kiosk."""
    svc = KioskCheckinService(db)
    return await svc.process_checkin(data)


# ═══════════════════════════════════════════════════════════════════════════════
# WAITLIST
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/waitlist", response_model=WaitlistOut)
async def add_to_waitlist(
    data: WaitlistCreate, user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    """Add a patient to the appointment waitlist for a specific doctor/date."""
    svc = WaitlistService(db)
    return await svc.add_to_waitlist(data, org_id=user.org_id)

@router.get("/waitlist", response_model=list[WaitlistOut])
async def list_waitlist(
    user: CurrentUser,
    doctor_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    svc = WaitlistService(db)
    return await svc.list_waitlist(doctor_id=doctor_id, status=status, org_id=user.org_id)

@router.post("/waitlist/process-cancellation")
async def process_cancellation_waitlist(
    user: CurrentUser,
    doctor_id: uuid.UUID = Query(...),
    slot_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """When a slot is cancelled, auto-offer to next waitlisted patient."""
    svc = WaitlistService(db)
    entry = await svc.process_cancellation_waitlist(doctor_id, slot_date, org_id=user.org_id)
    if entry:
        return {"status": "offered", "waitlist_id": str(entry.id), "patient_id": str(entry.patient_id)}
    return {"status": "no_waitlist", "message": "No patients waiting for this slot"}


# ═══════════════════════════════════════════════════════════════════════════════
# AI SCHEDULING
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai-scheduling/predict", response_model=AISchedulingPredictionOut)
async def predict_no_show(
    user: CurrentUser,
    patient_id: uuid.UUID = Query(...),
    doctor_id: uuid.UUID = Query(...),
    appointment_date: date = Query(...),
    booking_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    """AI prediction for no-show probability of an appointment."""
    svc = AISchedulingService(db)
    return await svc.predict_no_show(
        patient_id, doctor_id, appointment_date,
        booking_id=booking_id, org_id=user.org_id
    )


# ═══════════════════════════════════════════════════════════════════════════════
# BILL CANCELLATION
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/bills/{bill_id}/cancel")
async def cancel_bill(
    bill_id: uuid.UUID,
    data: BillCancelRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Cancel a bill with mandatory reason and audit trail."""
    svc = BillCancellationService(db)
    try:
        log = await svc.cancel_bill(bill_id, data, user.id, org_id=user.org_id)
        return {
            "status": "cancelled",
            "audit_id": str(log.id),
            "bill_number": log.bill_number,
            "reason": log.cancellation_reason,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# OPD ANALYTICS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/analytics/compute", response_model=OPDAnalyticsOut)
async def compute_opd_analytics(
    user: CurrentUser,
    for_date: date = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """Compute comprehensive OPD analytics for a given date."""
    target_date = for_date or date.today()
    svc = OPDAnalyticsService(db)
    return await svc.compute_daily_analytics(target_date, org_id=user.org_id)


# ═══════════════════════════════════════════════════════════════════════════════
# PATIENT JOURNEY
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/journey/{visit_id}", response_model=PatientJourneyOut)
async def get_patient_journey(
    visit_id: uuid.UUID, user: CurrentUser, db: AsyncSession = Depends(get_db)
):
    """Get the complete patient journey for a visit showing all workflow steps."""
    svc = PatientJourneyService(db)
    try:
        return await svc.get_journey(visit_id, org_id=user.org_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
