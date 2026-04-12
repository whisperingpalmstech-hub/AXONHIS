import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.database import engine

from app.core.analytics.clinical_metrics.services import ClinicalMetricService
from app.core.analytics.financial_metrics.services import FinancialMetricService
from app.core.analytics.operational_metrics.services import OperationalMetricService
from app.core.analytics.predictive_models.services import PredictiveModelService

# Import models to ensure relationship names resolve during Service initialization
from app.core.auth.models import User, Role, Permission, RolePermission, UserRole, DeviceSession
from app.core.patients.patients.models import Patient
from app.core.patients.identifiers.models import PatientIdentifier
from app.core.patients.contacts.models import PatientContact
from app.core.patients.guardians.models import PatientGuardian
from app.core.patients.insurance.models import PatientInsurance
from app.core.patients.consents.models import PatientConsent
from app.core.patients.appointments.models import Appointment
from app.core.encounters.encounters.models import Encounter
from app.core.encounters.diagnoses.models import EncounterDiagnosis
from app.core.encounters.notes.models import EncounterNote
from app.core.encounters.timeline.models import EncounterTimeline
from app.core.encounters.clinical_flags.models import ClinicalFlag
from app.core.orders.models import Order, OrderItem
from app.core.tasks.models import Task
from app.core.billing.invoices.models import Invoice
from app.core.billing.insurance.models import InsuranceProvider, InsurancePolicy, InsuranceClaim

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

async def main():
    print("Clearing mock analytics data...")
    async with AsyncSessionLocal() as db:
        await db.execute(text("TRUNCATE TABLE analytics_predictive_models RESTART IDENTITY CASCADE;"))
        await db.execute(text("TRUNCATE TABLE analytics_clinical_metrics RESTART IDENTITY CASCADE;"))
        await db.execute(text("TRUNCATE TABLE analytics_financial_metrics RESTART IDENTITY CASCADE;"))
        await db.execute(text("TRUNCATE TABLE analytics_operational_metrics RESTART IDENTITY CASCADE;"))
        await db.commit()
    
    print("Re-aggregating with live DB data...")
    async with AsyncSessionLocal() as db:
        cs = ClinicalMetricService(db)
        fs = FinancialMetricService(db)
        os = OperationalMetricService(db)
        ps = PredictiveModelService(db)

        await cs.aggregate_daily()
        await fs.aggregate_daily()
        await os.aggregate_daily()
        await ps.generate_forecasts()

    print("Done! Real data synced.")

if __name__ == "__main__":
    asyncio.run(main())
