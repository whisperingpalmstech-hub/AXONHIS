from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
from typing import List

from app.core.auth.models import User
from app.core.notifications.services import NotificationService

from .models import HistoSpecimen, MicroCulture, CSSDTest, BloodBankUnit, HistoSlide, HistoBlock, AntiSensitivity
from .schemas import AdvanceHistoCommand, AddSlideImageCommand, RegisterCSSDCommand, ConcludeCSSDCommand, RecordGrowthCommand, AddSensitivityCommand, BloodBankUnitBase

class AdvancedLabService:
    # --- HISTO ---
    @staticmethod
    async def get_histo(db: AsyncSession) -> List[HistoSpecimen]:
        result = await db.execute(select(HistoSpecimen).options(joinedload(HistoSpecimen.blocks).joinedload(HistoBlock.slides)))
        records = list(result.unique().scalars().all())
        print(f"DEBUG GET_HISTO CALLED. FOUND {len(records)} RECORDS:", records)
        return records
    
    @staticmethod
    async def advance_histo(db: AsyncSession, spec_id: str, data: AdvanceHistoCommand) -> HistoSpecimen:
        stmt = select(HistoSpecimen).options(joinedload(HistoSpecimen.blocks).joinedload(HistoBlock.slides)).where(HistoSpecimen.id == spec_id)
        res = await db.execute(stmt)
        spec = res.unique().scalars().first()
        if not spec: raise HTTPException(status_code=404, detail="Specimen not found")
        
        spec.current_stage = data.new_stage
        if data.macroscopic_notes:
            spec.macroscopic_notes = data.macroscopic_notes
            
        if data.diagnostic and "malignant" in data.diagnostic.lower():
            spec.is_oncology = True
            spec.is_sensitive = True
            spec.requires_counseling = True
            
        await db.commit()
        
        if getattr(spec, "is_oncology", False):
            sys_admin = (await db.execute(select(User).limit(1))).scalars().first()
            if sys_admin:
                ns = NotificationService(db)
                await ns.send(
                    user_id=sys_admin.id,
                    title="Oncology Alert: Malignancy Detected",
                    message=f"Specimen {spec.sample_id} ({spec.patient_name}) flagged for positive malignancy during {spec.current_stage}.",
                    notification_type="URGENT",
                    link="/dashboard/encounters"
                )
        
        res = await db.execute(select(HistoSpecimen).options(joinedload(HistoSpecimen.blocks).joinedload(HistoBlock.slides)).where(HistoSpecimen.id == spec_id))
        return res.unique().scalars().first()

    @staticmethod
    async def add_slide_image(db: AsyncSession, slide_id: str, data: AddSlideImageCommand) -> HistoSlide:
        res = await db.execute(select(HistoSlide).where(HistoSlide.id == slide_id))
        slide = res.scalars().first()
        if not slide: raise HTTPException(status_code=404)
        
        imgs = list(slide.microscopic_images)
        imgs.append(data.image_url)
        slide.microscopic_images = imgs
        if data.diagnosis:
            slide.microscopic_diagnosis = data.diagnosis
            
        await db.commit()
        await db.refresh(slide)
        return slide

    # --- MICRO ---
    @staticmethod
    async def get_micro(db: AsyncSession) -> List[MicroCulture]:
        result = await db.execute(select(MicroCulture).options(joinedload(MicroCulture.sensitivities)))
        return list(result.unique().scalars().all())
        
    @staticmethod
    async def record_growth(db: AsyncSession, culture_id: str, data: RecordGrowthCommand) -> MicroCulture:
        res = await db.execute(select(MicroCulture).where(MicroCulture.id == culture_id))
        cult = res.scalars().first()
        if not cult: raise HTTPException(status_code=404)
        
        cult.growth_findings = data.growth_findings
        if data.organism_identified:
            cult.organism_identified = data.organism_identified
        
        await db.commit()
        
        if cult.organism_identified:
            sys_admin = (await db.execute(select(User).limit(1))).scalars().first()
            if sys_admin:
                ns = NotificationService(db)
                await ns.send(
                    user_id=sys_admin.id,
                    title="Microbiology: Organism Isolated",
                    message=f"Culture {cult.id} positive for: {cult.organism_identified}. Infection control flag raised.",
                    notification_type="WARNING",
                    link="/dashboard/advanced-lab"
                )
                
        res = await db.execute(select(MicroCulture).options(joinedload(MicroCulture.sensitivities)).where(MicroCulture.id == culture_id))
        return res.unique().scalars().first()
        
    @staticmethod
    async def add_sensitivity(db: AsyncSession, culture_id: str, data: AddSensitivityCommand) -> AntiSensitivity:
        sens = AntiSensitivity(culture_id=culture_id, **data.model_dump())
        db.add(sens)
        await db.commit()
        await db.refresh(sens)
        return sens

    # --- CSSD ---
    @staticmethod
    async def get_cssd(db: AsyncSession) -> List[CSSDTest]:
        res = await db.execute(select(CSSDTest))
        return list(res.scalars().all())
        
    @staticmethod
    async def register_cssd(db: AsyncSession, data: RegisterCSSDCommand) -> CSSDTest:
        t = CSSDTest(**data.model_dump())
        db.add(t)
        await db.commit()
        await db.refresh(t)
        return t
        
    @staticmethod
    async def conclude_cssd(db: AsyncSession, test_id: str, data: ConcludeCSSDCommand) -> CSSDTest:
        res = await db.execute(select(CSSDTest).where(CSSDTest.id == test_id))
        t = res.scalars().first()
        if not t: raise HTTPException(status_code=404)
        
        t.growth_in_test_sample = data.growth_in_test_sample
        t.growth_in_control_sample = data.growth_in_control_sample
        # Validated if NO growth in test (sterile) and YES growth in control (indicator worked)
        t.sterilization_validated = (not data.growth_in_test_sample) and data.growth_in_control_sample
        if data.report_sent_to:
            t.report_sent_to = data.report_sent_to
            
        await db.commit()
        await db.refresh(t)
        
        if t.sterilization_validated:
            sys_admin = (await db.execute(select(User).limit(1))).scalars().first()
            if sys_admin:
                ns = NotificationService(db)
                await ns.send(
                    user_id=sys_admin.id,
                    title="CSSD Sterilization Verified",
                    message=f"Batch {t.test_sample_id} passed sterility. Instruments safely returned to OT Inventory.",
                    notification_type="SUCCESS",
                    link="/dashboard/inventory"
                )
                
        return t

    # --- BLOOD ---
    @staticmethod
    async def get_blood(db: AsyncSession) -> List[BloodBankUnit]:
        res = await db.execute(select(BloodBankUnit))
        return list(res.scalars().all())
        
    @staticmethod
    async def register_blood(db: AsyncSession, data: BloodBankUnitBase) -> BloodBankUnit:
        b = BloodBankUnit(**data.model_dump())
        db.add(b)
        await db.commit()
        await db.refresh(b)
        return b
