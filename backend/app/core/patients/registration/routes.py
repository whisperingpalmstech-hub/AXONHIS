"""
Enterprise Registration Router.

Exposes all 10 OPD FRD features as REST API endpoints:

  Feature 1 – AI-Assisted Registration:
    POST /registration/ai/start             – Start AI-guided session
    POST /registration/ai/step              – Submit step answer
    POST /registration/ai/complete          – Complete and create patient

  Feature 2 – Voice-Enabled Registration:
    POST /registration/voice/command        – Parse voice command

  Feature 3 – ID Scan (OCR):
    POST /registration/id-scan/extract      – Upload ID and extract data
    POST /registration/id-scan/{id}/verify  – Verify scan result

  Feature 4 – Face Recognition Check-in:
    POST /registration/face/enroll          – Enroll patient face
    POST /registration/face/check-in        – Identify patient by face

  Feature 5 – Duplicate Detection:
    POST /registration/duplicates/check     – AI duplicate check

  Feature 6 – Address Auto-Population:
    GET  /registration/address/lookup       – Pincode lookup

  Feature 7 – UHID Generation:
    POST /registration/uhid/generate        – Generate UHID

  Feature 8 – Health Card:
    POST /registration/health-card/generate – Generate health card with QR
    GET  /registration/health-card/{patient_id} – Fetch health card

  Feature 9 – Document Upload:
    POST /registration/documents/upload     – Upload document
    GET  /registration/documents/{patient_id} – List patient documents

  Feature 10 – Notification Engine:
    POST /registration/notifications/send   – Send registration notifications
    GET  /registration/notifications/{patient_id} – Get notification log
"""
import uuid

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile, status

from app.dependencies import CurrentUser, DBSession
from app.core.patients.registration.schemas import (
    AddressLookupResponse,
    AIDuplicateCheckRequest,
    AIDuplicateCheckResponse,
    AIRegistrationCompleteRequest,
    AIRegistrationSessionOut,
    AIRegistrationStartRequest,
    AIRegistrationStepRequest,
    DuplicateMatchOut,
    FaceCheckInResponse,
    FaceEnrollOut,
    HealthCardOut,
    IDScanResultOut,
    PatientDocumentOut,
    RegistrationNotificationOut,
    RegistrationNotifyResponse,
    UHIDGenerateResponse,
    VoiceRegistrationRequest,
    VoiceRegistrationResponse,
)
from app.core.patients.registration.services import (
    AddressAutoPopulationService,
    AIDuplicateDetectionService,
    AIRegistrationService,
    DocumentUploadService,
    FaceRecognitionService,
    HealthCardService,
    IDScanService,
    RegistrationNotificationEngine,
    UHIDService,
    VoiceRegistrationService,
)

router = APIRouter(prefix="/registration", tags=["Enterprise Patient Registration"])


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 1: AI-Assisted Registration
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/ai/start", response_model=AIRegistrationSessionOut, status_code=201)
async def ai_registration_start(
    body: AIRegistrationStartRequest,
    db: DBSession,
    user: CurrentUser,
) -> AIRegistrationSessionOut:
    """
    Start a new AI-guided registration session.
    The system will ask mandatory questions one-by-one.
    """
    svc = AIRegistrationService(db)
    result = await svc.start_session(user_id=user.id, language=body.language)
    return AIRegistrationSessionOut(**result)


@router.post("/ai/step", response_model=AIRegistrationSessionOut)
async def ai_registration_step(
    body: AIRegistrationStepRequest,
    db: DBSession,
    user: CurrentUser,
) -> AIRegistrationSessionOut:
    """
    Submit an answer for the current registration step.
    AI validates the response and advances to the next question.
    """
    svc = AIRegistrationService(db)
    try:
        result = await svc.submit_step(
            session_id=body.session_id,
            field_name=body.field_name,
            field_value=body.field_value,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return AIRegistrationSessionOut(**result)


@router.post("/ai/complete", response_model=AIRegistrationSessionOut)
async def ai_registration_complete(
    body: AIRegistrationCompleteRequest,
    db: DBSession,
    user: CurrentUser,
) -> AIRegistrationSessionOut:
    """
    Complete the AI-guided registration session and create the patient record.
    """
    svc = AIRegistrationService(db)
    try:
        result = await svc.complete_session(session_id=body.session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return AIRegistrationSessionOut(**result)


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 2: Voice-Enabled Registration
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/voice/command", response_model=VoiceRegistrationResponse, status_code=201)
async def voice_registration_command(
    body: VoiceRegistrationRequest,
    db: DBSession,
    user: CurrentUser,
) -> VoiceRegistrationResponse:
    """
    Parse voice command for registration actions.
    Supports: 'Register new patient', 'Search patient by mobile', 'Proceed to billing'.
    Multilingual: EN / HI / MR.
    """
    svc = VoiceRegistrationService(db)
    result = await svc.process_voice_command(
        transcript=body.transcript, language=body.language
    )
    return VoiceRegistrationResponse(**result)


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 3: ID Scan (OCR) Registration
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/id-scan/extract", response_model=IDScanResultOut, status_code=201)
async def id_scan_extract(
    db: DBSession,
    user: CurrentUser,
    file: UploadFile = File(..., description="Scanned ID document image"),
    document_type: str = Form(..., description="passport | national_id | aadhaar | driving_license"),
    session_id: str = Form(default="", description="Optional registration session ID"),
) -> IDScanResultOut:
    """
    Upload a scanned identity document (Passport, Aadhaar, National ID, Driving License).
    AI-OCR extracts: name, dob, gender, and ID number.
    """
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    # Save file
    import os
    upload_dir = os.path.join(os.getcwd(), "uploads", "id_scans")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{uuid.uuid4().hex}_{file.filename}")
    with open(file_path, "wb") as f:
        f.write(content)

    sid = uuid.UUID(session_id) if session_id else None

    svc = IDScanService(db)
    record = await svc.process_id_scan(
        document_type=document_type,
        file_content=content,
        file_path=file_path,
        session_id=sid,
    )
    return IDScanResultOut.model_validate(record)


@router.post("/id-scan/{scan_id}/verify", response_model=IDScanResultOut)
async def id_scan_verify(
    scan_id: uuid.UUID,
    db: DBSession,
    user: CurrentUser,
) -> IDScanResultOut:
    """Mark an ID scan extraction as verified by staff."""
    svc = IDScanService(db)
    try:
        record = await svc.verify_scan(scan_id=scan_id, user_id=user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return IDScanResultOut.model_validate(record)


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 4: Face Recognition Check-in
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/face/enroll", response_model=FaceEnrollOut, status_code=201)
async def face_enroll(
    db: DBSession,
    user: CurrentUser,
    patient_id: str = Form(..., description="Patient UUID"),
    photo: UploadFile = File(..., description="Patient face photo"),
) -> FaceEnrollOut:
    """
    Enroll a patient's face for biometric check-in.
    Photo is stored and a face embedding vector is generated.
    """
    content = await photo.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB
        raise HTTPException(status_code=413, detail="Photo too large (max 5MB)")

    # Save photo
    import os
    photo_dir = os.path.join(os.getcwd(), "uploads", "face_photos")
    os.makedirs(photo_dir, exist_ok=True)
    photo_path = os.path.join(photo_dir, f"{uuid.uuid4().hex}.jpg")
    with open(photo_path, "wb") as f:
        f.write(content)

    pid = uuid.UUID(patient_id)
    svc = FaceRecognitionService(db)
    record = await svc.enroll_face(
        patient_id=pid, photo_content=content, photo_path=photo_path
    )
    return FaceEnrollOut.model_validate(record)


@router.post("/face/check-in", response_model=FaceCheckInResponse, status_code=200)
async def face_check_in(
    db: DBSession,
    user: CurrentUser,
    photo: UploadFile = File(..., description="Face photo for identification"),
) -> FaceCheckInResponse:
    """
    Identify a patient by face photo for quick check-in.
    Returns matched patient details or a 'not found' response.
    """
    content = await photo.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Photo too large (max 5MB)")

    svc = FaceRecognitionService(db)
    result = await svc.check_in_by_face(photo_content=content)
    return FaceCheckInResponse(**result)


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 5: AI Duplicate Detection
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/duplicates/check", response_model=AIDuplicateCheckResponse)
async def check_duplicates(
    body: AIDuplicateCheckRequest,
    db: DBSession,
    user: CurrentUser,
) -> AIDuplicateCheckResponse:
    """
    AI-powered duplicate patient detection.
    Matches on: name, mobile, dob, email, and address similarity.
    """
    svc = AIDuplicateDetectionService(db)
    result = await svc.check_duplicates(
        first_name=body.first_name,
        last_name=body.last_name,
        date_of_birth=body.date_of_birth,
        mobile=body.mobile,
        email=body.email,
        address=body.address,
    )
    matches = [DuplicateMatchOut(**m) for m in result.get("matches", [])]
    return AIDuplicateCheckResponse(
        has_duplicates=result["has_duplicates"],
        matches=matches,
        ai_recommendation=result["ai_recommendation"],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 6: Address Auto-Population
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/address/lookup", response_model=AddressLookupResponse)
async def address_lookup(
    pincode: str = Query(..., min_length=4, max_length=10, description="Postal/ZIP code"),
    db: DBSession = None,
    user: CurrentUser = None,
) -> AddressLookupResponse:
    """
    Auto-populate address fields from pincode/ZIP code.
    Resolves: area, city, state, country.
    Uses local cache and falls back to postal API.
    """
    svc = AddressAutoPopulationService(db)
    result = await svc.lookup(pincode=pincode)
    return AddressLookupResponse(**result)


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 7: UHID Generation
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/uhid/generate", response_model=UHIDGenerateResponse, status_code=201)
async def generate_uhid(
    patient_id: uuid.UUID = Query(..., description="Patient ID to assign UHID to"),
    db: DBSession = None,
    user: CurrentUser = None,
) -> UHIDGenerateResponse:
    """
    Generate a globally unique hospital identifier (UHID) for a patient.
    Format: AXH-YYYYMMDD-XXXXXXXX + check digits.
    """
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.core.patients.patients.models import Patient

    # Fetch patient
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalars().first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    # If already has a UHID-style patient_uuid, return it
    if patient.patient_uuid and patient.patient_uuid.startswith("AXH-"):
        return UHIDGenerateResponse(
            patient_id=patient.id,
            uhid=patient.patient_uuid,
            generated_at=patient.updated_at or patient.created_at,
        )

    # Generate new UHID
    new_uhid = UHIDService.generate_uhid()
    patient.patient_uuid = new_uhid
    await db.flush()

    return UHIDGenerateResponse(
        patient_id=patient.id,
        uhid=new_uhid,
        generated_at=datetime.now(timezone.utc),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 8: Health Card Generation
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/health-card/generate", response_model=HealthCardOut, status_code=201)
async def generate_health_card(
    patient_id: uuid.UUID = Query(..., description="Patient to generate card for"),
    db: DBSession = None,
    user: CurrentUser = None,
) -> HealthCardOut:
    """
    Generate a digital patient health card with QR code.
    Contains: UHID, patient name, DOB, gender, hospital info.
    """
    svc = HealthCardService(db)
    try:
        card = await svc.generate_card(patient_id=patient_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return HealthCardOut.model_validate(card)


@router.get("/health-card/{patient_id}", response_model=HealthCardOut)
async def get_health_card(
    patient_id: uuid.UUID,
    db: DBSession,
    user: CurrentUser,
) -> HealthCardOut:
    """Fetch the active health card for a patient."""
    from sqlalchemy import select
    from app.core.patients.registration.models import HealthCard

    result = await db.execute(
        select(HealthCard).where(
            HealthCard.patient_id == patient_id,
            HealthCard.is_active.is_(True),
        )
    )
    card = result.scalars().first()
    if not card:
        raise HTTPException(status_code=404, detail="Health card not found. Generate one first.")
    return HealthCardOut.model_validate(card)


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 9: Document Upload
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/documents/upload", response_model=PatientDocumentOut, status_code=201)
async def upload_document(
    db: DBSession,
    user: CurrentUser,
    patient_id: str = Form(..., description="Patient UUID"),
    category: str = Form(..., description="id_proof | medical_document | patient_photo | insurance_card | other"),
    description: str = Form(default="", description="Document description"),
    file: UploadFile = File(..., description="Document file"),
) -> PatientDocumentOut:
    """
    Upload a patient document (ID proof, medical records, photos, insurance cards).
    """
    content = await file.read()
    if len(content) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=413, detail="File too large (max 20MB)")

    pid = uuid.UUID(patient_id)
    svc = DocumentUploadService(db)
    try:
        doc = await svc.upload_document(
            patient_id=pid,
            category=category,
            file_content=content,
            original_name=file.filename or "unknown",
            file_type=file.content_type or "application/octet-stream",
            description=description or None,
            uploaded_by=user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return PatientDocumentOut.model_validate(doc)


@router.get("/documents/{patient_id}", response_model=list[PatientDocumentOut])
async def list_documents(
    patient_id: uuid.UUID,
    db: DBSession,
    user: CurrentUser,
    category: str | None = Query(default=None, description="Filter by category"),
) -> list[PatientDocumentOut]:
    """List all uploaded documents for a patient."""
    svc = DocumentUploadService(db)
    docs = await svc.list_documents(patient_id=patient_id, category=category)
    return [PatientDocumentOut.model_validate(d) for d in docs]


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 10: Notification Engine
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/notifications/send", response_model=RegistrationNotifyResponse, status_code=201)
async def send_registration_notifications(
    patient_id: uuid.UUID = Query(...),
    channels: str = Query(
        default="sms,email",
        description="Comma-separated channels: sms, email, whatsapp",
    ),
    db: DBSession = None,
    user: CurrentUser = None,
) -> RegistrationNotifyResponse:
    """
    Send registration confirmation via SMS, Email, and/or WhatsApp.
    """
    channel_list = [c.strip() for c in channels.split(",") if c.strip()]
    svc = RegistrationNotificationEngine(db)
    try:
        notifs = await svc.send_registration_confirmation(
            patient_id=patient_id, channels=channel_list
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return RegistrationNotifyResponse(
        notifications_sent=len(notifs),
        details=[RegistrationNotificationOut.model_validate(n) for n in notifs],
    )


@router.get(
    "/notifications/{patient_id}",
    response_model=list[RegistrationNotificationOut],
)
async def get_notification_log(
    patient_id: uuid.UUID,
    db: DBSession,
    user: CurrentUser,
) -> list[RegistrationNotificationOut]:
    """Get notification history for a patient."""
    svc = RegistrationNotificationEngine(db)
    log = await svc.get_notification_log(patient_id=patient_id)
    return [RegistrationNotificationOut.model_validate(n) for n in log]
