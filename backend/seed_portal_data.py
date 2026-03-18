import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from app.database import AsyncSessionLocal
from app.core.patients.patients.models import Patient
from app.core.patients.identifiers.models import PatientIdentifier
from app.core.patients.contacts.models import PatientContact
from app.core.patients.guardians.models import PatientGuardian
from app.core.patients.insurance.models import PatientInsurance
from app.core.patients.consents.models import PatientConsent
from app.core.patients.appointments.models import Appointment # Clinical appointment model
from app.core.lab.models import LabResult, LabSample, LabTest
from app.core.pharmacy.prescriptions.models import Prescription, PrescriptionItem
from app.core.pharmacy.medications.models import Medication
from app.core.encounters.models import Encounter, EncounterType, EncounterStatus
from app.core.patient_portal.appointments.models import PortalAppointment, AppointmentStatus
from app.core.auth.models import User, Role, UserRole
from sqlalchemy import select

PATIENT_ID = uuid.UUID("47b82a31-0bcb-4df1-9317-e20954e6e870")
DOCTOR_ID = uuid.UUID("a79c6cd7-dc15-47c7-a2b6-f3cb61a4df14") 

async def seed_data():
    async with AsyncSessionLocal() as db:
        # 1. Ensure Medication exists
        med_query = select(Medication).where(Medication.drug_name == "Amoxicillin")
        med = (await db.execute(med_query)).scalar_one_or_none()
        if not med:
            med = Medication(
                drug_code="AMOX500",
                drug_name="Amoxicillin",
                generic_name="Amoxicillin",
                form="Capsule",
                strength="500mg"
            )
            db.add(med)
            await db.flush()

        # 2. Create Encounter (Required for Prescription)
        encounter = Encounter(
            patient_id=PATIENT_ID,
            doctor_id=DOCTOR_ID,
            encounter_type=EncounterType.OPD,
            status=EncounterStatus.ACTIVE,
            chief_complaint="Fever and cough"
        )
        db.add(encounter)
        await db.flush()

        # 3. Seed Lab Result
        lab_result = LabResult(
            patient_id=PATIENT_ID,
            value="14.2",
            unit="g/dL",
            reference_range="13.5-17.5",
            status="final",
            entered_at=datetime.now(timezone.utc) - timedelta(days=2)
        )
        db.add(lab_result)

        # 4. Seed Prescription
        prescription = Prescription(
            patient_id=PATIENT_ID,
            prescribing_doctor_id=DOCTOR_ID,
            encounter_id=encounter.id,
            status="active",
            prescription_time=datetime.now(timezone.utc) - timedelta(days=5)
        )
        db.add(prescription)
        await db.flush()

        item = PrescriptionItem(
            prescription_id=prescription.id,
            drug_id=med.id,
            dosage="500mg",
            frequency="TID",
            duration="7 days"
        )
        db.add(item)

        # 5. Seed Portal Appointment
        apt = PortalAppointment(
            patient_id=PATIENT_ID,
            doctor_id=DOCTOR_ID,
            department="General Medicine",
            appointment_time=datetime.now(timezone.utc) + timedelta(days=1),
            status=AppointmentStatus.CONFIRMED.value
        )
        db.add(apt)

        await db.commit()
        print("Successfully seeded all clinical and portal data for Patient Suj Gaik!")

if __name__ == "__main__":
    asyncio.run(seed_data())
