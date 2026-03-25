import uuid
from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from .schemas import IPReturnCreate, IPReturnOut, IPReturnProcess, IPReturnLogOut
from .services import IPReturnsService

router = APIRouter()

@router.post("/", response_model=IPReturnOut, status_code=201)
async def create_return_request(
    data: IPReturnCreate,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Create a new IP Pharmacy Return or Rejection request"""
    svc = IPReturnsService(db)
    req = await svc.create_return_request(data)
    return await svc.get_return(req.id)

@router.post("/seed-mock")
async def seed_mock_returns(db: AsyncSession = Depends(get_db)):
    """Seed dummy returns for UI testing without full Nursing flow"""
    from datetime import datetime, timezone
    from ...pharmacy.ip_issues.models import PharmacyIPPendingIssue, PharmacyIPDispenseRecord
    from ...pharmacy.ip_returns.models import PharmacyIPReturn, PharmacyIPReturnItem, PharmacyIPReturnLog
    import uuid

    mock_issue_id = uuid.uuid4()
    mock_dispense_id = uuid.uuid4()
    
    # 1. Provide valid FK issue & dispense record
    issue = PharmacyIPPendingIssue(
        id=mock_issue_id,
        patient_id=uuid.uuid4(),
        patient_name="Rahul Verma",
        uhid="UHID9999",
        admission_number="IP-24-99999",
        ward="General Ward",
        bed_number="Bed 10",
        treating_doctor_name="Dr. Smith",
        source="Nursing Station"
    )
    db.add(issue)
    
    disp = PharmacyIPDispenseRecord(
        id=mock_dispense_id,
        issue_id=mock_issue_id,
        medication_name="Amoxicillin 500mg",
        prescribed_quantity=10,
        dispensed_quantity=10
    )
    db.add(disp)

    # 2. Add the mock return
    mock_return_id = uuid.uuid4()
    ret = PharmacyIPReturn(
        id=mock_return_id,
        request_type="Return",
        issue_id=mock_issue_id,
        patient_id=issue.patient_id,
        patient_name="Rahul Verma",
        uhid="UHID9999",
        admission_number="IP-24-99999",
        ward="General Ward",
        bed_number="Bed 10",
        requested_by="Nurse Pooja",
        request_date=datetime.now(timezone.utc)
    )
    db.add(ret)
    
    item = PharmacyIPReturnItem(
        return_id=mock_return_id,
        dispense_record_id=mock_dispense_id,
        medication_name="Amoxicillin 500mg",
        return_quantity=5,
        reason="Treatment Discontinued",
        condition="Intact",
        is_restockable=True
    )
    db.add(item)
    
    log = PharmacyIPReturnLog(
        return_id=mock_return_id,
        action_type="Created",
        details={"requested_by": "Nurse Pooja", "remarks": "mocked"}
    )
    db.add(log)
    await db.commit()
    return {"status": "success", "message": "Seeded mock return WITH related records"}    
    item = PharmacyIPReturnItem(
        return_id=mock_return_id,
        dispense_record_id=uuid.uuid4(),
        medication_name="Amoxicillin 500mg",
        return_quantity=5,
        reason="Treatment Discontinued",
        condition="Intact",
        is_restockable=True
    )
    db.add(item)
    
    log = PharmacyIPReturnLog(
        return_id=mock_return_id,
        action_type="Created",
        details={"requested_by": "Nurse Pooja", "remarks": "mocked"}
    )
    db.add(log)
    await db.commit()
    return {"status": "success", "message": "Seeded mock return"}

@router.get("/", response_model=List[IPReturnOut])
async def list_returns(
    status: str = None,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """List pending/processed IP Pharmacy Returns and Rejections"""
    svc = IPReturnsService(db)
    return await svc.list_returns(status)

@router.get("/{return_id}", response_model=IPReturnOut)
async def get_return(
    return_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get single return request with all items and logs"""
    svc = IPReturnsService(db)
    return await svc.get_return(return_id)

@router.post("/{return_id}/process", response_model=IPReturnOut)
async def process_return(
    return_id: uuid.UUID,
    data: IPReturnProcess,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Pharmacy accepts or rejects the return request"""
    import uuid as sys_uuid
    svc = IPReturnsService(db)
    # Using a dummy pharmacist UUID placeholder since we removed current_user
    processed = await svc.process_return(return_id, data, sys_uuid.uuid4())
    return await svc.get_return(processed.id)

@router.get("/{return_id}/audit", response_model=List[IPReturnLogOut])
async def get_return_audit(
    return_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """Get the immutable audit logs for a return"""
    svc = IPReturnsService(db)
    ret = await svc.get_return(return_id)
    return ret.logs
