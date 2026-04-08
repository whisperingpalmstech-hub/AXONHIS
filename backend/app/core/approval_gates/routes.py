from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.approval_gates.schemas import (
    ApprovalGateCreate,
    ApprovalGateResponse,
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovalActionCreate,
    ApprovalActionResponse,
    ApprovalCheckResult
)
from app.core.approval_gates.services import ApprovalGateService
from app.database import get_db

router = APIRouter(prefix="/approval-gates", tags=["approval-gates"])


@router.post("/gates", response_model=ApprovalGateResponse)
async def create_gate(
    gate_data: ApprovalGateCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new approval gate."""
    service = ApprovalGateService(db)
    gate = await service.create_gate(gate_data)
    return gate


@router.get("/gates/{gate_id}", response_model=ApprovalGateResponse)
async def get_gate(
    gate_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific approval gate."""
    service = ApprovalGateService(db)
    gate = await service.get_gate(gate_id)
    if not gate:
        raise HTTPException(status_code=404, detail="Approval gate not found")
    return gate


@router.post("/check", response_model=ApprovalCheckResult)
async def check_approval_required(
    gate_code: str,
    request_data: dict,
    facility_id: UUID = Query(None),
    specialty_profile_id: UUID = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Check if approval is required for an operation."""
    service = ApprovalGateService(db)
    result = await service.check_approval_required(
        gate_code=gate_code,
        request_data=request_data,
        facility_id=facility_id,
        specialty_profile_id=specialty_profile_id
    )
    return result


@router.post("/requests", response_model=ApprovalRequestResponse)
async def create_approval_request(
    request_data: ApprovalRequestCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new approval request."""
    service = ApprovalGateService(db)
    request = await service.create_approval_request(request_data)
    return request


@router.get("/requests/{request_id}", response_model=ApprovalRequestResponse)
async def get_request(
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific approval request."""
    service = ApprovalGateService(db)
    request = await service.get_request(request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request


@router.get("/requests/pending", response_model=List[ApprovalRequestResponse])
async def get_pending_requests(
    approver_id: UUID = Query(None),
    patient_id: UUID = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """Get pending approval requests."""
    service = ApprovalGateService(db)
    requests = await service.get_pending_requests(approver_id, patient_id, limit)
    return requests


@router.post("/requests/{request_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(
    request_id: UUID,
    action_data: ApprovalActionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Approve an approval request."""
    service = ApprovalGateService(db)
    request = await service.approve_request(request_id, action_data)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request


@router.post("/requests/{request_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    request_id: UUID,
    action_data: ApprovalActionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Reject an approval request."""
    service = ApprovalGateService(db)
    request = await service.reject_request(request_id, action_data)
    if not request:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return request


@router.get("/requests/{request_id}/actions", response_model=List[ApprovalActionResponse])
async def get_request_actions(
    request_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get all actions for an approval request."""
    service = ApprovalGateService(db)
    actions = await service.get_request_actions(request_id)
    return actions


@router.post("/process-expired")
async def process_expired_requests(
    db: AsyncSession = Depends(get_db)
):
    """Process expired approval requests."""
    service = ApprovalGateService(db)
    result = await service.process_expired_requests()
    return result


@router.post("/process-auto-approve")
async def process_auto_approve(
    db: AsyncSession = Depends(get_db)
):
    """Process auto-approve based on timeout."""
    service = ApprovalGateService(db)
    result = await service.process_auto_approve()
    return result
