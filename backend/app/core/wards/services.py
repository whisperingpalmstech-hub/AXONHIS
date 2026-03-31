from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from datetime import datetime, timezone
from app.core.wards.models import Ward, Room, Bed, BedAssignment, BedTransfer, BedCleaningTask
from app.core.wards.schemas import WardCreate, RoomCreate, BedCreate, BedAssignmentCreate, BedTransferCreate, CleaningStatus, BedStatus, AssignmentStatus
from fastapi import HTTPException
import uuid

class WardService:
    @staticmethod
    async def create_ward(db: AsyncSession, ward: WardCreate):
        db_ward = Ward(**ward.dict())
        db.add(db_ward)
        await db.commit()
        await db.refresh(db_ward)
        return db_ward

    @staticmethod
    async def create_room(db: AsyncSession, room: RoomCreate):
        db_room = Room(**room.dict())
        db.add(db_room)
        await db.commit()
        await db.refresh(db_room)
        return db_room

    @staticmethod
    async def create_bed(db: AsyncSession, bed: BedCreate):
        db_bed = Bed(**bed.dict())
        db.add(db_bed)
        await db.commit()
        await db.refresh(db_bed)
        return db_bed

    @staticmethod
    async def assign_bed(db: AsyncSession, assignment: BedAssignmentCreate):
        # 1. Validate bed availability
        res = await db.execute(select(Bed).filter(Bed.id == assignment.bed_id))
        bed = res.scalar_one_or_none()
        if not bed or bed.status != "available":
            raise HTTPException(status_code=400, detail="Bed is not available or does not exist")

        # 2. Check if patient already has an active assignment
        res = await db.execute(select(BedAssignment).filter(
            BedAssignment.patient_id == assignment.patient_id,
            BedAssignment.status == "active"
        ))
        existing = res.scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Patient already has an active bed assignment")

        # 3. Create assignment
        db_assignment = BedAssignment(**assignment.dict(), status="active")
        db.add(db_assignment)
        
        # 4. Update bed status
        bed.status = "occupied"
        
        await db.commit()
        await db.refresh(db_assignment)
        return db_assignment

    @staticmethod
    async def transfer_bed(db: AsyncSession, transfer: BedTransferCreate):
        # 1. Validate destination bed
        res = await db.execute(select(Bed).filter(Bed.id == transfer.to_bed_id))
        to_bed = res.scalar_one_or_none()
        if not to_bed or to_bed.status != "available":
            raise HTTPException(status_code=400, detail="Destination bed is not available")

        # 2. Get current active assignment
        res = await db.execute(select(BedAssignment).filter(
            BedAssignment.patient_id == transfer.patient_id,
            BedAssignment.encounter_id == transfer.encounter_id,
            BedAssignment.status == "active"
        ))
        active_assignment = res.scalar_one_or_none()
        if not active_assignment:
            raise HTTPException(status_code=400, detail="No active bed assignment found for this patient encounter")

        # 3. Release old bed and create cleaning task
        res = await db.execute(select(Bed).filter(Bed.id == transfer.from_bed_id))
        from_bed = res.scalar_one_or_none()
        if from_bed:
            from_bed.status = "cleaning"
            cleaning_task = BedCleaningTask(bed_id=from_bed.id, cleaning_status="pending")
            db.add(cleaning_task)

        # 4. Close old assignment
        active_assignment.status = "transferred"
        active_assignment.released_at = datetime.now(timezone.utc)

        # 5. Create new assignment
        new_assignment = BedAssignment(
            patient_id=transfer.patient_id,
            encounter_id=transfer.encounter_id,
            bed_id=transfer.to_bed_id,
            assigned_by=transfer.transferred_by,
            status="active"
        )
        db.add(new_assignment)
        to_bed.status = "occupied"

        # 7. Record transfer history
        db_transfer = BedTransfer(**transfer.dict())
        db.add(db_transfer)

        await db.commit()
        return db_transfer

    @staticmethod
    async def release_bed(db: AsyncSession, patient_id: str, encounter_id: str):
        # 1. Get active assignment
        res = await db.execute(select(BedAssignment).filter(
            BedAssignment.patient_id == patient_id,
            BedAssignment.encounter_id == encounter_id,
            BedAssignment.status == "active"
        ))
        active_assignment = res.scalar_one_or_none()
        if not active_assignment:
            return None

        # 2. Close assignment
        active_assignment.status = "discharged"
        active_assignment.released_at = datetime.now(timezone.utc)

        # 3. Mark bed as cleaning
        res = await db.execute(select(Bed).filter(Bed.id == active_assignment.bed_id))
        bed = res.scalar_one_or_none()
        if bed:
            bed.status = "cleaning"
            cleaning_task = BedCleaningTask(bed_id=bed.id, cleaning_status="pending")
            db.add(cleaning_task)

        await db.commit()
        return active_assignment

    @staticmethod
    async def complete_cleaning(db: AsyncSession, bed_id: str, user_id: str):
        # 1. Find pending/in_progress cleaning task
        res = await db.execute(
            select(BedCleaningTask).filter(
                BedCleaningTask.bed_id == bed_id,
                BedCleaningTask.cleaning_status != "completed"
            ).order_by(BedCleaningTask.id.desc())
        )
        task = res.scalar_one_or_none()
        
        if task:
            task.cleaning_status = "completed"
            task.cleaning_completed_at = datetime.now(timezone.utc)
            task.cleaned_by = user_id
        
        # 2. Mark bed as available
        res = await db.execute(select(Bed).filter(Bed.id == bed_id))
        bed = res.scalar_one_or_none()
        if bed:
            bed.status = "available"

        await db.commit()
        return task

    @staticmethod
    async def get_occupancy_stats(db: AsyncSession, org_id: uuid.UUID | None = None):
        base_query = select(func.count(Bed.id))
        if org_id:
            base_query = base_query.where(Bed.org_id == org_id)

        total_beds = await db.scalar(base_query)
        occupied = await db.scalar(base_query.where(Bed.status == "occupied"))
        cleaning = await db.scalar(base_query.where(Bed.status == "cleaning"))
        available = await db.scalar(base_query.where(Bed.status == "available"))
        
        return {
            "total": total_beds or 0,
            "occupied": occupied or 0,
            "cleaning": cleaning or 0,
            "available": available or 0,
            "occupancy_rate": (occupied / total_beds * 100) if total_beds and total_beds > 0 else 0
        }

    @staticmethod
    async def calculate_assignment_duration(db: AsyncSession, assignment_id: str):
        res = await db.execute(select(BedAssignment).filter(BedAssignment.id == assignment_id))
        assignment = res.scalar_one_or_none()
        if not assignment:
            return 0
        
        end_time = assignment.released_at or datetime.now(timezone.utc)
        duration = end_time - assignment.assigned_at
        return duration.total_seconds() / 3600 # returns hours
