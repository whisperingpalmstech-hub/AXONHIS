from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import List, Optional

from .models import (
    HistopathologySpecimen, HistopathologyBlock, HistopathologySlide,
    MicrobiologyCulture, AntibioticSensitivity, CSSDSterilityTest, BloodBankInventory
)
from .schemas import (
    HistoAdvanceStageRequest, AddSlideImageRequest, RecordMicrobiologyRequest,
    AddSensitivityRequest, RegisterCSSDTestRequest, ConcludeCSSDTestRequest, RegisterBloodUnitRequest
)

class AdvancedLabService:
    # --- HISTOPATHOLOGY ---
    @staticmethod
    async def get_histo_specimens(db: AsyncSession) -> List[HistopathologySpecimen]:
        q = select(HistopathologySpecimen).options(
            selectinload(HistopathologySpecimen.blocks).selectinload(HistopathologyBlock.slides)
        )
        res = await db.execute(q)
        return res.scalars().all()

    @staticmethod
    async def advance_histo_stage(db: AsyncSession, specimen_id: str, req: HistoAdvanceStageRequest) -> HistopathologySpecimen:
        q = select(HistopathologySpecimen).where(HistopathologySpecimen.id == specimen_id).options(
            selectinload(HistopathologySpecimen.blocks).selectinload(HistopathologyBlock.slides)
        )
        spec = (await db.execute(q)).scalars().first()
        if not spec: raise ValueError("Specimen not found")
        
        spec.current_stage = req.new_stage
        if req.macroscopic_notes:
            spec.macroscopic_notes = req.macroscopic_notes

        # Automatic cross-referral & counseling check: if Diagnosis includes Cancer/Malignancy
        if "Diagnosis" in req.new_stage and req.macroscopic_notes and ("malignant" in req.macroscopic_notes.lower() or "carcinoma" in req.macroscopic_notes.lower()):
            spec.is_oncology = True
            spec.is_sensitive = True
            spec.requires_counseling = True
            spec.counseling_status = "PENDING"
            spec.cross_referral_sent = True # Auto-refer to oncology ward
            
        await db.commit()
        await db.refresh(spec)
        return spec

    @staticmethod
    async def create_block_and_slide(db: AsyncSession, specimen_id: str, block_label: str, slide_label: str) -> HistopathologyBlock:
        block = HistopathologyBlock(specimen_id=specimen_id, block_label=block_label)
        db.add(block)
        await db.flush() # get ID
        
        slide = HistopathologySlide(block_id=block.id, slide_label=slide_label)
        db.add(slide)
        await db.commit()
        await db.refresh(block)
        return block

    @staticmethod
    async def attach_microscopic_image(db: AsyncSession, slide_id: str, req: AddSlideImageRequest) -> HistopathologySlide:
        q = select(HistopathologySlide).where(HistopathologySlide.id == slide_id)
        slide = (await db.execute(q)).scalars().first()
        if not slide: raise ValueError("Slide not found")
        
        # appending to JSON list
        current_images = list(slide.microscopic_images) if slide.microscopic_images else []
        current_images.append(req.image_url)
        slide.microscopic_images = current_images
        
        if req.diagnosis:
            slide.microscopic_diagnosis = req.diagnosis
            
        await db.commit()
        await db.refresh(slide)
        return slide

    # --- MICROBIOLOGY & SENSITIVITY ---
    @staticmethod
    async def get_cultures(db: AsyncSession) -> List[MicrobiologyCulture]:
        q = select(MicrobiologyCulture).options(selectinload(MicrobiologyCulture.sensitivities))
        res = await db.execute(q)
        return res.scalars().all()

    @staticmethod
    async def record_culture_growth(db: AsyncSession, culture_id: str, req: RecordMicrobiologyRequest) -> MicrobiologyCulture:
        q = select(MicrobiologyCulture).where(MicrobiologyCulture.id == culture_id).options(selectinload(MicrobiologyCulture.sensitivities))
        culture = (await db.execute(q)).scalars().first()
        if not culture: raise ValueError("Culture not found")
        
        culture.growth_findings = req.growth_findings
        culture.organism_identified = req.organism_identified
        
        await db.commit()
        await db.refresh(culture)
        return culture

    @staticmethod
    async def add_antibiotic_sensitivity(db: AsyncSession, culture_id: str, req: AddSensitivityRequest) -> AntibioticSensitivity:
        sens = AntibioticSensitivity(
            culture_id=culture_id,
            antibiotic_name=req.antibiotic_name,
            mic_value=req.mic_value,
            susceptibility=req.susceptibility
        )
        db.add(sens)
        await db.commit()
        await db.refresh(sens)
        return sens

    # --- CSSD INFECTION CONTROL ---
    @staticmethod
    async def get_cssd_tests(db: AsyncSession) -> List[CSSDSterilityTest]:
        res = await db.execute(select(CSSDSterilityTest))
        return res.scalars().all()

    @staticmethod
    async def register_cssd_test(db: AsyncSession, req: RegisterCSSDTestRequest) -> CSSDSterilityTest:
        t = CSSDSterilityTest(test_sample_id=req.test_sample_id, control_sample_id=req.control_sample_id)
        db.add(t)
        await db.commit()
        await db.refresh(t)
        return t

    @staticmethod
    async def conclude_cssd_test(db: AsyncSession, test_id: str, req: ConcludeCSSDTestRequest) -> CSSDSterilityTest:
        t = (await db.execute(select(CSSDSterilityTest).where(CSSDSterilityTest.id == test_id))).scalars().first()
        if not t: raise ValueError("Test not found")
        
        t.growth_in_test_sample = req.growth_in_test_sample
        t.growth_in_control_sample = req.growth_in_control_sample
        t.report_sent_to = req.report_sent_to
        
        # Validated if control grows (medium viable) AND test doesn't grow (sterilized perfectly)
        t.sterilization_validated = (req.growth_in_control_sample and not req.growth_in_test_sample)
        
        await db.commit()
        await db.refresh(t)
        return t

    # --- BLOOD BANK ---
    @staticmethod
    async def get_blood_inventory(db: AsyncSession) -> List[BloodBankInventory]:
        res = await db.execute(select(BloodBankInventory))
        return res.scalars().all()

    @staticmethod
    async def register_blood_unit(db: AsyncSession, req: RegisterBloodUnitRequest) -> BloodBankInventory:
        unit = BloodBankInventory(
            unit_id=req.unit_id,
            blood_group=req.blood_group,
            donor_id=req.donor_id,
            donor_email=req.donor_email,
            collection_date=req.collection_date.replace(tzinfo=None),
            expiry_date=req.expiry_date.replace(tzinfo=None),
            component_type=req.component_type,
            status="Available"
        )
        db.add(unit)
        await db.commit()
        await db.refresh(unit)
        return unit
