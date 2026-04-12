"""
AxonHIS MD – Database Table Creation Script.

Run this script to create all md_* tables in the PostgreSQL database.
Usage:
    python -m app.core.axonhis_md.create_tables
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../.."))

from app.database import engine, Base
from app.core.axonhis_md.models import (
    MdOrganization, MdFacility, MdSpecialtyProfile, MdClinician,
    MdPatient, MdPatientIdentifier, MdConsentProfile, MdChannel,
    MdAppointment, MdEncounter, MdEncounterNote, MdDiagnosis,
    MdServiceRequest, MdMedicationRequest, MdDevice, MdDeviceResult,
    MdObservation, MdDocument, MdShareGrant, MdShareAccessLog,
    MdPayer, MdCoverage, MdBillingInvoice, MdBillingLineItem,
    MdIntegrationEvent, MdAuditEvent,
)


async def create_tables():
    async with engine.begin() as conn:
        # Create only md_* tables (won't affect existing tables)
        tables = [
            MdOrganization.__table__, MdFacility.__table__,
            MdSpecialtyProfile.__table__, MdClinician.__table__,
            MdPatient.__table__, MdPatientIdentifier.__table__,
            MdConsentProfile.__table__, MdChannel.__table__,
            MdAppointment.__table__, MdEncounter.__table__,
            MdEncounterNote.__table__, MdDiagnosis.__table__,
            MdServiceRequest.__table__, MdMedicationRequest.__table__,
            MdDevice.__table__, MdDeviceResult.__table__,
            MdObservation.__table__, MdDocument.__table__,
            MdShareGrant.__table__, MdShareAccessLog.__table__,
            MdPayer.__table__, MdCoverage.__table__,
            MdBillingInvoice.__table__, MdBillingLineItem.__table__,
            MdIntegrationEvent.__table__, MdAuditEvent.__table__,
        ]
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
    print("✅ All AxonHIS MD tables created successfully")


async def seed_demo_data():
    """Seed demo specialty profiles, organization, and channels."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Check if demo org already exists
        existing = (await db.execute(
            select(MdOrganization).where(MdOrganization.code == "AXON-MD-DEMO")
        )).scalars().first()
        if existing:
            print("ℹ️  Demo data already exists, skipping seed")
            return

        # Create demo organization
        org = MdOrganization(code="AXON-MD-DEMO", name="AxonHIS MD Demo Clinic", organization_type="CLINIC")
        db.add(org)
        await db.flush()

        # Create facilities
        fac1 = MdFacility(organization_id=org.organization_id, code="FAC-MAIN", name="Main Clinic", facility_type="CLINIC", timezone="UTC")
        fac2 = MdFacility(organization_id=org.organization_id, code="FAC-ATM", name="Health ATM Kiosk", facility_type="HEALTH_ATM", timezone="UTC")
        db.add_all([fac1, fac2])
        await db.flush()

        # Create specialty profiles
        specialties = [
            MdSpecialtyProfile(code="GENERAL_PRACTICE", name="General Practice", description="Primary care and general medicine"),
            MdSpecialtyProfile(code="DERMATOLOGY", name="Dermatology", description="Skin, hair, and nail conditions"),
            MdSpecialtyProfile(code="CARDIOLOGY", name="Cardiology", description="Heart and cardiovascular system"),
            MdSpecialtyProfile(code="ORTHOPEDICS", name="Orthopedics", description="Musculoskeletal system"),
            MdSpecialtyProfile(code="PEDIATRICS", name="Pediatrics", description="Children and adolescent health"),
            MdSpecialtyProfile(code="OPHTHALMOLOGY", name="Ophthalmology", description="Eye care and vision"),
            MdSpecialtyProfile(code="ENT", name="ENT", description="Ear, nose, and throat"),
            MdSpecialtyProfile(code="PSYCHIATRY", name="Psychiatry", description="Mental health and behavioral medicine"),
        ]
        db.add_all(specialties)
        await db.flush()

        # Create channels
        channels = [
            MdChannel(organization_id=org.organization_id, code="CLINIC-WALK-IN", name="Walk-in Clinic", channel_type="CLINIC"),
            MdChannel(organization_id=org.organization_id, code="TELECONSULT", name="Teleconsult", channel_type="TELECONSULT"),
            MdChannel(organization_id=org.organization_id, code="HEALTH-ATM-1", name="Health ATM Kiosk", channel_type="HEALTH_ATM"),
            MdChannel(organization_id=org.organization_id, code="HYBRID-CARE", name="Hybrid Care", channel_type="HYBRID"),
        ]
        db.add_all(channels)

        # Create demo clinicians
        clinicians = [
            MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, specialty_profile_id=specialties[0].specialty_profile_id, code="DR001", display_name="Dr. Sarah Ahmed", mobile_number="+971501234567", email="sarah.ahmed@axonmd.com", clinician_type="DOCTOR"),
            MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, specialty_profile_id=specialties[1].specialty_profile_id, code="DR002", display_name="Dr. Mohammed Ali", mobile_number="+971502345678", email="mohammed.ali@axonmd.com", clinician_type="DOCTOR"),
            MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, specialty_profile_id=specialties[2].specialty_profile_id, code="DR003", display_name="Dr. Fatima Khan", mobile_number="+971503456789", email="fatima.khan@axonmd.com", clinician_type="DOCTOR"),
            MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, code="NR001", display_name="Nurse Aisha Patel", mobile_number="+971504567890", email="aisha.patel@axonmd.com", clinician_type="NURSE"),
            MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, code="TECH001", display_name="Tech. Omar Hassan", mobile_number="+971505678901", email="omar.hassan@axonmd.com", clinician_type="TECHNICIAN"),
        ]
        db.add_all(clinicians)

        # Create demo payers
        payers = [
            MdPayer(organization_id=org.organization_id, payer_code="INS-DAMAN", payer_name="Daman Health Insurance", payer_type="INSURANCE"),
            MdPayer(organization_id=org.organization_id, payer_code="SELF-PAY", payer_name="Self Pay", payer_type="SELF"),
            MdPayer(organization_id=org.organization_id, payer_code="INS-OMAN", payer_name="Oman Insurance", payer_type="INSURANCE"),
        ]
        db.add_all(payers)

        # Create demo devices
        devices = [
            MdDevice(organization_id=org.organization_id, facility_id=fac1.facility_id, device_code="BP-MONITOR-01", device_name="Digital BP Monitor", device_class="VITAL_SIGNS", manufacturer="Omron", integration_method="USB"),
            MdDevice(organization_id=org.organization_id, facility_id=fac1.facility_id, device_code="PULSE-OX-01", device_name="Pulse Oximeter", device_class="VITAL_SIGNS", manufacturer="Masimo", integration_method="BLUETOOTH"),
            MdDevice(organization_id=org.organization_id, facility_id=fac1.facility_id, device_code="ECG-01", device_name="12-Lead ECG", device_class="CARDIAC", manufacturer="GE Healthcare", integration_method="NETWORK"),
            MdDevice(organization_id=org.organization_id, facility_id=fac2.facility_id, device_code="ATM-KIOSK-01", device_name="Health ATM Terminal", device_class="KIOSK", manufacturer="AxonHIS", integration_method="NETWORK"),
        ]
        db.add_all(devices)

        await db.commit()
        print("✅ Demo data seeded successfully")


async def main():
    await create_tables()
    # Create a fresh engine for seeding
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    import os

    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        from app.database import engine as _eng
        db_url = str(_eng.url)

    seed_engine = create_async_engine(db_url, echo=False)
    SeedSession = sessionmaker(seed_engine, class_=AsyncSession, expire_on_commit=False)

    async with SeedSession() as db:
        try:
            existing = (await db.execute(
                select(MdOrganization).where(MdOrganization.code == "AXON-MD-DEMO")
            )).scalars().first()
            if existing:
                print("ℹ️  Demo data already exists, skipping seed")
                await seed_engine.dispose()
                return

            org = MdOrganization(code="AXON-MD-DEMO", name="AxonHIS MD Demo Clinic", organization_type="CLINIC")
            db.add(org)
            await db.flush()

            fac1 = MdFacility(organization_id=org.organization_id, code="FAC-MAIN", name="Main Clinic", facility_type="CLINIC", timezone="UTC")
            fac2 = MdFacility(organization_id=org.organization_id, code="FAC-ATM", name="Health ATM Kiosk", facility_type="HEALTH_ATM", timezone="UTC")
            db.add_all([fac1, fac2])
            await db.flush()

            specialties = [
                MdSpecialtyProfile(code="GENERAL_PRACTICE", name="General Practice", description="Primary care and general medicine"),
                MdSpecialtyProfile(code="DERMATOLOGY", name="Dermatology", description="Skin, hair, and nail conditions"),
                MdSpecialtyProfile(code="CARDIOLOGY", name="Cardiology", description="Heart and cardiovascular system"),
                MdSpecialtyProfile(code="ORTHOPEDICS", name="Orthopedics", description="Musculoskeletal system"),
                MdSpecialtyProfile(code="PEDIATRICS", name="Pediatrics", description="Children and adolescent health"),
                MdSpecialtyProfile(code="OPHTHALMOLOGY", name="Ophthalmology", description="Eye care and vision"),
                MdSpecialtyProfile(code="ENT", name="ENT", description="Ear, nose, and throat"),
                MdSpecialtyProfile(code="PSYCHIATRY", name="Psychiatry", description="Mental health and behavioral medicine"),
            ]
            db.add_all(specialties)
            await db.flush()

            channels = [
                MdChannel(organization_id=org.organization_id, code="CLINIC-WALK-IN", name="Walk-in Clinic", channel_type="CLINIC"),
                MdChannel(organization_id=org.organization_id, code="TELECONSULT", name="Teleconsult", channel_type="TELECONSULT"),
                MdChannel(organization_id=org.organization_id, code="HEALTH-ATM-1", name="Health ATM Kiosk", channel_type="HEALTH_ATM"),
                MdChannel(organization_id=org.organization_id, code="HYBRID-CARE", name="Hybrid Care", channel_type="HYBRID"),
            ]
            db.add_all(channels)

            clinicians = [
                MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, specialty_profile_id=specialties[0].specialty_profile_id, code="DR001", display_name="Dr. Sarah Ahmed", mobile_number="+971501234567", email="sarah.ahmed@axonmd.com", clinician_type="DOCTOR"),
                MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, specialty_profile_id=specialties[1].specialty_profile_id, code="DR002", display_name="Dr. Mohammed Ali", mobile_number="+971502345678", email="mohammed.ali@axonmd.com", clinician_type="DOCTOR"),
                MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, specialty_profile_id=specialties[2].specialty_profile_id, code="DR003", display_name="Dr. Fatima Khan", mobile_number="+971503456789", email="fatima.khan@axonmd.com", clinician_type="DOCTOR"),
                MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, code="NR001", display_name="Nurse Aisha Patel", mobile_number="+971504567890", email="aisha.patel@axonmd.com", clinician_type="NURSE"),
                MdClinician(organization_id=org.organization_id, facility_id=fac1.facility_id, code="TECH001", display_name="Tech. Omar Hassan", mobile_number="+971505678901", email="omar.hassan@axonmd.com", clinician_type="TECHNICIAN"),
            ]
            db.add_all(clinicians)

            payers = [
                MdPayer(organization_id=org.organization_id, payer_code="INS-DAMAN", payer_name="Daman Health Insurance", payer_type="INSURANCE"),
                MdPayer(organization_id=org.organization_id, payer_code="SELF-PAY", payer_name="Self Pay", payer_type="SELF"),
                MdPayer(organization_id=org.organization_id, payer_code="INS-OMAN", payer_name="Oman Insurance", payer_type="INSURANCE"),
            ]
            db.add_all(payers)

            devices = [
                MdDevice(organization_id=org.organization_id, facility_id=fac1.facility_id, device_code="BP-MONITOR-01", device_name="Digital BP Monitor", device_class="VITAL_SIGNS", manufacturer="Omron", integration_method="USB"),
                MdDevice(organization_id=org.organization_id, facility_id=fac1.facility_id, device_code="PULSE-OX-01", device_name="Pulse Oximeter", device_class="VITAL_SIGNS", manufacturer="Masimo", integration_method="BLUETOOTH"),
                MdDevice(organization_id=org.organization_id, facility_id=fac1.facility_id, device_code="ECG-01", device_name="12-Lead ECG", device_class="CARDIAC", manufacturer="GE Healthcare", integration_method="NETWORK"),
                MdDevice(organization_id=org.organization_id, facility_id=fac2.facility_id, device_code="ATM-KIOSK-01", device_name="Health ATM Terminal", device_class="KIOSK", manufacturer="AxonHIS", integration_method="NETWORK"),
            ]
            db.add_all(devices)

            await db.commit()
            print("✅ Demo data seeded successfully")
        except Exception as e:
            print(f"❌ Seed error: {e}")
            await db.rollback()
        finally:
            await seed_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
