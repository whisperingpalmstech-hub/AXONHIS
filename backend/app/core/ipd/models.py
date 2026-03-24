import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, JSON, Index, Float, Text, Date
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.database import Base

class IpdAdmissionRequest(Base):
    __tablename__ = "ipd_admission_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(String, unique=True, nullable=False, index=True) # e.g. ADM-REQ-2026-000214
    patient_name = Column(String, nullable=False)
    patient_uhid = Column(String, nullable=False, index=True)
    gender = Column(String, nullable=False)
    date_of_birth = Column(String, nullable=False)
    mobile_number = Column(String, nullable=False)
    blood_group = Column(String, nullable=True)

    admitting_doctor = Column(String, nullable=False)
    treating_doctor = Column(String, nullable=False)
    specialty = Column(String, nullable=False)
    reason_for_admission = Column(String, nullable=False)

    admission_category = Column(String, nullable=False) # Emergency, Planned Admission, Day Care Admission
    admission_source = Column(String, nullable=False) # OPD, Emergency, Referral
    preferred_bed_category = Column(String, nullable=False)
    expected_admission_date = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(String, default="Pending", nullable=False) # Pending, Approved, Rejected, Allocated
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)


class IpdAdmissionRecord(Base):
    __tablename__ = "ipd_admission_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, unique=True, nullable=False, index=True) # e.g. IPD-ADM-2026-003541
    request_id = Column(UUID(as_uuid=True), ForeignKey("ipd_admission_requests.id", ondelete="SET NULL"), nullable=True)
    patient_uhid = Column(String, nullable=False, index=True)
    visit_id = Column(String, nullable=True)
    
    bed_uuid = Column(UUID(as_uuid=True), ForeignKey("beds.id", ondelete="RESTRICT"), nullable=False)
    admitting_doctor = Column(String, nullable=False)
    
    admission_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    discharge_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="Admitted", nullable=False) # Admitted, Transferred, Discharged


class IpdAdmissionAuditLog(Base):
    __tablename__ = "ipd_admission_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    action_type = Column(String, nullable=False) # Request Created, Bed Allocated, Admission Approved, Discharged
    entity_id = Column(String, nullable=False) # Request ID or Admission Number
    patient_uhid = Column(String, nullable=True)
    details = Column(JSON, nullable=False, default={})
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdCostEstimation(Base):
    __tablename__ = "ipd_cost_estimations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(UUID(as_uuid=True), ForeignKey("ipd_admission_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_uhid = Column(String, nullable=False)
    
    selected_bed_category = Column(String, nullable=False)
    planned_procedures = Column(JSONB, default=list) # e.g. ["Appendectomy", "Anesthesia"]
    planned_services = Column(JSONB, default=list) # e.g. ["Nursing", "Dietary"]
    
    estimated_cost_lower = Column(Float, default=0.0)
    estimated_cost_upper = Column(Float, default=0.0)
    
    generated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    generated_by = Column(UUID(as_uuid=True), nullable=True)

class IpdAdmissionChecklist(Base):
    __tablename__ = "ipd_admission_checklists"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, index=True)
    
    registration_completed = Column(Boolean, default=False)
    identity_proof_verified = Column(Boolean, default=False)
    insurance_captured = Column(Boolean, default=False)
    preauth_initiated = Column(Boolean, default=False)
    consent_taken = Column(Boolean, default=False)
    kin_details_recorded = Column(Boolean, default=False)
    deposit_collected = Column(Boolean, default=False)
    
    is_complete = Column(Boolean, default=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

class IpdInsuranceDetails(Base):
    __tablename__ = "ipd_insurance_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    
    provider_name = Column(String, nullable=False)
    policy_number = Column(String, nullable=False)
    total_sum_assured = Column(Float, default=0.0)
    bed_charge_limit_percent = Column(Float, default=1.0) # E.g., 0.01 for 1% of total sum
    eligible_bed_category = Column(String, nullable=True)
    
    preauth_number = Column(String, nullable=True)
    preauth_amount = Column(Float, default=0.0)
    status = Column(String, default="Pending Validation") # Validated, Rejected

class IpdProjectedBill(Base):
    __tablename__ = "ipd_projected_bills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), unique=True, nullable=False)
    
    bed_charges = Column(Float, default=0.0)
    investigations = Column(Float, default=0.0)
    procedures = Column(Float, default=0.0)
    medications = Column(Float, default=0.0)
    consumables = Column(Float, default=0.0)
    other_charges = Column(Float, default=0.0)
    
    total_projected_amount = Column(Float, default=0.0)
    
    last_recalculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class IpdDepositRecord(Base):
    __tablename__ = "ipd_deposit_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    receipt_number = Column(String, unique=True, nullable=False)
    
    deposit_amount = Column(Float, nullable=False)
    payment_mode = Column(String, nullable=False) # Cash, Card, Bank Transfer
    reference_id = Column(String, nullable=True) # Transaction ID
    
    collected_by = Column(UUID(as_uuid=True), nullable=True)
    collected_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdPatientTransport(Base):
    __tablename__ = "ipd_patient_transport"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    
    transport_type = Column(String, nullable=False) # Wheelchair, Stretcher, Bed
    source = Column(String, nullable=False) # e.g. Admission Desk
    destination = Column(String, nullable=False) # e.g. General Ward Level 3
    
    status = Column(String, default="Requested") # Requested, Assigned, Completed
    assigned_staff_id = Column(UUID(as_uuid=True), nullable=True)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdAdmissionDocument(Base):
    __tablename__ = "ipd_admission_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    
    document_type = Column(String, nullable=False) # Insurance Policy, Identity Proof, Consent Form
    file_url = Column(String, nullable=False)
    file_format = Column(String, nullable=False) # pdf, jpg
    
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    uploaded_by = Column(UUID(as_uuid=True), nullable=True)

# --- Phase 15: Nursing Coversheet & Patient Acceptance ---

class IpdNursingWorklist(Base):
    __tablename__ = "ipd_nursing_worklist"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    patient_uhid = Column(String, nullable=False)
    bed_uuid = Column(UUID(as_uuid=True), nullable=False)
    ward_name = Column(String, nullable=True) # Readonly projection from mapping for quick lists
    bed_number = Column(String, nullable=True)
    admitting_doctor = Column(String, nullable=True)
    admission_time = Column(DateTime(timezone=True), nullable=False)
    
    status = Column(String, default="Pending Acceptance") # Pending Acceptance, Accepted
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdNursingCoversheet(Base):
    __tablename__ = "ipd_nursing_coversheets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    patient_uhid = Column(String, nullable=False)
    bed_uuid = Column(UUID(as_uuid=True), nullable=False)
    primary_diagnosis = Column(String, nullable=True)
    treating_doctor_id = Column(UUID(as_uuid=True), nullable=True)
    treating_doctor_name = Column(String, nullable=True)
    
    priority_status = Column(String, default="Normal") # Critical, VIP, Review, Normal
    
    acceptance_time = Column(DateTime(timezone=True), nullable=True)
    accepted_by_nurse_id = Column(UUID(as_uuid=True), nullable=True)
    accepted_by_nurse_name = Column(String, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdPatientStatusMonitor(Base):
    __tablename__ = "ipd_patient_status_monitor"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    status = Column(String, default="Pending Acceptance") # Pending Acceptance, Accepted, Under Observation, Under Treatment, Transferred, Discharged
    last_updated = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdNursingNote(Base):
    __tablename__ = "ipd_nursing_notes"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    note_type = Column(String, default="Initial Assessment") # e.g. Initial Assessment, Shift Handover
    clinical_note = Column(Text, nullable=False)
    
    logged_by_id = Column(UUID(as_uuid=True), nullable=False)
    logged_by_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdCareAssignment(Base):
    __tablename__ = "ipd_care_assignments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    
    primary_nurse_id = Column(UUID(as_uuid=True), nullable=True)
    primary_nurse_name = Column(String, nullable=True)
    shift_nurse_id = Column(UUID(as_uuid=True), nullable=True)
    shift_nurse_name = Column(String, nullable=True)
    ward_supervisor_id = Column(UUID(as_uuid=True), nullable=True)
    ward_supervisor_name = Column(String, nullable=True)
    
    start_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime(timezone=True), nullable=True)

class IpdNursingAuditLog(Base):
    __tablename__ = "ipd_nursing_audit_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, nullable=False)
    action = Column(String, nullable=False) # e.g. Patient Accepted, Priority Changed
    nurse_id = Column(UUID(as_uuid=True), nullable=False)
    nurse_name = Column(String, nullable=False)
    details = Column(JSON, nullable=True) # Immutably stores what changed and existing state
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# --- Phase 16: Nursing Assessment & Vitals Monitoring ---

class IpdVitalsRecord(Base):
    __tablename__ = "ipd_vitals_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    
    temperature = Column(Float, nullable=True)       # °C
    pulse_rate = Column(Integer, nullable=True)       # bpm
    respiratory_rate = Column(Integer, nullable=True)  # breaths/min
    bp_systolic = Column(Integer, nullable=True)       # mmHg
    bp_diastolic = Column(Integer, nullable=True)      # mmHg
    spo2 = Column(Float, nullable=True)                # %
    height_cm = Column(Float, nullable=True)
    weight_kg = Column(Float, nullable=True)
    bmi = Column(Float, nullable=True)                 # auto-calculated
    blood_glucose = Column(Float, nullable=True)       # mg/dL
    pain_score = Column(Integer, nullable=True)        # 0-10
    gcs_score = Column(Integer, nullable=True)         # Glasgow Coma Scale 3-15
    
    recorded_by_id = Column(UUID(as_uuid=True), nullable=True)
    recorded_by_name = Column(String, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    alert_triggered = Column(Boolean, default=False)
    alert_message = Column(String, nullable=True)

class IpdNursingAssessment(Base):
    __tablename__ = "ipd_nursing_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    patient_uhid = Column(String, nullable=False)
    
    presenting_complaints = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    surgical_history = Column(Text, nullable=True)
    allergy_information = Column(Text, nullable=True)
    medication_history = Column(Text, nullable=True)
    family_history = Column(Text, nullable=True)
    
    # Lifestyle
    smoking_status = Column(String, nullable=True)    # Never, Former, Current
    alcohol_consumption = Column(String, nullable=True) # None, Occasional, Regular
    exercise_habits = Column(String, nullable=True)
    
    assessed_by_id = Column(UUID(as_uuid=True), nullable=True)
    assessed_by_name = Column(String, nullable=True)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdRiskAssessment(Base):
    __tablename__ = "ipd_risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    
    risk_type = Column(String, nullable=False)  # Fall Risk, Pressure Ulcer, Infection, Mobility
    risk_score = Column(Integer, nullable=True)
    risk_level = Column(String, nullable=True)  # Low, Moderate, High, Critical
    details = Column(JSON, nullable=True)
    
    assessed_by_name = Column(String, nullable=True)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdPainScore(Base):
    __tablename__ = "ipd_pain_scores"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    
    pain_scale = Column(String, default="NRS")  # NRS (Numeric Rating Scale), VAS (Visual Analog)
    score = Column(Integer, nullable=False)      # 0-10
    location = Column(String, nullable=True)     # Body location
    character = Column(String, nullable=True)    # Sharp, Dull, Burning etc.
    
    recorded_by_name = Column(String, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdNutritionAssessment(Base):
    __tablename__ = "ipd_nutrition_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    
    bmi = Column(Float, nullable=True)
    dietary_habits = Column(String, nullable=True)    # Vegetarian, Non-Vegetarian, Vegan
    appetite_status = Column(String, nullable=True)   # Good, Poor, Anorexia
    malnutrition_risk = Column(String, nullable=True) # Low, Moderate, High
    dietician_notified = Column(Boolean, default=False)
    
    assessed_by_name = Column(String, nullable=True)
    assessed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdNursingObservation(Base):
    __tablename__ = "ipd_nursing_observations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    
    observation_type = Column(String, default="General")  # General, Critical, Shift Handover
    note = Column(Text, nullable=False)
    
    recorded_by_id = Column(UUID(as_uuid=True), nullable=True)
    recorded_by_name = Column(String, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# --- Phase 17: Doctor Coversheet & Clinical Documentation ---

class IpdDoctorWorklist(Base):
    __tablename__ = "ipd_doctor_worklist"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    doctor_uuid = Column(UUID(as_uuid=True), nullable=False)
    doctor_name = Column(String, nullable=False)
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="Active")

class IpdDoctorCoversheet(Base):
    __tablename__ = "ipd_doctor_coversheets"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    patient_uhid = Column(String, nullable=False)
    primary_diagnosis = Column(String, nullable=True)
    clinical_summary = Column(Text, nullable=True)
    verified_by_doctor = Column(String, nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

class IpdDiagnosis(Base):
    __tablename__ = "ipd_diagnoses"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    diagnosis_type = Column(String, nullable=False) # Provisional, Confirmed, Secondary
    icd10_code = Column(String, nullable=True)
    description = Column(String, nullable=False)
    diagnosed_by_name = Column(String, nullable=False)
    diagnosed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdTreatmentPlan(Base):
    __tablename__ = "ipd_treatment_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    therapy_type = Column(String, nullable=False) # Medication, Procedure, Investigation, Supportive
    instructions = Column(Text, nullable=False)
    created_by_name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdProgressNote(Base):
    __tablename__ = "ipd_progress_notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    doctor_name = Column(String, nullable=False)
    notes = Column(Text, nullable=False)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdClinicalProcedure(Base):
    __tablename__ = "ipd_clinical_procedures"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    procedure_name = Column(String, nullable=False)
    procedure_date = Column(DateTime(timezone=True), nullable=False)
    performing_doctor = Column(String, nullable=False)
    notes = Column(Text, nullable=True)

class IpdConsultationRequest(Base):
    __tablename__ = "ipd_consultation_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    consulting_department = Column(String, nullable=False)
    reason_for_referral = Column(Text, nullable=False)
    urgency_level = Column(String, default="Routine") # Routine, Urgent, Emergency
    requested_by = Column(String, nullable=False)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="Pending") # Pending, Completed

# --- Phase 18: IPD Clinical Orders Management Engine ---

class IpdOrdersMaster(Base):
    __tablename__ = "ipd_orders_master"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    doctor_uuid = Column(UUID(as_uuid=True), nullable=True)
    doctor_name = Column(String, nullable=False)
    order_type = Column(String, nullable=False) # Laboratory, Radiology, Medication, Procedure, Nursing
    priority = Column(String, default="Routine") # Routine, Urgent, STAT
    order_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="Ordered") # Ordered, Scheduled, In Progress, Completed, Cancelled
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True) # e.g. "Daily", "BID"

class IpdLabOrder(Base):
    __tablename__ = "ipd_lab_orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("ipd_orders_master.id", ondelete="CASCADE"), nullable=False)
    test_name = Column(String, nullable=False)
    sample_type = Column(String, nullable=True)
    clinical_indication = Column(Text, nullable=True)
    result_status = Column(String, default="Pending") # Pending, Sample Collected, Processing, Result Available

class IpdRadiologyOrder(Base):
    __tablename__ = "ipd_radiology_orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("ipd_orders_master.id", ondelete="CASCADE"), nullable=False)
    imaging_type = Column(String, nullable=False) # X-Ray, Ultrasound, CT Scan, MRI
    target_area = Column(String, nullable=False)
    clinical_indication = Column(Text, nullable=True)
    report_status = Column(String, default="Pending") # Pending, Scheduled, Performed, Reported

class IpdMedicationOrder(Base):
    __tablename__ = "ipd_medication_orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("ipd_orders_master.id", ondelete="CASCADE"), nullable=False)
    medicine_name = Column(String, nullable=False)
    dosage = Column(String, nullable=False)
    frequency = Column(String, nullable=False) # OD, BID, TID, QID
    route = Column(String, nullable=False) # Oral, IV, IM, SC
    duration_days = Column(Integer, nullable=True)
    pharmacy_status = Column(String, default="Pending") # Pending, Dispensed, Administered

class IpdProcedureOrder(Base):
    __tablename__ = "ipd_procedure_orders"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("ipd_orders_master.id", ondelete="CASCADE"), nullable=False)
    procedure_service_name = Column(String, nullable=False)
    department = Column(String, nullable=False) # Physiotherapy, Surgery, Dietetics
    scheduling_notes = Column(Text, nullable=True)
    execution_status = Column(String, default="Pending")

class IpdOrderStatusLog(Base):
    __tablename__ = "ipd_order_status_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("ipd_orders_master.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    updated_by = Column(String, nullable=False) # Name of user
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    remarks = Column(Text, nullable=True)

# --- Phase 19: IPD Bed Transfer & Patient Movement Engine ---

class IpdTransferRequest(Base):
    __tablename__ = "ipd_transfer_requests"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    current_ward = Column(String, nullable=False)
    current_bed = Column(String, nullable=False)
    requested_ward = Column(String, nullable=False)
    requested_bed_category = Column(String, nullable=True)  # General, Semi-Private, Private, ICU
    requested_bed = Column(String, nullable=True)
    reason = Column(Text, nullable=False)
    transfer_type = Column(String, default="Ward-to-Ward")  # Bed-to-Bed, Ward-to-Ward, ICU Transfer
    priority = Column(String, default="Routine")  # Routine, Urgent, Emergency
    requested_by = Column(String, nullable=False)
    requested_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="Pending")  # Pending, Approved, Rejected, Completed, Cancelled

class IpdTransferRecord(Base):
    __tablename__ = "ipd_transfer_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_request_id = Column(UUID(as_uuid=True), ForeignKey("ipd_transfer_requests.id", ondelete="CASCADE"), nullable=False)
    admission_number = Column(String, nullable=False)
    patient_uhid = Column(String, nullable=False)
    from_ward = Column(String, nullable=False)
    from_bed = Column(String, nullable=False)
    to_ward = Column(String, nullable=False)
    to_bed = Column(String, nullable=False)
    transfer_type = Column(String, nullable=False)
    transferred_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    approved_by = Column(String, nullable=False)
    executed_by = Column(String, nullable=True)

class IpdBedMovement(Base):
    __tablename__ = "ipd_bed_movements"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, nullable=False)
    patient_uhid = Column(String, nullable=False)
    previous_ward = Column(String, nullable=True)
    previous_bed = Column(String, nullable=True)
    new_ward = Column(String, nullable=False)
    new_bed = Column(String, nullable=False)
    movement_reason = Column(String, nullable=False)
    moved_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    recorded_by = Column(String, nullable=False)

class IpdTransferHandover(Base):
    __tablename__ = "ipd_transfer_handovers"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_request_id = Column(UUID(as_uuid=True), ForeignKey("ipd_transfer_requests.id", ondelete="CASCADE"), nullable=False)
    admission_number = Column(String, nullable=False)
    # ISBAR fields
    identification = Column(Text, nullable=True)
    situation = Column(Text, nullable=False)
    background = Column(Text, nullable=False)
    assessment = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)
    documented_by = Column(String, nullable=False)
    documented_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdTransferNotification(Base):
    __tablename__ = "ipd_transfer_notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_request_id = Column(UUID(as_uuid=True), ForeignKey("ipd_transfer_requests.id", ondelete="CASCADE"), nullable=False)
    recipient_role = Column(String, nullable=False)  # Nurse, Doctor, Bed Manager
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdTransferAuditLog(Base):
    __tablename__ = "ipd_transfer_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transfer_request_id = Column(UUID(as_uuid=True), ForeignKey("ipd_transfer_requests.id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)  # Created, Approved, Rejected, Completed, Cancelled
    performed_by = Column(String, nullable=False)
    performed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details = Column(Text, nullable=True)

# --- Phase 20: IPD Smart Discharge Planning Engine ---

class IpdDischargePlan(Base):
    __tablename__ = "ipd_discharge_plans"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    patient_uhid = Column(String, nullable=False)
    doctor_uuid = Column(String, nullable=True)
    planned_discharge_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, default="Planned")  # Planned, In Progress, Ready, Discharged, Cancelled
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdDischargeChecklist(Base):
    __tablename__ = "ipd_discharge_checklists"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    patient_uhid = Column(String, nullable=False)
    doctor_approval = Column(Boolean, default=False)
    nursing_clearance = Column(Boolean, default=False)
    medications_reconciled = Column(Boolean, default=False)
    final_investigations_checked = Column(Boolean, default=False)
    patient_counseling = Column(Boolean, default=False)
    billing_clearance = Column(Boolean, default=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdDischargeSummary(Base):
    __tablename__ = "ipd_discharge_summaries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    patient_uhid = Column(String, nullable=False)
    doctor_uuid = Column(String, nullable=True)
    admission_diagnosis = Column(Text, nullable=True)
    hospital_course = Column(Text, nullable=True)
    procedures_performed = Column(Text, nullable=True)
    medications_prescribed = Column(Text, nullable=True)
    follow_up_instructions = Column(Text, nullable=True)
    status = Column(String, default="Draft")  # Draft, Finalized
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finalized_at = Column(DateTime(timezone=True), nullable=True)

class IpdDischargeNote(Base):
    __tablename__ = "ipd_discharge_notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    nurse_uuid = Column(String, nullable=True)
    patient_condition = Column(Text, nullable=False)
    instructions_given = Column(Text, nullable=False)
    wound_care_guidance = Column(Text, nullable=True)
    recorded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdDischargeNotification(Base):
    __tablename__ = "ipd_discharge_notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    department = Column(String, nullable=False)  # Billing, Pharmacy, Housekeeping
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdDischargeAuditLog(Base):
    __tablename__ = "ipd_discharge_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)  # Checklist Updated, Summary Finalized, Discharged
    performed_by = Column(String, nullable=False)
    performed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details = Column(Text, nullable=True)

# --- Phase 21: IPD Billing & Payment Settlement Engine ---

class IpdBillingMaster(Base):
    __tablename__ = "ipd_billing_master"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False, unique=True)
    patient_uhid = Column(String, nullable=False)
    patient_name = Column(String, nullable=False)
    ward_name = Column(String, nullable=True)
    bed_code = Column(String, nullable=True)
    total_charges = Column(Float, default=0.0)
    total_deposits = Column(Float, default=0.0)
    total_discount = Column(Float, default=0.0)
    total_tax = Column(Float, default=0.0)
    insurance_payable = Column(Float, default=0.0)
    patient_payable = Column(Float, default=0.0)
    total_paid = Column(Float, default=0.0)
    outstanding_balance = Column(Float, default=0.0)
    status = Column(String, default="Active")  # Active, Interim, Final, Settled, Closed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdBillingService(Base):
    __tablename__ = "ipd_billing_services"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    service_category = Column(String, nullable=False)  # Bed, Lab, Radiology, Pharmacy, Procedure, Nursing, Consumable
    service_name = Column(String, nullable=False)
    service_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    source_order_id = Column(String, nullable=True)  # FK to originating order
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdBillingDeposit(Base):
    __tablename__ = "ipd_billing_deposits"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    payment_mode = Column(String, nullable=False)  # Cash, Card, UPI, Bank Transfer
    receipt_number = Column(String, nullable=True)
    reference_number = Column(String, nullable=True)
    collected_by = Column(String, nullable=True)
    deposit_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String, default="Collected")  # Collected, Adjusted, Refunded

class IpdInsuranceClaim(Base):
    __tablename__ = "ipd_insurance_claims"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    insurance_provider = Column(String, nullable=False)
    policy_number = Column(String, nullable=False)
    pre_auth_number = Column(String, nullable=True)
    coverage_limit = Column(Float, default=0.0)
    claimed_amount = Column(Float, default=0.0)
    approved_amount = Column(Float, default=0.0)
    patient_share = Column(Float, default=0.0)
    status = Column(String, default="Pending")  # Pending, Submitted, Approved, Rejected, Settled
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdPaymentTransaction(Base):
    __tablename__ = "ipd_payment_transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    payment_mode = Column(String, nullable=False)  # Cash, Credit Card, Debit Card, Cheque, Bank Transfer, Online
    reference_number = Column(String, nullable=True)
    receipt_number = Column(String, nullable=True)
    payment_type = Column(String, default="Settlement")  # Settlement, Partial, Refund
    processed_by = Column(String, nullable=True)
    payment_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdRefundRecord(Base):
    __tablename__ = "ipd_refund_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    refund_amount = Column(Float, nullable=False)
    refund_mode = Column(String, nullable=False)  # Cash, Bank Transfer, Digital Wallet
    refund_reason = Column(Text, nullable=True)
    approved_by = Column(String, nullable=True)
    processed_by = Column(String, nullable=True)
    status = Column(String, default="Pending")  # Pending, Approved, Processed
    refund_date = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdBillingAuditLog(Base):
    __tablename__ = "ipd_billing_audit_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)
    performed_by = Column(String, nullable=False)
    performed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    details = Column(Text, nullable=True)


# Phase 22: Visitor Management & Medico-Legal Case (MLC) Engine
class IpdVisitor(Base):
    __tablename__ = "ipd_visitors"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    patient_uhid = Column(String, nullable=False)
    visitor_name = Column(String, nullable=False)
    relationship = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    id_proof = Column(String, nullable=False)
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdVisitorPass(Base):
    __tablename__ = "ipd_visitor_passes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pass_number = Column(String, unique=True, nullable=False, index=True) # VIS-2026-...
    visitor_id = Column(UUID(as_uuid=True), ForeignKey("ipd_visitors.id", ondelete="CASCADE"), nullable=False)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), nullable=False)
    ward_name = Column(String, nullable=False)
    visit_date = Column(Date, default=lambda: datetime.now(timezone.utc).date())
    pass_type = Column(String, default="Standard") # Standard, ICU, Attendant
    status = Column(String, default="Active") # Active, Expired, Revoked
    generated_by = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdVisitorLog(Base):
    __tablename__ = "ipd_visitor_logs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pass_number = Column(String, ForeignKey("ipd_visitor_passes.pass_number", ondelete="CASCADE"), nullable=False)
    entry_time = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    exit_time = Column(DateTime(timezone=True), nullable=True)
    checkpoint = Column(String, nullable=False) # Main Gate, ICU Gate
    security_guard_id = Column(String, nullable=True)

class IpdMlcCase(Base):
    __tablename__ = "ipd_mlc_cases"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, ForeignKey("ipd_admission_records.admission_number", ondelete="CASCADE"), unique=True, nullable=False)
    patient_uhid = Column(String, nullable=False)
    case_type = Column(String, nullable=False) # Road Accident, Assault, Burn, Poisoning
    incident_details = Column(Text, nullable=True)
    
    police_station = Column(String, nullable=True)
    fir_number = Column(String, nullable=True)
    officer_name = Column(String, nullable=True)
    officer_badge = Column(String, nullable=True)
    
    registered_by = Column(String, nullable=False)
    status = Column(String, default="Active") # Active, Closed, Sent for Legal Review
    registered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdMlcDocument(Base):
    __tablename__ = "ipd_mlc_documents"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mlc_id = Column(UUID(as_uuid=True), ForeignKey("ipd_mlc_cases.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(String, nullable=False) # FIR Copy, Consent, Medical Report
    file_url = Column(String, nullable=False)
    uploaded_by = Column(String, nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class IpdSecurityNotification(Base):
    __tablename__ = "ipd_security_notifications"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admission_number = Column(String, nullable=False)
    notification_type = Column(String, nullable=False) # MLC Alert, VIP Admission, High Risk
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
