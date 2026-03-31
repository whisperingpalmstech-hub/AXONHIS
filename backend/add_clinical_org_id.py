import asyncio
from app.database import engine
from sqlalchemy import text

async def run():
    tables = [
        "ipd_admission_requests",
        "ipd_admission_records",
        "ipd_admission_audit_logs",
        "ipd_admission_checklists",
        "lab_tests",
        "lab_orders",
        "lab_samples",
        "lab_processing",
        "lab_results",
        "lab_validations",
        "doctor_worklist",
        "doctor_consultation_notes",
        "doctor_clinical_templates",
        "doctor_prescriptions",
        "doctor_diagnostic_orders",
        "rcm_billing_services",
        "rcm_billing_payments",
        "rcm_billing_discounts",
        "rcm_billing_refunds",
        "rcm_billing_payers",
        "pharmacy_sales_worklist",
        "pharmacy_worklist_prescriptions",
        "pharmacy_dispensing_records",
        "encounters"
    ]
    
    async with engine.begin() as conn:
        for table in tables:
            try:
                await conn.execute(text(f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS org_id UUID'))
                await conn.execute(text(f'CREATE INDEX IF NOT EXISTS idx_{table}_org_id ON "{table}" (org_id)'))
                print(f"Added org_id to {table}")
            except Exception as e:
                print(f"Error on {table}: {e}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
