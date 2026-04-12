"""
LIS Central Receiving & Specimen Tracking Engine – API Routes
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db

from .schemas import (
    RegisterSampleRequest, ReceiptOut,
    VerifySampleRequest, VerificationOut,
    RejectSampleRequest, RejectionOut,
    RouteSampleRequest, ReceiveAtDeptRequest, RoutingOut,
    StoreSampleRequest, RetrieveSampleRequest, StorageOut,
    CustodyEntryOut, AlertOut, AcknowledgeAlertRequest,
    CRAuditOut, DashboardStats,
)
from .services import (
    ReceiptService, VerificationService, RejectionService,
    RoutingService, StorageService, ChainOfCustodyService,
    AlertService, CRAuditService, DashboardService,
)

router = APIRouter(prefix="/central-receiving", tags=["Central Receiving & Specimen Tracking"])


def _serialize(obj, cls):
    d = {}
    for k in cls.model_fields:
        v = getattr(obj, k, None)
        if v is not None and hasattr(v, "isoformat"):
            v = v.isoformat()
        elif v is not None and hasattr(v, "hex"):
            v = str(v)
        d[k] = v
    return cls(**d)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    stats = await DashboardService.get_stats(db)
    return DashboardStats(**stats)


# ── Receipt / Barcode Scan ────────────────────────────────────────────────────

@router.post("/receive", response_model=ReceiptOut)
async def register_sample(req: RegisterSampleRequest, db: AsyncSession = Depends(get_db)):
    try:
        receipt = await ReceiptService.register_by_barcode(db, req.barcode, req.received_by, req.notes)
        return _serialize(receipt, ReceiptOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/receipts", response_model=list[ReceiptOut])
async def list_receipts(
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items = await ReceiptService.list_receipts(db, status, priority)
    return [_serialize(i, ReceiptOut) for i in items]


@router.get("/receipts/{receipt_id}", response_model=ReceiptOut)
async def get_receipt(receipt_id: str, db: AsyncSession = Depends(get_db)):
    r = await ReceiptService.get_receipt(db, receipt_id)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return _serialize(r, ReceiptOut)


@router.get("/receipts/barcode/{barcode}", response_model=ReceiptOut)
async def get_receipt_by_barcode(barcode: str, db: AsyncSession = Depends(get_db)):
    r = await ReceiptService.get_receipt_by_barcode(db, barcode)
    if not r:
        raise HTTPException(status_code=404, detail="Receipt not found for barcode")
    return _serialize(r, ReceiptOut)


# ── Verification ──────────────────────────────────────────────────────────────

@router.post("/verify", response_model=VerificationOut)
async def verify_sample(req: VerifySampleRequest, db: AsyncSession = Depends(get_db)):
    try:
        checks = {
            "sample_type_correct": req.sample_type_correct,
            "container_correct": req.container_correct,
            "volume_adequate": req.volume_adequate,
            "labeling_correct": req.labeling_correct,
            "transport_ok": req.transport_ok,
            "hemolyzed": req.hemolyzed,
            "clotted": req.clotted,
        }
        v = await VerificationService.verify_sample(db, req.receipt_id, checks, req.verified_by, req.remarks)
        return _serialize(v, VerificationOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Rejection ─────────────────────────────────────────────────────────────────

@router.post("/reject", response_model=RejectionOut)
async def reject_sample(req: RejectSampleRequest, db: AsyncSession = Depends(get_db)):
    try:
        r = await RejectionService.reject_sample(
            db, req.receipt_id, req.rejection_reason,
            req.rejection_details, req.rejected_by, req.recollection_requested,
        )
        return _serialize(r, RejectionOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rejections", response_model=list[RejectionOut])
async def list_rejections(db: AsyncSession = Depends(get_db)):
    items = await RejectionService.list_rejections(db)
    return [_serialize(i, RejectionOut) for i in items]


# ── Routing ───────────────────────────────────────────────────────────────────

@router.post("/route", response_model=RoutingOut)
async def route_sample(req: RouteSampleRequest, db: AsyncSession = Depends(get_db)):
    try:
        r = await RoutingService.route_sample(
            db, req.receipt_id, req.target_department, req.routed_by, req.notes,
        )
        return _serialize(r, RoutingOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/routing/{routing_id}/receive", response_model=RoutingOut)
async def receive_at_department(routing_id: str, req: ReceiveAtDeptRequest,
                                 db: AsyncSession = Depends(get_db)):
    try:
        r = await RoutingService.receive_at_department(db, routing_id, req.received_by_dept)
        return _serialize(r, RoutingOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/routings", response_model=list[RoutingOut])
async def list_routings(department: Optional[str] = Query(None),
                        db: AsyncSession = Depends(get_db)):
    items = await RoutingService.list_routings(db, department)
    return [_serialize(i, RoutingOut) for i in items]


# ── Storage ───────────────────────────────────────────────────────────────────

@router.post("/store", response_model=StorageOut)
async def store_sample(req: StoreSampleRequest, db: AsyncSession = Depends(get_db)):
    try:
        s = await StorageService.store_sample(
            db, req.receipt_id, req.storage_location,
            req.storage_temperature, req.max_duration_hours, req.stored_by,
        )
        return _serialize(s, StorageOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/storage/{storage_id}/retrieve", response_model=StorageOut)
async def retrieve_sample(storage_id: str, req: RetrieveSampleRequest,
                          db: AsyncSession = Depends(get_db)):
    try:
        s = await StorageService.retrieve_sample(db, storage_id, req.retrieved_by)
        return _serialize(s, StorageOut)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/storage", response_model=list[StorageOut])
async def list_active_storage(db: AsyncSession = Depends(get_db)):
    items = await StorageService.list_active_storage(db)
    return [_serialize(i, StorageOut) for i in items]


# ── Chain of Custody ──────────────────────────────────────────────────────────

@router.get("/chain-of-custody/{receipt_id}", response_model=list[CustodyEntryOut])
async def get_chain_of_custody(receipt_id: str, db: AsyncSession = Depends(get_db)):
    items = await ChainOfCustodyService.get_chain(db, receipt_id)
    return [_serialize(i, CustodyEntryOut) for i in items]


# ── Alerts ────────────────────────────────────────────────────────────────────

@router.get("/alerts", response_model=list[AlertOut])
async def list_alerts(status: Optional[str] = Query(None),
                      db: AsyncSession = Depends(get_db)):
    items = await AlertService.list_alerts(db, status)
    return [_serialize(i, AlertOut) for i in items]


@router.put("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(alert_id: str, req: AcknowledgeAlertRequest,
                            db: AsyncSession = Depends(get_db)):
    a = await AlertService.acknowledge_alert(db, alert_id, req.acknowledged_by)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _serialize(a, AlertOut)


@router.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str, db: AsyncSession = Depends(get_db)):
    a = await AlertService.resolve_alert(db, alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _serialize(a, AlertOut)


# ── Audit Trail ───────────────────────────────────────────────────────────────

@router.get("/audit", response_model=list[CRAuditOut])
async def get_audit_trail(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    items = await CRAuditService.get_trail(db, entity_type, entity_id, limit)
    return [_serialize(i, CRAuditOut) for i in items]
