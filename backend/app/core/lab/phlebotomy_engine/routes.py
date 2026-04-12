"""
LIS Phlebotomy & Sample Collection Engine – API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db

from .schemas import (
    WorklistItemOut, WorklistFilterParams,
    PatientVerificationRequest, PatientVerificationResponse,
    CollectSampleRequest, SampleCollectionOut, UpdateSampleStatusRequest,
    UploadConsentRequest, ConsentDocumentOut,
    CreateRepeatScheduleRequest, RepeatScheduleOut,
    CreateTransportBatchRequest, ReceiveTransportRequest, TransportBatchOut,
    BarcodeLabel, AuditEntryOut,
)
from .services import (
    WorklistService, PatientVerificationService, SampleCollectionService,
    ConsentService, RepeatScheduleService, TransportService, AuditService,
)

router = APIRouter(prefix="/phlebotomy", tags=["Phlebotomy & Sample Collection"])


def _serialize(obj, cls):
    """Quick serializer for SQLAlchemy → Pydantic."""
    d = {}
    for k in cls.model_fields:
        v = getattr(obj, k, None)
        if v is not None and hasattr(v, "isoformat"):
            v = v.isoformat()
        elif v is not None and hasattr(v, "hex"):
            v = str(v)
        d[k] = v
    return cls(**d)


# ── Worklist ──────────────────────────────────────────────────────────────────

@router.get("/worklist", response_model=list[WorklistItemOut])
async def get_worklist(
    location: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    collector: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items = await WorklistService.get_pending_worklist(db, location, priority, status, collector)
    return [_serialize(i, WorklistItemOut) for i in items]


@router.get("/worklist/{wl_id}", response_model=WorklistItemOut)
async def get_worklist_item(wl_id: str, db: AsyncSession = Depends(get_db)):
    item = await WorklistService.get_worklist_item(db, __import__("uuid").UUID(wl_id))
    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")
    return _serialize(item, WorklistItemOut)


@router.put("/worklist/{wl_id}/assign")
async def assign_collector(wl_id: str, collector: str = Query(...), db: AsyncSession = Depends(get_db)):
    item = await WorklistService.assign_collector(db, __import__("uuid").UUID(wl_id), collector)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")
    return _serialize(item, WorklistItemOut)


# ── Patient Verification ──────────────────────────────────────────────────────

@router.post("/verify-patient", response_model=PatientVerificationResponse)
async def verify_patient(req: PatientVerificationRequest, db: AsyncSession = Depends(get_db)):
    try:
        result = await PatientVerificationService.verify_patient(
            db, __import__("uuid").UUID(req.worklist_id), req.verification_method, req.verified_by
        )
        return PatientVerificationResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Sample Collection ────────────────────────────────────────────────────────

@router.post("/collect", response_model=SampleCollectionOut)
async def collect_sample(req: CollectSampleRequest, db: AsyncSession = Depends(get_db)):
    try:
        sample = await SampleCollectionService.collect_sample(
            db,
            worklist_id=req.worklist_id,
            collector_name=req.collector_name,
            collector_id=req.collector_id,
            container_type=req.container_type,
            collection_location=req.collection_location,
            identity_verified=req.identity_verified,
            identity_method=req.identity_method,
            notes=req.notes,
            quantity_ml=req.quantity_ml,
        )
        return _serialize(sample, SampleCollectionOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/samples", response_model=list[SampleCollectionOut])
async def list_samples(patient_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    items = await SampleCollectionService.list_collected(db, patient_id)
    return [_serialize(i, SampleCollectionOut) for i in items]


@router.get("/samples/{sample_id}", response_model=SampleCollectionOut)
async def get_sample(sample_id: str, db: AsyncSession = Depends(get_db)):
    s = await SampleCollectionService.get_sample(db, sample_id)
    if not s:
        raise HTTPException(status_code=404, detail="Sample not found")
    return _serialize(s, SampleCollectionOut)


@router.put("/samples/{sample_id}/status", response_model=SampleCollectionOut)
async def update_sample_status(sample_id: str, req: UpdateSampleStatusRequest, db: AsyncSession = Depends(get_db)):
    try:
        s = await SampleCollectionService.update_status(db, sample_id, req.status, req.updated_by, req.notes)
        return _serialize(s, SampleCollectionOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/samples/{sample_id}/barcode", response_model=BarcodeLabel)
async def get_barcode_label(sample_id: str, db: AsyncSession = Depends(get_db)):
    try:
        return await SampleCollectionService.get_barcode_label(db, sample_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Consent ───────────────────────────────────────────────────────────────────

@router.post("/consent", response_model=ConsentDocumentOut)
async def upload_consent(req: UploadConsentRequest, db: AsyncSession = Depends(get_db)):
    try:
        doc = await ConsentService.upload_consent(
            db, req.worklist_id, req.file_name, req.file_url, req.file_format, req.uploaded_by
        )
        return _serialize(doc, ConsentDocumentOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/consent/{worklist_id}", response_model=list[ConsentDocumentOut])
async def get_consent_docs(worklist_id: str, db: AsyncSession = Depends(get_db)):
    docs = await ConsentService.get_consent_for_worklist(db, worklist_id)
    return [_serialize(d, ConsentDocumentOut) for d in docs]


# ── Repeat Schedule ───────────────────────────────────────────────────────────

@router.post("/repeat-schedule", response_model=RepeatScheduleOut)
async def create_repeat_schedule(req: CreateRepeatScheduleRequest, db: AsyncSession = Depends(get_db)):
    sch = await RepeatScheduleService.create_schedule(
        db, req.order_id, req.patient_id, req.test_code, req.test_name,
        req.total_samples, req.interval_minutes, req.schedule_config,
    )
    return _serialize(sch, RepeatScheduleOut)


@router.get("/repeat-schedule", response_model=list[RepeatScheduleOut])
async def list_active_schedules(patient_id: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    items = await RepeatScheduleService.list_active(db, patient_id)
    return [_serialize(i, RepeatScheduleOut) for i in items]


@router.put("/repeat-schedule/{schedule_id}/collected", response_model=RepeatScheduleOut)
async def mark_repeat_collected(schedule_id: str, db: AsyncSession = Depends(get_db)):
    try:
        sch = await RepeatScheduleService.mark_sample_collected(db, schedule_id)
        return _serialize(sch, RepeatScheduleOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Transport ─────────────────────────────────────────────────────────────────

@router.post("/transport", response_model=TransportBatchOut)
async def create_transport_batch(req: CreateTransportBatchRequest, db: AsyncSession = Depends(get_db)):
    try:
        batch = await TransportService.create_batch(
            db, req.sample_ids, req.transport_personnel, req.transport_method, req.notes
        )
        return _serialize(batch, TransportBatchOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/transport/{batch_id}/receive", response_model=TransportBatchOut)
async def receive_transport_batch(batch_id: str, req: ReceiveTransportRequest, db: AsyncSession = Depends(get_db)):
    try:
        batch = await TransportService.receive_batch(db, batch_id, req.received_by)
        return _serialize(batch, TransportBatchOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/transport", response_model=list[TransportBatchOut])
async def list_transport_batches(status: Optional[str] = Query(None), db: AsyncSession = Depends(get_db)):
    items = await TransportService.list_batches(db, status)
    return [_serialize(i, TransportBatchOut) for i in items]


# ── Audit ─────────────────────────────────────────────────────────────────────

@router.get("/audit", response_model=list[AuditEntryOut])
async def get_audit_trail(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    items = await AuditService.get_audit_trail(db, entity_type, entity_id, limit)
    return [_serialize(i, AuditEntryOut) for i in items]
