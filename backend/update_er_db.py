import asyncio
import sys
from sqlalchemy import text
from app.database import engine, Base
# Import all ER models to ensure they are registered in Base
from app.core.er.models import EREncounter, ERTriage, ERBed, ERMlcCase, ERNursingScore, EROrder, ERDischarge, ERClinicalNote, ERDiagnosis

async def main():
    try:
        async with engine.begin() as conn:
            # Drop org_id constraints
            tables = ['er_encounters', 'er_triage', 'er_beds', 'er_mlc_cases', 'er_nursing_scores', 'er_orders']
            for t in tables:
                try:
                    await conn.execute(text(f"ALTER TABLE {t} ALTER COLUMN org_id DROP NOT NULL;"))
                    print(f"Altered {t}")
                except Exception as e:
                    print(f"Skipped altering {t}: {e}")
            
            # Create new tables
            await conn.run_sync(Base.metadata.create_all, tables=[
                Base.metadata.tables['er_discharges'],
                Base.metadata.tables['er_clinical_notes'],
                Base.metadata.tables['er_diagnoses']
            ])
            print("Created new ER tables successfully.")
    except Exception as e:
        print("Root error:", e)

if __name__ == "__main__":
    asyncio.run(main())
