"""
LIS Analyzer & Device Integration Engine – API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db

from .schemas import (
    DeviceCreate, DeviceUpdate, DeviceOut,
    WorklistSendRequest, BatchWorklistRequest, AnalyzerWorklistOut,
    AnalyzerResultReceive, BatchResultReceive, VerifyResultRequest, AnalyzerResultOut,
    RecordReagentRequest, ReagentUsageOut,
    ReportErrorRequest, ResolveErrorRequest, DeviceErrorOut,
    DeviceAuditOut, AnalyzerDashboardStats,
)
from .services import (
    DeviceService, WorklistDistributionService, ResultImportService,
    ReagentService, DeviceErrorService, DeviceAuditService, AnalyzerStatsService,
)

router = APIRouter(prefix="/analyzer-integration", tags=["Analyzer & Device Integration"])


def _s(obj, cls):
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

@router.get("/dashboard", response_model=AnalyzerDashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    stats = await AnalyzerStatsService.get_stats(db)
    return AnalyzerDashboardStats(**stats)


# ── Device Management ────────────────────────────────────────────────────────

@router.post("/devices", response_model=DeviceOut, status_code=201)
async def register_device(req: DeviceCreate, db: AsyncSession = Depends(get_db)):
    existing = await DeviceService.get_device_by_code(db, req.device_code)
    if existing:
        raise HTTPException(400, f"Device code '{req.device_code}' already exists")
    device = await DeviceService.register_device(db, req.model_dump())
    return _s(device, DeviceOut)


@router.get("/devices", response_model=list[DeviceOut])
async def list_devices(
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items = await DeviceService.list_devices(db, department, status)
    return [_s(i, DeviceOut) for i in items]


@router.get("/devices/{device_id}", response_model=DeviceOut)
async def get_device(device_id: str, db: AsyncSession = Depends(get_db)):
    d = await DeviceService.get_device(db, device_id)
    if not d:
        raise HTTPException(404, "Device not found")
    return _s(d, DeviceOut)


@router.put("/devices/{device_id}", response_model=DeviceOut)
async def update_device(device_id: str, req: DeviceUpdate, db: AsyncSession = Depends(get_db)):
    d = await DeviceService.update_device(db, device_id, req.model_dump(exclude_unset=True))
    if not d:
        raise HTTPException(404, "Device not found")
    return _s(d, DeviceOut)


@router.put("/devices/{device_id}/status", response_model=DeviceOut)
async def update_device_status(device_id: str, status: str = Query(...),
                               performed_by: Optional[str] = Query(None),
                               db: AsyncSession = Depends(get_db)):
    d = await DeviceService.update_status(db, device_id, status, performed_by)
    if not d:
        raise HTTPException(404, "Device not found")
    return _s(d, DeviceOut)


# ── Worklist Distribution ────────────────────────────────────────────────────

@router.post("/worklists", response_model=AnalyzerWorklistOut)
async def send_worklist(req: WorklistSendRequest, db: AsyncSession = Depends(get_db)):
    try:
        wl = await WorklistDistributionService.send_worklist(db, req.model_dump())
        return _s(wl, AnalyzerWorklistOut)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/worklists/batch", response_model=list[AnalyzerWorklistOut])
async def batch_send_worklists(req: BatchWorklistRequest, db: AsyncSession = Depends(get_db)):
    items = [i.model_dump() for i in req.items]
    results = await WorklistDistributionService.batch_send(db, req.device_id, items)
    return [_s(r, AnalyzerWorklistOut) for r in results]


@router.get("/worklists", response_model=list[AnalyzerWorklistOut])
async def list_worklists(
    device_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items = await WorklistDistributionService.list_worklists(db, device_id, status)
    return [_s(i, AnalyzerWorklistOut) for i in items]


@router.put("/worklists/{wl_id}/acknowledge")
async def acknowledge_worklist(wl_id: str, db: AsyncSession = Depends(get_db)):
    await WorklistDistributionService.acknowledge(db, wl_id)
    return {"status": "acknowledged"}


# ── Result Import ─────────────────────────────────────────────────────────────

@router.post("/results", response_model=AnalyzerResultOut)
async def receive_result(req: AnalyzerResultReceive, db: AsyncSession = Depends(get_db)):
    try:
        r = await ResultImportService.receive_result(db, req.model_dump())
        return _s(r, AnalyzerResultOut)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/results/batch", response_model=list[AnalyzerResultOut])
async def batch_receive_results(req: BatchResultReceive, db: AsyncSession = Depends(get_db)):
    results = await ResultImportService.batch_receive(db, req.device_id,
                                                       [r.model_dump() for r in req.results])
    return [_s(r, AnalyzerResultOut) for r in results]


@router.get("/results", response_model=list[AnalyzerResultOut])
async def list_results(
    device_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    unverified: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    items = await ResultImportService.list_results(db, device_id, status, unverified)
    return [_s(i, AnalyzerResultOut) for i in items]


@router.put("/results/{result_id}/verify", response_model=AnalyzerResultOut)
async def verify_result(result_id: str, req: VerifyResultRequest,
                        db: AsyncSession = Depends(get_db)):
    r = await ResultImportService.verify_result(db, result_id, req.verified_by)
    if not r:
        raise HTTPException(404, "Result not found")
    return _s(r, AnalyzerResultOut)


@router.put("/results/{result_id}/import")
async def import_result(result_id: str, db: AsyncSession = Depends(get_db)):
    await ResultImportService.import_to_lis(db, result_id)
    return {"status": "imported"}


# ── Reagent Tracking ──────────────────────────────────────────────────────────

@router.post("/reagents", response_model=ReagentUsageOut)
async def record_reagent(req: RecordReagentRequest, db: AsyncSession = Depends(get_db)):
    r = await ReagentService.record_usage(db, req.model_dump())
    return _s(r, ReagentUsageOut)


@router.get("/reagents", response_model=list[ReagentUsageOut])
async def list_reagents(
    device_id: Optional[str] = Query(None),
    low_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    items = await ReagentService.list_usage(db, device_id, low_only)
    return [_s(i, ReagentUsageOut) for i in items]


# ── Error Handling ────────────────────────────────────────────────────────────

@router.post("/errors", response_model=DeviceErrorOut)
async def report_error(req: ReportErrorRequest, db: AsyncSession = Depends(get_db)):
    e = await DeviceErrorService.report_error(db, req.model_dump())
    return _s(e, DeviceErrorOut)


@router.get("/errors", response_model=list[DeviceErrorOut])
async def list_errors(
    device_id: Optional[str] = Query(None),
    unresolved: bool = Query(False),
    db: AsyncSession = Depends(get_db),
):
    items = await DeviceErrorService.list_errors(db, device_id, unresolved)
    return [_s(i, DeviceErrorOut) for i in items]


@router.put("/errors/{error_id}/resolve")
async def resolve_error(error_id: str, req: ResolveErrorRequest,
                        db: AsyncSession = Depends(get_db)):
    await DeviceErrorService.resolve_error(db, error_id, req.resolved_by)
    return {"status": "resolved"}


# ── Audit ─────────────────────────────────────────────────────────────────────

@router.get("/audit", response_model=list[DeviceAuditOut])
async def get_audit(
    device_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
):
    items = await DeviceAuditService.get_trail(db, device_id, action, limit)
    return [_s(i, DeviceAuditOut) for i in items]
