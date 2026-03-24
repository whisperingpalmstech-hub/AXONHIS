from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db

from .schemas import (
    ValidationWorklistOut, ApproveResultRequest, CorrectResultRequest, RejectResultRequest,
    BatchApproveRequest, ValidationPerformanceOut
)
from .services import ValidationService
from .models import ValidationWorklist

router = APIRouter(prefix="/validation", tags=["Result Validation Engine"])

@router.get("/worklist", response_model=List[ValidationWorklistOut])
async def get_validation_worklist(
    department: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    priority: Optional[str] = None,
    test_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    items = await ValidationService.get_worklist(db, department, stage, priority, test_type)
    return items

@router.get("/worklist/{item_id}", response_model=ValidationWorklistOut)
async def get_validation_item(item_id: str, db: AsyncSession = Depends(get_db)):
    item = await ValidationService.get_worklist_by_id(db, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Validation worklist item not found")
    return item

@router.put("/worklist/{item_id}/approve", response_model=ValidationWorklistOut)
async def approve_result_stage(item_id: str, req: ApproveResultRequest, db: AsyncSession = Depends(get_db)):
    try:
        updated = await ValidationService.approve_result(db, item_id, req)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/worklist/batch/approve")
async def batch_approve_results(req: BatchApproveRequest, db: AsyncSession = Depends(get_db)):
    count = await ValidationService.batch_approve(db, req.worklist_ids, req.validator_id, req.validator_name, req.stage_name)
    return {"message": f"Successfully batch approved {count} non-critical items."}

@router.put("/worklist/{item_id}/correct", response_model=ValidationWorklistOut)
async def correct_result_value(item_id: str, req: CorrectResultRequest, db: AsyncSession = Depends(get_db)):
    try:
        updated = await ValidationService.correct_result(db, item_id, req)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/worklist/{item_id}/reject", response_model=ValidationWorklistOut)
async def reject_result(item_id: str, req: RejectResultRequest, db: AsyncSession = Depends(get_db)):
    try:
        updated = await ValidationService.reject_result(db, item_id, req)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/worklist/{item_id}/flag-critical")
async def trigger_critical_alert(item_id: str, value: str, ref: str, message: str, db: AsyncSession = Depends(get_db)):
    await ValidationService.generate_critical_alert(db, item_id, value, ref, message)
    return {"message": "Critical alert triggered successfully."}

@router.get("/metrics", response_model=ValidationPerformanceOut)
async def get_validation_performance_metrics(db: AsyncSession = Depends(get_db)):
    metrics = await ValidationService.get_performance_metrics(db)
    return metrics
