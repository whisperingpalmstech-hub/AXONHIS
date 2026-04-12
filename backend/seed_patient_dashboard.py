import asyncio
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.core.auth.models import User, Role, UserRole
from app.core.patients.patients.models import Patient
from app.core.patient_portal.appointments.models import PortalAppointment, AppointmentType, AppointmentStatus

async def seed_patient_data():
    async with AsyncSessionLocal() as db:
        # 1. Get or create the test patient
        # Based on user's previous context, email is suj@example.com
        patient_email = "suj@example.com"
        patient = await db.scalar(select(Patient).where(Patient.email == patient_email))
        
        if not patient:
            print(f"Patient {patient_email} not found. Please run seed_account.py first.")
            return

        patient_id = patient.id
        print(f"Seeding data for patient: {patient.first_name} {patient.last_name} ({patient_id})")

        # 2. Get a doctor
        doctor_role = await db.scalar(select(Role).where(Role.name == "doctor"))
        doctor_user_role = await db.scalar(select(UserRole).where(UserRole.role_id == doctor_role.id))
        doctor = await db.scalar(select(User).where(User.id == doctor_user_role.user_id))

        if not doctor:
            print("No doctors found to link appointments to.")
            return

        print(f"Linking to doctor: {doctor.full_name} ({doctor.id})")

        # 3. Create some past and future appointments
        appointments = [
            PortalAppointment(
                patient_id=patient_id,
                doctor_id=doctor.id,
                appointment_time=datetime.now() - timedelta(days=2),
                appointment_type=AppointmentType.IN_PERSON,
                status=AppointmentStatus.COMPLETED,
                reason="Regular Checkup"
            ),
            PortalAppointment(
                patient_id=patient_id,
                doctor_id=doctor.id,
                appointment_time=datetime.now() + timedelta(days=3),
                appointment_type=AppointmentType.TELEMEDICINE,
                status=AppointmentStatus.CONFIRMED,
                reason="Follow-up on results"
            )
        ]

        for apt in appointments:
            db.add(apt)

        # 4. Create some prescriptions (placeholder for now if models exist)
        # Note: I'll check if Prescription model exists in patient portal context
        
        try:
            await db.commit()
            print("Successfully seeded patient data!")
        except Exception as e:
            await db.rollback()
            print(f"Error seeding data: {e}")

if __name__ == "__main__":
    asyncio.run(seed_patient_data())
