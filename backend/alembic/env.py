"""Alembic env.py – async migration runner."""
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.config import settings
from app.database import Base

# Import ALL models so Alembic sees them for autogenerate

# Phase 1 – Core Platform
from app.core.auth.models import User, Role, Permission, RolePermission, UserRole, DeviceSession  # noqa: F401
from app.core.events.models import Event  # noqa: F401
from app.core.audit.models import AuditLog  # noqa: F401
from app.core.files.models import File  # noqa: F401
from app.core.notifications.models import Notification  # noqa: F401
from app.core.config.models import Configuration  # noqa: F401

# Phase 2+ – Clinical
from app.core.patients.patients.models import Patient  # noqa: F401
from app.core.patients.identifiers.models import PatientIdentifier  # noqa: F401
from app.core.patients.contacts.models import PatientContact  # noqa: F401
from app.core.patients.guardians.models import PatientGuardian  # noqa: F401
from app.core.patients.insurance.models import PatientInsurance  # noqa: F401
from app.core.patients.consents.models import PatientConsent  # noqa: F401
from app.core.patients.appointments.models import Appointment  # noqa: F401
from app.core.encounters.encounters.models import Encounter  # noqa: F401
from app.core.encounters.diagnoses.models import EncounterDiagnosis  # noqa: F401
from app.core.encounters.notes.models import EncounterNote  # noqa: F401
from app.core.encounters.timeline.models import EncounterTimeline  # noqa: F401
from app.core.encounters.clinical_flags.models import ClinicalFlag  # noqa: F401
from app.core.orders.models import Order, OrderItem  # noqa: F401
from app.core.tasks.models import Task  # noqa: F401
from app.core.billing.services.models import BillingService  # noqa: F401
from app.core.billing.tariffs.models import ServiceTariff  # noqa: F401
from app.core.billing.billing_entries.models import BillingEntry, BillingReversal, FinancialAuditLog  # noqa: F401
from app.core.billing.insurance.models import InsuranceProvider, InsurancePackage, InsurancePolicy, PreAuthorization, InsuranceClaim, ClaimItem  # noqa: F401
from app.core.billing.discounts.models import DiscountRule  # noqa: F401
from app.core.billing.invoices.models import Invoice  # noqa: F401
from app.core.billing.payments.models import Payment  # noqa: F401
from app.core.lab.models import LabTest, LabOrder, LabSample, LabResult, LabValidation, LabProcessing  # noqa: F401
from app.core.pharmacy.medications.models import Medication  # noqa: F401
from app.core.pharmacy.prescriptions.models import Prescription, PrescriptionItem  # noqa: F401
from app.core.pharmacy.dispensing.models import DispensingRecord  # noqa: F401
from app.core.pharmacy.inventory.models import InventoryItem, ControlledDrugLog  # noqa: F401
from app.core.pharmacy.batches.models import DrugBatch  # noqa: F401
# from app.core.pharmacy.drug_interactions.models import DrugInteraction  # noqa: F401
from app.core.orders.templates.models import OrderTemplate, OrderTemplateItem, OrderSet, OrderSetItem  # noqa: F401

# Phase 9 – AI Platform
from app.core.ai.models import AISummary, ClinicalInsight, RiskAlert, VoiceCommand, AIAgentTask  # noqa: F401

# Phase 10 - Analytics
from app.core.analytics.clinical_metrics.models import DailyClinicalMetric  # noqa: F401
from app.core.analytics.financial_metrics.models import DailyFinancialMetric  # noqa: F401
from app.core.analytics.operational_metrics.models import DailyOperationalMetric  # noqa: F401

# Phase 11 - System
from app.core.system.logging.models import SystemLog  # noqa: F401
from app.core.system.monitoring.models import TrackedError, PerformanceMetric  # noqa: F401
from app.core.analytics.predictive_models.models import HospitalPrediction  # noqa: F401

# Hospital Intelligence & Analytics Engine
from app.core.hospital_intelligence.models import (
    AnalyticsPatientFlow,
    AnalyticsDoctorProductivity,
    AnalyticsRevenue,
    AnalyticsClinicalStatistics,
    AnalyticsCrowdPrediction
)

# Phase 12 - CDSS
from app.core.cdss.drug_interactions.models import DrugInteraction  # noqa: F401
from app.core.cdss.allergy_checks.models import DrugAllergyMapping  # noqa: F401
from app.core.cdss.dose_validation.models import DrugDosageGuideline  # noqa: F401
from app.core.cdss.duplicate_therapy.models import DrugClass  # noqa: F401
from app.core.cdss.contraindications.models import DrugContraindication  # noqa: F401
from app.core.cdss.engine.models import CDSSAlert  # noqa: F401

# Phase 13 - Blood Bank
from app.core.blood_bank.blood_components.models import BloodComponent  # noqa: F401
from app.core.blood_bank.blood_inventory.models import BloodStorageUnit  # noqa: F401
from app.core.blood_bank.donors.models import BloodDonor, BloodCollection  # noqa: F401
from app.core.blood_bank.blood_units.models import BloodUnit  # noqa: F401
from app.core.blood_bank.transfusion_orders.models import TransfusionOrder, BloodAllocation  # noqa: F401
from app.core.blood_bank.compatibility_tests.models import CrossmatchTest  # noqa: F401
from app.core.blood_bank.transfusions.models import Transfusion  # noqa: F401
from app.core.blood_bank.transfusion_reactions.models import TransfusionReaction  # noqa: F401
from app.core.communication.messages.models import Message  # noqa: F401
from app.core.communication.channels.models import Channel, ChannelMember, ChannelMessage  # noqa: F401
from app.core.communication.alerts.models import ClinicalAlert  # noqa: F401
from app.core.communication.notifications.models import CommunicationNotification  # noqa: F401
from app.core.communication.escalations.models import TaskEscalation  # noqa: F401
from app.core.communication.patient_threads.models import PatientThread  # noqa: F401

# Phase 10 - Ward & Bed Management
from app.core.wards.models import Ward, Room, Bed, BedAssignment, BedTransfer, BedCleaningTask  # noqa: F401

# Phase 11 - Radiology & Imaging Management
from app.core.radiology.imaging_orders.models import ImagingOrder  # noqa: F401
from app.core.radiology.imaging_studies.models import ImagingStudy  # noqa: F401
from app.core.radiology.imaging_schedule.models import ImagingSchedule  # noqa: F401
from app.core.radiology.dicom_metadata.models import DICOMMetadata  # noqa: F401
from app.core.radiology.radiology_reports.models import RadiologyReport  # noqa: F401
from app.core.radiology.radiology_results.models import RadiologyResult  # noqa: F401

# Phase 14 - Operating Theatre
from app.core.ot.operating_rooms.models import OperatingRoom  # noqa: F401
from app.core.ot.surgical_procedures.models import SurgicalProcedure  # noqa: F401
from app.core.ot.surgery_schedule.models import SurgerySchedule  # noqa: F401
from app.core.ot.surgical_teams.models import SurgicalTeam  # noqa: F401
from app.core.ot.anesthesia_records.models import AnesthesiaRecord  # noqa: F401
from app.core.ot.surgery_events.models import SurgeryEvent  # noqa: F401
from app.core.ot.surgery_notes.models import SurgeryNote  # noqa: F401
from app.core.ot.postoperative_events.models import PostoperativeEvent  # noqa: F401

# Phase 16 - Patient Portal
from app.core.patient_portal.patient_accounts.models import PatientAccount  # noqa: F401
from app.core.patient_portal.appointments.models import PortalAppointment, DoctorAvailability  # noqa: F401
from app.core.patient_portal.teleconsultations.models import Teleconsultation  # noqa: F401
from app.core.patient_portal.medical_records.models import PatientDocument  # noqa: F401
from app.core.patient_portal.patient_payments.models import PatientPayment  # noqa: F401

# Enterprise Registration (OPD FRD)
from app.core.patients.registration.models import (  # noqa: F401
    RegistrationSession,
    IDScanRecord,
    FaceEmbedding,
    HealthCard,
    RegistrationDocument,
    RegistrationNotification,
    AddressDirectory,
)

# Enterprise Scheduling
from app.core.scheduling.models import (  # noqa: F401
    DoctorCalendar,
    CalendarSlot,
    SlotBooking,
    OverbookingConfig,
    CyclicSchedule,
    ModalityResource,
    ModalitySlot,
    AppointmentReminder,
    FollowUpRule,
    SchedulingAnalytics,
)

# OPD Visit Intelligence Engine
from app.core.opd_visits.models import (  # noqa: F401
    VisitMaster,
    VisitComplaint,
    VisitClassification,
    VisitDoctorRecommendation,
    VisitQuestionnaireTemplate,
    VisitQuestionnaireResponse,
    VisitContextSnapshot,
    MultiVisitRule,
    VisitAnalyticsSnapshot,
)

# OPD Smart Queue & Flow Orchestration Engine
from app.core.smart_queue.models import (  # noqa: F401
    QueueMaster,
    QueuePatientPosition,
    QueueEvent,
    QueueNotification,
    WayfindingNode,
    RoomWayfindingMapping,
    CrowdPredictionSnapshot,
)

# OPD Nursing Clinical Triage Engine
from app.core.nursing_triage.models import (  # noqa: F401
    NursingWorklist,
    NursingVitals,
    NursingAssessment,
    NursingTemplate,
    NursingDocumentUpload,
    TriagePriorityUpdate,
)

# AI Doctor Desk & Intelligent EMR Engine
from app.core.doctor_desk.models import (  # noqa: F401
    DoctorWorklist,
    ConsultationNote,
    DoctorClinicalTemplate,
    DoctorPrescription,
    DoctorDiagnosticOrder,
    DoctorClinicalSummary,
    FollowUpRecord,
)

# Enterprise OPD Billing & Revenue Cycle Engine
from app.core.rcm_billing.models import (  # noqa: F401
    BillingMaster,
    BillingService,
    BillingPayment,
    BillingDiscount,
    BillingRefund,
    BillingPayer,
    BillingTariff,
)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", str(settings.database_url))


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
