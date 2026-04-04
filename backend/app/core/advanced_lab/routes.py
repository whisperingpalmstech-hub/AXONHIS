from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from .schemas import (
    HistoSpecimenOut, AdvanceHistoCommand, HistoSlideOut, AddSlideImageCommand,
    MicroCultureOut, RecordGrowthCommand, AntiSensitivityOut, AddSensitivityCommand,
    CSSDTestOut, RegisterCSSDCommand, ConcludeCSSDCommand,
    BloodBankUnitOut, BloodBankUnitBase
)
from .services import AdvancedLabService

router = APIRouter()

# --- HISTO ---
@router.get("/histo/specimens", response_model=List[HistoSpecimenOut])
async def get_histo_specimens(db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.get_histo(db)

@router.put("/histo/specimens/{spec_id}/advance", response_model=HistoSpecimenOut)
async def advance_histo_specimen(spec_id: str, data: AdvanceHistoCommand, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.advance_histo(db, spec_id, data)

@router.post("/histo/slides/{slide_id}/images", response_model=HistoSlideOut)
async def add_slide_image(slide_id: str, data: AddSlideImageCommand, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.add_slide_image(db, slide_id, data)

# --- MICRO ---
@router.get("/micro/cultures", response_model=List[MicroCultureOut])
async def get_micro_cultures(db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.get_micro(db)

@router.put("/micro/cultures/{cult_id}/growth", response_model=MicroCultureOut)
async def record_growth(cult_id: str, data: RecordGrowthCommand, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.record_growth(db, cult_id, data)

@router.post("/micro/cultures/{cult_id}/sensitivities", response_model=AntiSensitivityOut)
async def add_sensitivity(cult_id: str, data: AddSensitivityCommand, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.add_sensitivity(db, cult_id, data)

# --- CSSD ---
@router.get("/cssd/tests", response_model=List[CSSDTestOut])
async def get_cssd_tests(db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.get_cssd(db)

@router.post("/cssd/tests", response_model=CSSDTestOut)
async def register_cssd(data: RegisterCSSDCommand, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.register_cssd(db, data)

@router.put("/cssd/tests/{test_id}/conclude", response_model=CSSDTestOut)
async def conclude_cssd(test_id: str, data: ConcludeCSSDCommand, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.conclude_cssd(db, test_id, data)

# --- BLOOD BANK ---
@router.get("/blood-bank/inventory", response_model=List[BloodBankUnitOut])
async def get_blood_inventory(db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.get_blood(db)

@router.post("/blood-bank/inventory", response_model=BloodBankUnitOut)
async def register_blood_unit(data: BloodBankUnitBase, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.register_blood(db, data)
