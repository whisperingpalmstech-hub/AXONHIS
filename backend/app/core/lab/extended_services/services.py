from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from datetime import datetime
import json

from .models import (
    LisHomeCollectionRequest, LisPhlebotomistSchedule,
    LisOutsourceLabMaster, LisExternalResult, LisQualityControl, LisEquipmentMaintenance
)
from .schemas import (
    HomeCollectionCreate, PhlebotomistScheduleCreate,
    OutsourceLabCreate, ExternalResultCreate, QualityControlCreate,
    EquipmentMaintenanceCreate
)

class ExtendedLabService:
    @staticmethod
    async def create_home_request(db: AsyncSession, req: HomeCollectionCreate) -> LisHomeCollectionRequest:
        new_req = LisHomeCollectionRequest(
            patient_name=req.patient_name,
            patient_uhid=req.patient_uhid,
            address=req.address,
            test_requested=req.test_requested,
            preferred_collection_time=req.preferred_collection_time.replace(tzinfo=None),
            status="Pending"
        )
        db.add(new_req)
        await db.commit()
        await db.refresh(new_req)
        return new_req

    @staticmethod
    async def get_home_collections(db: AsyncSession) -> List[LisHomeCollectionRequest]:
        res = await db.execute(select(LisHomeCollectionRequest).order_by(LisHomeCollectionRequest.created_at.desc()))
        return res.scalars().all()

    @staticmethod
    async def schedule_phlebotomist(db: AsyncSession, sched: PhlebotomistScheduleCreate) -> LisPhlebotomistSchedule:
        new_sched = LisPhlebotomistSchedule(
            request_id=sched.request_id,
            collection_date=sched.collection_date.replace(tzinfo=None),
            collection_time=sched.collection_time.replace(tzinfo=None),
            assigned_phlebotomist=sched.assigned_phlebotomist,
            collection_location=sched.collection_location,
            status="Scheduled"
        )
        # Update Request Status
        req_q = await db.execute(select(LisHomeCollectionRequest).where(LisHomeCollectionRequest.id == sched.request_id))
        hc_req = req_q.scalars().first()
        if hc_req: hc_req.status = "Scheduled"

        db.add(new_sched)
        await db.commit()
        await db.refresh(new_sched)
        return new_sched

    # Sample Transport is managed by the Phlebotomy Engine — no duplicate service here

    @staticmethod
    async def register_outsource_lab(db: AsyncSession, lab: OutsourceLabCreate) -> LisOutsourceLabMaster:
        new_lab = LisOutsourceLabMaster(
            lab_name=lab.lab_name,
            contact_details=lab.contact_details,
            test_capabilities=lab.test_capabilities
        )
        db.add(new_lab)
        await db.commit()
        await db.refresh(new_lab)
        return new_lab
        
    @staticmethod
    async def get_outsource_labs(db: AsyncSession) -> List[LisOutsourceLabMaster]:
        res = await db.execute(select(LisOutsourceLabMaster))
        return res.scalars().all()

    @staticmethod
    async def import_external_result(db: AsyncSession, er: ExternalResultCreate) -> LisExternalResult:
        new_res = LisExternalResult(
            outsource_lab_id=er.outsource_lab_id,
            test_order_id=er.test_order_id,
            sample_id=er.sample_id,
            patient_uhid=er.patient_uhid,
            result_data=er.result_data,
            is_validated=False
        )
        db.add(new_res)
        await db.commit()
        await db.refresh(new_res)
        return new_res

    @staticmethod
    async def record_qc(db: AsyncSession, qc: QualityControlCreate) -> LisQualityControl:
        threshold = qc.expected_value * 0.1 # Example 10% tolerance 
        diff = abs(qc.result_value - qc.expected_value)
        passed = diff <= threshold
        
        new_qc = LisQualityControl(
            test_name=qc.test_name,
            equipment_id=qc.equipment_id,
            result_value=qc.result_value,
            expected_value=qc.expected_value,
            is_passed=passed,
            failure_alert_sent=not passed,
            remarks="Tolerance breached" if not passed else "Within limits"
        )
        db.add(new_qc)
        await db.commit()
        await db.refresh(new_qc)
        return new_qc

    @staticmethod
    async def get_qcs(db: AsyncSession) -> List[LisQualityControl]:
        res = await db.execute(select(LisQualityControl).order_by(LisQualityControl.qc_date.desc()))
        return res.scalars().all()

    @staticmethod
    async def register_equipment(db: AsyncSession, eq: EquipmentMaintenanceCreate) -> LisEquipmentMaintenance:
        curr_time = datetime.utcnow()
        is_overdue = eq.next_maintenance_date.replace(tzinfo=None) < curr_time
        
        new_eq = LisEquipmentMaintenance(
            equipment_id=eq.equipment_id,
            equipment_name=eq.equipment_name,
            maintenance_schedule=eq.maintenance_schedule,
            last_calibration_date=eq.last_calibration_date.replace(tzinfo=None),
            next_maintenance_date=eq.next_maintenance_date.replace(tzinfo=None),
            service_history=eq.service_history,
            is_overdue=is_overdue
        )
        db.add(new_eq)
        await db.commit()
        await db.refresh(new_eq)
        return new_eq

    @staticmethod
    async def get_equipment(db: AsyncSession) -> List[LisEquipmentMaintenance]:
        # check overdues on fly
        eqs = (await db.execute(select(LisEquipmentMaintenance))).scalars().all()
        curr_time = datetime.utcnow()
        for eq in eqs:
            if eq.next_maintenance_date < curr_time and not eq.is_overdue:
                eq.is_overdue = True
                await db.commit()
        return eqs
