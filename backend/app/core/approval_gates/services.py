from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, update

from app.core.approval_gates.models import (
    MdApprovalGate,
    MdApprovalRequest,
    MdApprovalAction,
    ApprovalStatus,
    ApprovalPriority
)
from app.core.approval_gates.schemas import (
    ApprovalGateCreate,
    ApprovalRequestCreate,
    ApprovalActionCreate
)


class ApprovalGateService:
    """Service for managing approval gates for high-risk operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_gate(
        self,
        gate_data: ApprovalGateCreate
    ) -> MdApprovalGate:
        """Create a new approval gate."""
        gate = MdApprovalGate(
            gate_name=gate_data.gate_name,
            gate_code=gate_data.gate_code,
            gate_type=gate_data.gate_type,
            risk_level=gate_data.risk_level,
            description=gate_data.description,
            approval_criteria=gate_data.approval_criteria,
            required_roles=gate_data.required_roles,
            auto_approve_after_minutes=gate_data.auto_approve_after_minutes,
            notify_approvers=gate_data.notify_approvers,
            facility_id=gate_data.facility_id,
            specialty_profile_id=gate_data.specialty_profile_id
        )
        self.db.add(gate)
        await self.db.commit()
        await self.db.refresh(gate)
        return gate

    async def get_gate(
        self,
        gate_id: uuid.UUID
    ) -> Optional[MdApprovalGate]:
        """Get a specific approval gate."""
        query = select(MdApprovalGate).where(
            MdApprovalGate.gate_id == gate_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_gate_by_code(
        self,
        gate_code: str
    ) -> Optional[MdApprovalGate]:
        """Get an approval gate by code."""
        query = select(MdApprovalGate).where(
            and_(
                MdApprovalGate.gate_code == gate_code,
                MdApprovalGate.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def check_approval_required(
        self,
        gate_code: str,
        request_data: Dict[str, Any],
        facility_id: Optional[uuid.UUID] = None,
        specialty_profile_id: Optional[uuid.UUID] = None
    ) -> Dict[str, Any]:
        """Check if approval is required for an operation."""
        gate = await self.get_gate_by_code(gate_code)
        
        if not gate or not gate.is_active:
            return {
                "requires_approval": False,
                "reason": "No active approval gate found"
            }
        
        # Check facility/specificity match
        if gate.facility_id and facility_id != gate.facility_id:
            return {
                "requires_approval": False,
                "reason": "Gate not applicable to this facility"
            }
        
        if gate.specialty_profile_id and specialty_profile_id != gate.specialty_profile_id:
            return {
                "requires_approval": False,
                "reason": "Gate not applicable to this specialty"
            }
        
        # Check approval criteria
        criteria = gate.approval_criteria
        for key, expected_value in criteria.items():
            if key in request_data:
                if request_data[key] != expected_value:
                    return {
                        "requires_approval": False,
                        "reason": f"Criteria {key} does not match"
                    }
        
        return {
            "requires_approval": True,
            "gate_id": str(gate.gate_id),
            "gate_name": gate.gate_name,
            "risk_level": gate.risk_level
        }

    async def create_approval_request(
        self,
        request_data: ApprovalRequestCreate
    ) -> MdApprovalRequest:
        """Create a new approval request."""
        # Calculate expiration
        expires_at = None
        if request_data.expires_after_minutes:
            expires_at = datetime.utcnow() + timedelta(minutes=request_data.expires_after_minutes)
        
        request = MdApprovalRequest(
            gate_id=request_data.gate_id,
            request_type=request_data.request_type,
            request_data=request_data.request_data,
            requester_id=request_data.requester_id,
            requester_name=request_data.requester_name,
            patient_id=request_data.patient_id,
            encounter_id=request_data.encounter_id,
            priority=request_data.priority,
            urgency_reason=request_data.urgency_reason,
            expires_at=expires_at
        )
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        
        # Notify approvers if configured
        gate = await self.get_gate(request_data.gate_id)
        if gate and gate.notify_approvers:
            await self._notify_approvers(request, gate)
        
        return request

    async def approve_request(
        self,
        request_id: uuid.UUID,
        action_data: ApprovalActionCreate
    ) -> Optional[MdApprovalRequest]:
        """Approve an approval request."""
        return await self._process_request(
            request_id=request_id,
            action_data=action_data,
            action="APPROVE"
        )

    async def reject_request(
        self,
        request_id: uuid.UUID,
        action_data: ApprovalActionCreate
    ) -> Optional[MdApprovalRequest]:
        """Reject an approval request."""
        return await self._process_request(
            request_id=request_id,
            action_data=action_data,
            action="REJECT"
        )

    async def _process_request(
        self,
        request_id: uuid.UUID,
        action_data: ApprovalActionCreate,
        action: str
    ) -> Optional[MdApprovalRequest]:
        """Process an approval action."""
        query = select(MdApprovalRequest).where(
            MdApprovalRequest.request_id == request_id
        )
        result = await self.db.execute(query)
        request = result.scalar_one_or_none()
        
        if not request:
            return None
        
        # Check if request is still pending
        if request.status != ApprovalStatus.PENDING:
            raise ValueError(f"Request is not pending. Current status: {request.status}")
        
        # Create action record
        approval_action = MdApprovalAction(
            request_id=request_id,
            approver_id=action_data.approver_id,
            approver_name=action_data.approver_name,
            approver_role=action_data.approver_role,
            action=action,
            comments=action_data.comments,
            action_data=action_data.action_data
        )
        self.db.add(approval_action)
        
        # Update request status
        if action == "APPROVE":
            request.status = ApprovalStatus.APPROVED
            request.approved_at = datetime.utcnow()
            request.approved_by = action_data.approver_name
        elif action == "REJECT":
            request.status = ApprovalStatus.REJECTED
            request.rejected_at = datetime.utcnow()
            request.rejected_by = action_data.approver_name
            request.rejection_reason = action_data.comments
        
        await self.db.commit()
        await self.db.refresh(request)
        
        return request

    async def get_request(
        self,
        request_id: uuid.UUID
    ) -> Optional[MdApprovalRequest]:
        """Get a specific approval request."""
        query = select(MdApprovalRequest).where(
            MdApprovalRequest.request_id == request_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_requests(
        self,
        approver_id: Optional[uuid.UUID] = None,
        patient_id: Optional[uuid.UUID] = None,
        limit: int = 100
    ) -> List[MdApprovalRequest]:
        """Get pending approval requests."""
        conditions = [MdApprovalRequest.status == ApprovalStatus.PENDING]
        
        if patient_id:
            conditions.append(MdApprovalRequest.patient_id == patient_id)
        
        # Filter expired requests
        conditions.append(
            or_(
                MdApprovalRequest.expires_at.is_(None),
                MdApprovalRequest.expires_at > datetime.utcnow()
            )
        )
        
        query = select(MdApprovalRequest).where(
            and_(*conditions)
        ).order_by(desc(MdApprovalRequest.priority), MdApprovalRequest.created_at).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_request_actions(
        self,
        request_id: uuid.UUID
    ) -> List[MdApprovalAction]:
        """Get all actions for an approval request."""
        query = select(MdApprovalAction).where(
            MdApprovalAction.request_id == request_id
        ).order_by(MdApprovalAction.created_at)
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def process_expired_requests(self) -> Dict[str, int]:
        """Process expired approval requests."""
        now = datetime.utcnow()
        
        # Find expired pending requests
        query = select(MdApprovalRequest).where(
            and_(
                MdApprovalRequest.status == ApprovalStatus.PENDING,
                MdApprovalRequest.expires_at <= now
            )
        )
        
        result = await self.db.execute(query)
        expired_requests = result.scalars().all()
        
        expired_count = 0
        for request in expired_requests:
            request.status = ApprovalStatus.EXPIRED
            expired_count += 1
        
        await self.db.commit()
        
        return {"expired_count": expired_count}

    async def process_auto_approve(self) -> Dict[str, int]:
        """Process auto-approve based on timeout."""
        now = datetime.utcnow()
        
        # Get gates with auto-approve configured
        query = select(MdApprovalRequest).join(
            MdApprovalGate,
            MdApprovalRequest.gate_id == MdApprovalGate.gate_id
        ).where(
            and_(
                MdApprovalRequest.status == ApprovalStatus.PENDING,
                MdApprovalGate.auto_approve_after_minutes.isnot(None)
            )
        )
        
        result = await self.db.execute(query)
        requests = result.scalars().all()
        
        auto_approved_count = 0
        for request in requests:
            gate = await self.get_gate(request.gate_id)
            if gate:
                # Check if timeout has passed
                timeout_minutes = gate.auto_approve_after_minutes
                timeout_time = request.created_at + timedelta(minutes=timeout_minutes)
                
                if now >= timeout_time:
                    request.status = ApprovalStatus.APPROVED
                    request.approved_at = now
                    request.approved_by = "SYSTEM_AUTO_APPROVE"
                    auto_approved_count += 1
        
        await self.db.commit()
        
        return {"auto_approved_count": auto_approved_count}

    async def _notify_approvers(
        self,
        request: MdApprovalRequest,
        gate: MdApprovalGate
    ):
        """Notify approvers of new approval request."""
        # In a real implementation, this would send notifications via email, SMS, in-app, etc.
        # For now, we'll just log it
        pass
