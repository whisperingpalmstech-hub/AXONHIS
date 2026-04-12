import asyncio
import sys
from sqlalchemy import text
from app.database import engine, Base
from app.core.doctor_desk.models import (
    DoctorWorklist, ClinicalComplaint, PatientMedicalHistory, 
    ExaminationRecord, DiagnosisRecord, EMRConsultationVitals
)

async def main():
    try:
        async with engine.begin() as conn:
            # We already changed DoctorWorklist to add encounter_type. Let's just alter it directly using raw SQL
            tables_to_create = [
                Base.metadata.tables['doctor_clinical_complaints'],
                Base.metadata.tables['doctor_patient_medical_history'],
                Base.metadata.tables['doctor_examination_records'],
                Base.metadata.tables['doctor_diagnosis_records'],
                Base.metadata.tables['doctor_consultation_vitals']
            ]
            
            try:
                await conn.execute(text("ALTER TABLE doctor_worklist ADD COLUMN encounter_type VARCHAR(50) DEFAULT 'opd';"))
                print("Added encounter_type to doctor_worklist")
            except Exception as e:
                print(f"Skipped altering doctor_worklist: {e}")
            
            await conn.run_sync(Base.metadata.create_all, tables=tables_to_create)
            print("Created new EMR tables successfully.")
    except Exception as e:
        print("Root error:", e)

if __name__ == "__main__":
    asyncio.run(main())
