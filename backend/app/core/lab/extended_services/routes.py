from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from .schemas import (
    HomeCollectionCreate, HomeCollectionOut, PhlebotomistScheduleCreate, PhlebotomistScheduleOut,
    OutsourceLabCreate, OutsourceLabOut,
    ExternalResultCreate, ExternalResultOut, QualityControlCreate, QualityControlOut,
    EquipmentMaintenanceCreate, EquipmentMaintenanceOut
)
from .services import ExtendedLabService

router = APIRouter(prefix="/extended", tags=["LIS Extended Services & Quality Management"])

# --- Home Collections ---
@router.post("/home-collections", response_model=HomeCollectionOut)
async def request_home_collection(req: HomeCollectionCreate, db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.create_home_request(db, req)

@router.get("/home-collections", response_model=List[HomeCollectionOut])
async def list_collections(db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.get_home_collections(db)

@router.post("/home-collections/schedule", response_model=PhlebotomistScheduleOut)
async def schedule_phlebotomist(sched: PhlebotomistScheduleCreate, db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.schedule_phlebotomist(db, sched)

# Sample Transport is managed by Phlebotomy Engine (/api/v1/phlebotomy/transport)

# --- Outsource Management ---
@router.post("/outsource-labs", response_model=OutsourceLabOut)
async def register_outsource_lab(lab: OutsourceLabCreate, db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.register_outsource_lab(db, lab)

@router.get("/outsource-labs", response_model=List[OutsourceLabOut])
async def list_outsource_labs(db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.get_outsource_labs(db)

@router.post("/outsource-results", response_model=ExternalResultOut)
async def import_external_result(res: ExternalResultCreate, db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.import_external_result(db, res)

# --- Quality Control ---
@router.post("/quality-controls", response_model=QualityControlOut)
async def record_qc(qc: QualityControlCreate, db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.record_qc(db, qc)

@router.get("/quality-controls", response_model=List[QualityControlOut])
async def list_qcs(db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.get_qcs(db)

# --- Equipment Maintenance ---
@router.post("/equipment-maintenance", response_model=EquipmentMaintenanceOut)
async def add_equipment(eq: EquipmentMaintenanceCreate, db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.register_equipment(db, eq)

@router.get("/equipment-maintenance", response_model=List[EquipmentMaintenanceOut])
async def list_equipment(db: AsyncSession = Depends(get_db)):
    return await ExtendedLabService.get_equipment(db)
