import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.core.diagnostics.models import (
    DiagnosticTemplate,
    DiagnosticProcedureOrder,
    DiagnosticWorkbenchRecord
)

async def seed_data():
    async with AsyncSessionLocal() as db:
        # Check if templates exist
        import sqlalchemy as sa
        res = await db.execute(sa.select(sa.func.count(DiagnosticTemplate.id)))
        if res.scalar() == 0:
            print("Seeding Diagnostic Templates...")
            t1 = DiagnosticTemplate(
                id="template-2dECHO-123",
                procedure_name="2D ECHO",
                department="Cardiology",
                structured_fields_schema={"LV_Function": "string", "EF_percent": "number"},
                rich_text_layout="<p>2D ECHO Findings</p>"
            )
            t2 = DiagnosticTemplate(
                id="template-ECG-123",
                procedure_name="Electrocardiogram (ECG)",
                department="Cardiology",
                structured_fields_schema={"Rhythm": "string", "Rate": "number"},
                rich_text_layout="<p>ECG Findings</p>"
            )
            db.add_all([t1, t2])
            await db.commit()
            
            # Create a mock order so UI has something to show
            order = DiagnosticProcedureOrder(
                id="ord-diag-111",
                patient_id="patient-1",
                uhid="DH123456",
                encounter_id="opd-enc-1",
                encounter_type="OPD",
                template_id=t1.id,
                ordering_doctor_id="dr-john",
                clinical_notes="Patient complains of chest pain."
            )
            db.add(order)
            
            wb = DiagnosticWorkbenchRecord(
                id="wb-111",
                order_id=order.id,
                workflow_state="PENDING_ACCEPTANCE"
            )
            db.add(wb)
            await db.commit()
            print("Diagnostic Data Seeded!")
        else:
            print("Diagnostic Data already exists.")

if __name__ == "__main__":
    asyncio.run(seed_data())
