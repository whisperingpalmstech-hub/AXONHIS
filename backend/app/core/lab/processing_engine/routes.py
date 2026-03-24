"""
LIS Laboratory Processing & Result Entry Engine – API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.database import get_db

from .schemas import (
    WorklistOut, AssignTechRequest, StartProcessingRequest,
    EnterResultRequest, BatchResultRequest, ResultOut, ReviewResultRequest,
    FlagOut, DeltaOut, CommentOut,
    RecordQCRequest, QCOut,
    AddCommentRequest,
    AuditOut, ProcessingStats,
    ValidateResultRequest, ReleaseResultRequest, RejectResultRequest,
)
from .services import (
    WorklistService, ResultService, QCService,
    CommentService, AuditService, StatsService,
)

router = APIRouter(prefix="/lab-processing", tags=["Laboratory Processing & Result Entry"])


def _s(obj, cls):
    """Serialize SQLAlchemy model to Pydantic schema."""
    d = {}
    for k in cls.model_fields:
        v = getattr(obj, k, None)
        if v is not None and hasattr(v, "isoformat"):
            v = v.isoformat()
        elif v is not None and hasattr(v, "hex"):
            v = str(v)
        if k in ("flags", "delta", "comments"):
            continue
        d[k] = v
    return cls(**d)


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=ProcessingStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    stats = await StatsService.get_stats(db)
    return ProcessingStats(**stats)


# ── Worklist ──────────────────────────────────────────────────────────────────

@router.get("/worklist", response_model=list[WorklistOut])
async def list_worklist(
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items = await WorklistService.list_worklist(db, department, status, priority)
    return [_s(i, WorklistOut) for i in items]


@router.get("/worklist/{wl_id}", response_model=WorklistOut)
async def get_worklist_item(wl_id: str, db: AsyncSession = Depends(get_db)):
    item = await WorklistService.get_item(db, wl_id)
    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")
    return _s(item, WorklistOut)


@router.put("/worklist/{wl_id}/assign", response_model=WorklistOut)
async def assign_technician(wl_id: str, req: AssignTechRequest,
                            db: AsyncSession = Depends(get_db)):
    item = await WorklistService.assign_technician(db, wl_id, req.technician)
    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")
    return _s(item, WorklistOut)


@router.put("/worklist/{wl_id}/start", response_model=WorklistOut)
async def start_processing(wl_id: str, req: StartProcessingRequest,
                           db: AsyncSession = Depends(get_db)):
    item = await WorklistService.start_processing(db, wl_id, req.technician)
    if not item:
        raise HTTPException(status_code=404, detail="Worklist item not found")
    return _s(item, WorklistOut)


@router.post("/worklist/create", response_model=WorklistOut)
async def create_worklist_item(
    receipt_id: str = "", sample_id: str = "", barcode: str = "",
    order_id: str = "", order_number: str = "",
    patient_id: str = "", patient_name: str = "", patient_uhid: str = "",
    test_code: str = "", test_name: str = "", sample_type: str = "",
    department: str = "", priority: str = "ROUTINE",
    db: AsyncSession = Depends(get_db),
):
    item = await WorklistService.create_from_routing(
        db, receipt_id, sample_id, barcode, order_id, order_number,
        patient_id, patient_name, patient_uhid,
        test_code, test_name, sample_type, department, priority,
    )
    return _s(item, WorklistOut)


# ── Result Entry ──────────────────────────────────────────────────────────────

@router.post("/results", response_model=ResultOut)
async def enter_result(req: EnterResultRequest, db: AsyncSession = Depends(get_db)):
    try:
        r = await ResultService.enter_result(
            db, req.worklist_id, req.result_type,
            req.result_value, req.result_numeric, req.result_unit,
            req.result_source, req.entered_by, req.analyzer_id, req.comments,
        )
        return await _build_result_out(db, r)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/results/batch", response_model=list[ResultOut])
async def batch_enter_results(req: BatchResultRequest, db: AsyncSession = Depends(get_db)):
    items = [item.model_dump() for item in req.items]
    results = await ResultService.batch_enter(db, items, req.result_source, req.entered_by)
    return [await _build_result_out(db, r) for r in results]


@router.get("/results", response_model=list[ResultOut])
async def list_results(
    patient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    results = await ResultService.list_results(db, patient_id, status)
    return [await _build_result_out(db, r) for r in results]


@router.get("/results/{result_id}", response_model=ResultOut)
async def get_result(result_id: str, db: AsyncSession = Depends(get_db)):
    data = await ResultService.get_result_with_details(db, result_id)
    if not data or not data.get("result"):
        raise HTTPException(status_code=404, detail="Result not found")
    return _build_result_out_from_dict(data)


@router.put("/results/{result_id}/review", response_model=ResultOut)
async def review_result(result_id: str, req: ReviewResultRequest,
                        db: AsyncSession = Depends(get_db)):
    r = await ResultService.review_result(db, result_id, req.reviewed_by, req.remarks)
    if not r:
        raise HTTPException(status_code=404, detail="Result not found")
    return await _build_result_out(db, r)


@router.put("/results/{result_id}/validate", response_model=ResultOut)
async def validate_result(result_id: str, req: ValidateResultRequest,
                          db: AsyncSession = Depends(get_db)):
    try:
        r = await ResultService.validate_result(db, result_id, req.validated_by, req.remarks)
        if not r:
            raise HTTPException(status_code=404, detail="Result not found")
        return await _build_result_out(db, r)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/results/{result_id}/release", response_model=ResultOut)
async def release_result(result_id: str, req: ReleaseResultRequest,
                         db: AsyncSession = Depends(get_db)):
    try:
        r = await ResultService.release_result(db, result_id, req.released_by, req.remarks)
        if not r:
            raise HTTPException(status_code=404, detail="Result not found")
        return await _build_result_out(db, r)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/results/{result_id}/reject", response_model=ResultOut)
async def reject_result(result_id: str, req: RejectResultRequest,
                        db: AsyncSession = Depends(get_db)):
    try:
        r = await ResultService.reject_result(db, result_id, req.rejected_by, req.reason)
        if not r:
            raise HTTPException(status_code=404, detail="Result not found")
        return await _build_result_out(db, r)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


async def _build_result_out(db: AsyncSession, result) -> ResultOut:
    from sqlalchemy import select as sel
    from .models import ResultFlag as RF, DeltaCheck as DC, ResultComment as RC

    flags = list((await db.execute(sel(RF).where(RF.result_id == result.id))).scalars().all())
    delta = (await db.execute(sel(DC).where(DC.result_id == result.id))).scalar_one_or_none()
    comments = list((await db.execute(sel(RC).where(RC.result_id == result.id))).scalars().all())

    d = {}
    for k in ResultOut.model_fields:
        if k in ("flags", "delta", "comments"):
            continue
        v = getattr(result, k, None)
        if v is not None and hasattr(v, "isoformat"):
            v = v.isoformat()
        elif v is not None and hasattr(v, "hex"):
            v = str(v)
        d[k] = v

    d["flags"] = [_s(f, FlagOut) for f in flags]
    d["delta"] = _s(delta, DeltaOut) if delta else None
    d["comments"] = [_s(c, CommentOut) for c in comments]
    return ResultOut(**d)


def _build_result_out_from_dict(data: dict) -> ResultOut:
    result = data["result"]
    d = {}
    for k in ResultOut.model_fields:
        if k in ("flags", "delta", "comments"):
            continue
        v = getattr(result, k, None)
        if v is not None and hasattr(v, "isoformat"):
            v = v.isoformat()
        elif v is not None and hasattr(v, "hex"):
            v = str(v)
        d[k] = v
    d["flags"] = [_s(f, FlagOut) for f in data.get("flags", [])]
    d["delta"] = _s(data["delta"], DeltaOut) if data.get("delta") else None
    d["comments"] = [_s(c, CommentOut) for c in data.get("comments", [])]
    return ResultOut(**d)


# ── QC ────────────────────────────────────────────────────────────────────────

@router.post("/qc", response_model=QCOut)
async def record_qc(req: RecordQCRequest, db: AsyncSession = Depends(get_db)):
    qc = await QCService.record_qc(db, req.model_dump())
    return _s(qc, QCOut)


@router.get("/qc", response_model=list[QCOut])
async def list_qc(
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    items = await QCService.list_qc(db, department, status)
    return [_s(i, QCOut) for i in items]


# ── Comments ──────────────────────────────────────────────────────────────────

@router.post("/comments", response_model=CommentOut)
async def add_comment(req: AddCommentRequest, db: AsyncSession = Depends(get_db)):
    c = await CommentService.add_comment(
        db, req.result_id, req.comment_type, req.comment_text, req.added_by,
    )
    return _s(c, CommentOut)


@router.get("/comments/{result_id}", response_model=list[CommentOut])
async def get_comments(result_id: str, db: AsyncSession = Depends(get_db)):
    items = await CommentService.get_comments(db, result_id)
    return [_s(i, CommentOut) for i in items]


@router.get("/comments/library/{department}")
async def get_comment_library(department: str):
    """Return predefined comment templates for a department."""
    return CommentService.get_comment_library(department)


# ── Audit ─────────────────────────────────────────────────────────────────────

@router.get("/audit", response_model=list[AuditOut])
async def get_audit(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    limit: int = Query(50),
    db: AsyncSession = Depends(get_db),
):
    items = await AuditService.get_trail(db, entity_type, entity_id, limit)
    return [_s(i, AuditOut) for i in items]
