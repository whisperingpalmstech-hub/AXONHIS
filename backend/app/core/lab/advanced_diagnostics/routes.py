from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.database import get_db

from .schemas import (
    HistopathologySpecimenOut, HistoAdvanceStageRequest, AddSlideImageRequest, HistopathologySlideOut,
    MicrobiologyCultureOut, RecordMicrobiologyRequest, AddSensitivityRequest, AntibioticSensitivityOut,
    CSSDSterilityTestOut, RegisterCSSDTestRequest, ConcludeCSSDTestRequest,
    BloodBankInventoryOut, RegisterBloodUnitRequest
)
from .services import AdvancedLabService

router = APIRouter(prefix="/advanced", tags=["Advanced Laboratory Diagnostics"])

# ======================= HISTOPATHOLOGY =========================
@router.get("/histo/specimens", response_model=List[HistopathologySpecimenOut])
async def list_specimens(db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.get_histo_specimens(db)

@router.put("/histo/specimens/{specimen_id}/advance", response_model=HistopathologySpecimenOut)
async def advance_specimen_stage(specimen_id: str, req: HistoAdvanceStageRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AdvancedLabService.advance_histo_stage(db, specimen_id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/histo/slides/{slide_id}/images", response_model=HistopathologySlideOut)
async def attach_slide_image(slide_id: str, req: AddSlideImageRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AdvancedLabService.attach_microscopic_image(db, slide_id, req)
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))

# ======================= MICROBIOLOGY ===========================
@router.get("/micro/cultures", response_model=List[MicrobiologyCultureOut])
async def list_cultures(db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.get_cultures(db)

@router.put("/micro/cultures/{culture_id}/growth", response_model=MicrobiologyCultureOut)
async def record_growth(culture_id: str, req: RecordMicrobiologyRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AdvancedLabService.record_culture_growth(db, culture_id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/micro/cultures/{culture_id}/sensitivities", response_model=AntibioticSensitivityOut)
async def add_culture_sensitivity(culture_id: str, req: AddSensitivityRequest, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.add_antibiotic_sensitivity(db, culture_id, req)

# ======================= CSSD STERILITY =========================
@router.get("/cssd/tests", response_model=List[CSSDSterilityTestOut])
async def list_cssd_tests(db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.get_cssd_tests(db)

@router.post("/cssd/tests", response_model=CSSDSterilityTestOut)
async def register_cssd_test(req: RegisterCSSDTestRequest, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.register_cssd_test(db, req)

@router.put("/cssd/tests/{test_id}/conclude", response_model=CSSDSterilityTestOut)
async def conclude_test(test_id: str, req: ConcludeCSSDTestRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await AdvancedLabService.conclude_cssd_test(db, test_id, req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ========================== BLOOD BANK ==========================
@router.get("/blood-bank/inventory", response_model=List[BloodBankInventoryOut])
async def list_blood_inventory(db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.get_blood_inventory(db)

@router.post("/blood-bank/inventory", response_model=BloodBankInventoryOut)
async def append_blood_inventory(req: RegisterBloodUnitRequest, db: AsyncSession = Depends(get_db)):
    return await AdvancedLabService.register_blood_unit(db, req)
