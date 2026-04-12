import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.core.advanced_lab.models import HistoSpecimen, HistoBlock, HistoSlide, MicroCulture, AntiSensitivity, CSSDTest, BloodBankUnit
from datetime import datetime, timedelta

async def seed_data():
    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy.future import select
        res = await session.execute(select(HistoSpecimen).limit(1))
        if res.scalars().first():
            print("Advanced Lab already seeded.")
            return

        print("Seeding Advanced Lab...")

        # HIS1
        spec1 = HistoSpecimen(
            sample_id="SMP-772", patient_uhid="UHID-8822", patient_name="Sarah Connors",
            current_stage="Microscopic Examination", is_sensitive=False, requires_counseling=False,
            counseling_status="PENDING", is_oncology=False
        )
        block1 = HistoBlock(block_label="A1", embedding_status="Embedded", specimen=spec1)
        slide1 = HistoSlide(slide_label="A1-H&E", staining_type="H&E", microscopic_images=["/dicom_mock.jpg"], block=block1)

        # HIS2
        spec2 = HistoSpecimen(
            sample_id="SMP-775", patient_uhid="UHID-1100", patient_name="John Miller",
            current_stage="Block Creation", is_sensitive=True, requires_counseling=True,
            counseling_status="PENDING", is_oncology=True
        )

        session.add_all([spec1, spec2])

        # MICRO
        cult = MicroCulture(
            sample_id="SMP-881", patient_uhid="UHID-1100", source_department="Ward B",
            incubation_type="Aerobic", organism_identified="MRSA", is_infection_control_screen=False
        )
        sens1 = AntiSensitivity(antibiotic_name="Vancomycin", mic_value=1.5, susceptibility="Sensitive", culture=cult)
        sens2 = AntiSensitivity(antibiotic_name="Penicillin", mic_value=32.0, susceptibility="Resistant", culture=cult)
        session.add(cult)

        # CSSD
        cssd = CSSDTest(
            test_sample_id="OT1-INSTR-99", control_sample_id="CTRL-V1",
            sterilization_validated=True, growth_in_test_sample=False, growth_in_control_sample=True
        )
        session.add(cssd)

        # BLOOD
        blood = BloodBankUnit(
            unit_id="DON-209", blood_group="O+", collection_date=datetime.utcnow(),
            expiry_date=datetime.utcnow() + timedelta(days=30), component_type="PRBC", status="Available"
        )
        session.add(blood)

        await session.commit()
        print("Advanced Lab seeded successfully.")

if __name__ == "__main__":
    asyncio.run(seed_data())
