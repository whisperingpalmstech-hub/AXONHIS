from datetime import datetime, date
from pydantic import BaseModel, ConfigDict
import uuid
from uuid import UUID
from typing import Optional, Any

class IpdAdmissionRequestCreate(BaseModel):
    patient_name: str
    patient_uhid: str
    gender: str
    date_of_birth: str
    mobile_number: str
    blood_group: Optional[str] = None
    admitting_doctor: str
    treating_doctor: str
    specialty: str
    reason_for_admission: str
    admission_category: str
    admission_source: str
    preferred_bed_category: str
    expected_admission_date: datetime

class IpdAdmissionRequestOut(BaseModel):
    id: uuid.UUID
    request_id: str
    patient_name: str
    patient_uhid: str
    gender: str
    date_of_birth: str
    mobile_number: str
    admitting_doctor: str
    treating_doctor: str
    specialty: str
    reason_for_admission: str
    admission_category: str
    admission_source: str
    preferred_bed_category: str
    expected_admission_date: datetime
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class BedAllocationRequest(BaseModel):
    bed_id: str
    
class IpdAdmissionRecordOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    request_id: Optional[uuid.UUID] = None
    patient_uhid: str
    visit_id: Optional[str] = None
    bed_uuid: uuid.UUID
    admitting_doctor: str
    admission_time: datetime
    status: str

    model_config = ConfigDict(from_attributes=True)

class DashboardStats(BaseModel):
    total_beds: int
    occupied_beds: int
    available_beds: int
    housekeeping_beds: int
    reserved_beds: int
    pending_requests: int

# --- Phase 14 Models ---
class IpdCostEstimationCreate(BaseModel):
    selected_bed_category: str
    planned_procedures: list[str] = []
    planned_services: list[str] = []

class IpdCostEstimationOut(BaseModel):
    id: uuid.UUID
    request_id: uuid.UUID
    patient_uhid: str
    selected_bed_category: str
    planned_procedures: list[str]
    planned_services: list[str]
    estimated_cost_lower: float
    estimated_cost_upper: float
    generated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdAdmissionChecklistUpdate(BaseModel):
    registration_completed: Optional[bool] = None
    identity_proof_verified: Optional[bool] = None
    insurance_captured: Optional[bool] = None
    preauth_initiated: Optional[bool] = None
    consent_taken: Optional[bool] = None
    kin_details_recorded: Optional[bool] = None
    deposit_collected: Optional[bool] = None

class IpdAdmissionChecklistOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    registration_completed: bool
    identity_proof_verified: bool
    insurance_captured: bool
    preauth_initiated: bool
    consent_taken: bool
    kin_details_recorded: bool
    deposit_collected: bool
    is_complete: bool
    completed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)

class IpdInsuranceDetailsCreate(BaseModel):
    provider_name: str
    policy_number: str
    total_sum_assured: float
    bed_charge_limit_percent: float

class IpdInsuranceDetailsOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    provider_name: str
    policy_number: str
    total_sum_assured: float
    bed_charge_limit_percent: float
    eligible_bed_category: Optional[str] = None
    preauth_number: Optional[str] = None
    preauth_amount: float
    status: str
    
    model_config = ConfigDict(from_attributes=True)

class IpdProjectedBillOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    bed_charges: float
    investigations: float
    procedures: float
    medications: float
    consumables: float
    other_charges: float
    total_projected_amount: float
    last_recalculated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class IpdDepositRecordCreate(BaseModel):
    deposit_amount: float
    payment_mode: str
    reference_id: Optional[str] = None

class IpdDepositRecordOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    receipt_number: str
    deposit_amount: float
    payment_mode: str
    reference_id: Optional[str] = None
    collected_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdPatientTransportCreate(BaseModel):
    transport_type: str
    source: str
    destination: str

class IpdPatientTransportOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    transport_type: str
    source: str
    destination: str
    status: str
    requested_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdAdmissionDocumentCreate(BaseModel):
    document_type: str
    file_url: str
    file_format: str

class IpdAdmissionDocumentOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    document_type: str
    file_url: str
    file_format: str
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Phase 15: Nursing Coversheet & Patient Acceptance ---

class IpdNursingWorklistOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    bed_uuid: uuid.UUID
    ward_name: Optional[str] = None
    bed_number: Optional[str] = None
    admitting_doctor: Optional[str] = None
    admission_time: datetime
    status: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdNursingCoversheetCreate(BaseModel):
    admission_number: str
    priority_status: Optional[str] = "Normal"

class IpdNursingCoversheetOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    bed_uuid: uuid.UUID
    primary_diagnosis: Optional[str] = None
    treating_doctor_name: Optional[str] = None
    priority_status: str
    acceptance_time: Optional[datetime] = None
    accepted_by_nurse_name: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class IpdNursingNoteCreate(BaseModel):
    note_type: str
    clinical_note: str

class IpdNursingNoteOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    note_type: str
    clinical_note: str
    logged_by_name: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdCareAssignmentCreate(BaseModel):
    primary_nurse_id: Optional[uuid.UUID] = None
    primary_nurse_name: Optional[str] = None
    shift_nurse_id: Optional[uuid.UUID] = None
    shift_nurse_name: Optional[str] = None
    ward_supervisor_id: Optional[uuid.UUID] = None
    ward_supervisor_name: Optional[str] = None
    
class IpdCareAssignmentOut(IpdCareAssignmentCreate):
    id: uuid.UUID
    admission_number: str
    start_time: datetime
    
    model_config = ConfigDict(from_attributes=True)
    
class IpdPatientStatusMonitorOut(BaseModel):
    admission_number: str
    status: str
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Phase 16: Nursing Assessment & Vitals Monitoring ---

class IpdVitalsRecordCreate(BaseModel):
    temperature: Optional[float] = None
    pulse_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    spo2: Optional[float] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    blood_glucose: Optional[float] = None
    pain_score: Optional[int] = None
    gcs_score: Optional[int] = None

class IpdVitalsRecordOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    temperature: Optional[float] = None
    pulse_rate: Optional[int] = None
    respiratory_rate: Optional[int] = None
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    spo2: Optional[float] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    bmi: Optional[float] = None
    blood_glucose: Optional[float] = None
    pain_score: Optional[int] = None
    gcs_score: Optional[int] = None
    recorded_by_name: Optional[str] = None
    recorded_at: datetime
    alert_triggered: bool = False
    alert_message: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class IpdNursingAssessmentCreate(BaseModel):
    presenting_complaints: Optional[str] = None
    medical_history: Optional[str] = None
    surgical_history: Optional[str] = None
    allergy_information: Optional[str] = None
    medication_history: Optional[str] = None
    family_history: Optional[str] = None
    smoking_status: Optional[str] = None
    alcohol_consumption: Optional[str] = None
    exercise_habits: Optional[str] = None

class IpdNursingAssessmentOut(IpdNursingAssessmentCreate):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    assessed_by_name: Optional[str] = None
    assessed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdRiskAssessmentCreate(BaseModel):
    risk_type: str
    risk_score: Optional[int] = None
    risk_level: Optional[str] = None
    details: Optional[dict] = None

class IpdRiskAssessmentOut(IpdRiskAssessmentCreate):
    id: uuid.UUID
    admission_number: str
    assessed_by_name: Optional[str] = None
    assessed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdPainScoreCreate(BaseModel):
    pain_scale: str = "NRS"
    score: int
    location: Optional[str] = None
    character: Optional[str] = None

class IpdPainScoreOut(IpdPainScoreCreate):
    id: uuid.UUID
    admission_number: str
    recorded_by_name: Optional[str] = None
    recorded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdNutritionAssessmentCreate(BaseModel):
    bmi: Optional[float] = None
    dietary_habits: Optional[str] = None
    appetite_status: Optional[str] = None
    malnutrition_risk: Optional[str] = None

class IpdNutritionAssessmentOut(IpdNutritionAssessmentCreate):
    id: uuid.UUID
    admission_number: str
    dietician_notified: bool = False
    assessed_by_name: Optional[str] = None
    assessed_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class IpdNursingObservationCreate(BaseModel):
    observation_type: str = "General"
    note: str

class IpdNursingObservationOut(IpdNursingObservationCreate):
    id: uuid.UUID
    admission_number: str
    recorded_by_name: Optional[str] = None
    recorded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

# --- Phase 17: Doctor Coversheet & Clinical Documentation ---

class IpdDoctorWorklistOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    doctor_uuid: uuid.UUID
    doctor_name: str
    assigned_at: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

class IpdDoctorCoversheetUpdate(BaseModel):
    primary_diagnosis: Optional[str] = None
    clinical_summary: Optional[str] = None

class IpdDoctorCoversheetOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    primary_diagnosis: Optional[str] = None
    clinical_summary: Optional[str] = None
    verified_by_doctor: Optional[str] = None
    verified_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class IpdDiagnosisCreate(BaseModel):
    diagnosis_type: str  # Provisional, Confirmed, Secondary
    icd10_code: Optional[str] = None
    description: str

class IpdDiagnosisOut(IpdDiagnosisCreate):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    diagnosed_by_name: str
    diagnosed_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdTreatmentPlanCreate(BaseModel):
    therapy_type: str  # Medication, Procedure, Investigation, Supportive
    instructions: str

class IpdTreatmentPlanOut(IpdTreatmentPlanCreate):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    created_by_name: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdProgressNoteCreate(BaseModel):
    notes: str

class IpdProgressNoteOut(IpdProgressNoteCreate):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    doctor_name: str
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdClinicalProcedureCreate(BaseModel):
    procedure_name: str
    procedure_date: datetime
    notes: Optional[str] = None

class IpdClinicalProcedureOut(IpdClinicalProcedureCreate):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    performing_doctor: str
    model_config = ConfigDict(from_attributes=True)

class IpdConsultationRequestCreate(BaseModel):
    consulting_department: str
    reason_for_referral: str
    urgency_level: str = "Routine"

class IpdConsultationRequestOut(IpdConsultationRequestCreate):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    requested_by: str
    requested_at: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

# --- Phase 18: IPD Clinical Orders Management Engine ---

class IpdOrderCreate(BaseModel):
    order_type: str  # Laboratory, Radiology, Medication, Procedure, Nursing
    priority: str = "Routine"  # Routine, Urgent, STAT
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None

class IpdOrderOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    doctor_uuid: Optional[uuid.UUID] = None
    doctor_name: str
    order_type: str
    priority: str
    order_date: datetime
    status: str
    is_recurring: bool
    recurrence_pattern: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class IpdLabOrderCreate(BaseModel):
    test_name: str
    sample_type: Optional[str] = None
    clinical_indication: Optional[str] = None
    priority: str = "Routine"

class IpdLabOrderOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    test_name: str
    sample_type: Optional[str] = None
    clinical_indication: Optional[str] = None
    result_status: str
    model_config = ConfigDict(from_attributes=True)

class IpdRadiologyOrderCreate(BaseModel):
    imaging_type: str  # X-Ray, Ultrasound, CT Scan, MRI
    target_area: str
    clinical_indication: Optional[str] = None
    priority: str = "Routine"

class IpdRadiologyOrderOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    imaging_type: str
    target_area: str
    clinical_indication: Optional[str] = None
    report_status: str
    model_config = ConfigDict(from_attributes=True)

class IpdMedicationOrderCreate(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str  # OD, BID, TID, QID
    route: str  # Oral, IV, IM, SC
    duration_days: Optional[int] = None
    priority: str = "Routine"

class IpdMedicationOrderOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    medicine_name: str
    dosage: str
    frequency: str
    route: str
    duration_days: Optional[int] = None
    pharmacy_status: str
    model_config = ConfigDict(from_attributes=True)

class IpdProcedureOrderCreate(BaseModel):
    procedure_service_name: str
    department: str
    scheduling_notes: Optional[str] = None
    priority: str = "Routine"

class IpdProcedureOrderOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    procedure_service_name: str
    department: str
    scheduling_notes: Optional[str] = None
    execution_status: str
    model_config = ConfigDict(from_attributes=True)

class IpdOrderStatusUpdate(BaseModel):
    new_status: str
    remarks: Optional[str] = None

class IpdOrderStatusLogOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    previous_status: Optional[str] = None
    new_status: str
    updated_by: str
    updated_at: datetime
    remarks: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class IpdOrderDetailOut(BaseModel):
    order: IpdOrderOut
    lab_detail: Optional[IpdLabOrderOut] = None
    radiology_detail: Optional[IpdRadiologyOrderOut] = None
    medication_detail: Optional[IpdMedicationOrderOut] = None
    procedure_detail: Optional[IpdProcedureOrderOut] = None
    status_logs: list[IpdOrderStatusLogOut] = []

# --- Phase 19: IPD Bed Transfer & Patient Movement Engine ---

class IpdTransferHandoverCreate(BaseModel):
    identification: Optional[str] = None
    situation: str
    background: str
    assessment: str
    recommendation: str

class IpdTransferHandoverOut(BaseModel):
    id: uuid.UUID
    transfer_request_id: uuid.UUID
    admission_number: str
    identification: Optional[str] = None
    situation: str
    background: str
    assessment: str
    recommendation: str
    documented_by: str
    documented_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdTransferRequestCreate(BaseModel):
    current_ward: str
    current_bed: str
    requested_ward: str
    requested_bed_category: Optional[str] = None
    reason: str
    transfer_type: str = "Ward-to-Ward"
    priority: str = "Routine"
    handover: Optional[IpdTransferHandoverCreate] = None

class IpdTransferAuditLogOut(BaseModel):
    id: uuid.UUID
    action: str
    performed_by: str
    performed_at: datetime
    details: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class IpdTransferRequestOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    current_ward: str
    current_bed: str
    requested_ward: str
    requested_bed_category: Optional[str] = None
    requested_bed: Optional[str] = None
    reason: str
    transfer_type: str
    priority: str
    requested_by: str
    requested_at: datetime
    status: str
    handover: Optional[IpdTransferHandoverOut] = None
    audit_logs: list[IpdTransferAuditLogOut] = []
    model_config = ConfigDict(from_attributes=True)

class IpdTransferApproval(BaseModel):
    approved_bed: str
    remarks: Optional[str] = None

class IpdBedMovementOut(BaseModel):
    id: uuid.UUID
    admission_number: str
    patient_uhid: str
    previous_ward: Optional[str] = None
    previous_bed: Optional[str] = None
    new_ward: str
    new_bed: str
    movement_reason: str
    moved_at: datetime
    recorded_by: str
    model_config = ConfigDict(from_attributes=True)

# --- Phase 20: IPD Smart Discharge Planning Engine ---

class IpdDischargePlanCreate(BaseModel):
    planned_discharge_date: Optional[datetime] = None

class IpdDischargePlanOut(BaseModel):
    id: UUID
    admission_number: str
    patient_uhid: str
    doctor_uuid: Optional[str] = None
    planned_discharge_date: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdDischargeChecklistUpdate(BaseModel):
    doctor_approval: Optional[bool] = None
    nursing_clearance: Optional[bool] = None
    medications_reconciled: Optional[bool] = None
    final_investigations_checked: Optional[bool] = None
    patient_counseling: Optional[bool] = None
    billing_clearance: Optional[bool] = None

class IpdDischargeChecklistOut(BaseModel):
    id: UUID
    admission_number: str
    patient_uhid: str
    doctor_approval: bool
    nursing_clearance: bool
    medications_reconciled: bool
    final_investigations_checked: bool
    patient_counseling: bool
    billing_clearance: bool
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdDischargeSummaryCreate(BaseModel):
    admission_diagnosis: Optional[str] = None
    hospital_course: Optional[str] = None
    procedures_performed: Optional[str] = None
    medications_prescribed: Optional[str] = None
    follow_up_instructions: Optional[str] = None

class IpdDischargeSummaryOut(BaseModel):
    id: UUID
    admission_number: str
    patient_uhid: str
    doctor_uuid: Optional[str] = None
    admission_diagnosis: Optional[str] = None
    hospital_course: Optional[str] = None
    procedures_performed: Optional[str] = None
    medications_prescribed: Optional[str] = None
    follow_up_instructions: Optional[str] = None
    status: str
    created_at: datetime
    finalized_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class IpdDischargeNoteCreate(BaseModel):
    patient_condition: str
    instructions_given: str
    wound_care_guidance: Optional[str] = None

class IpdDischargeNoteOut(BaseModel):
    id: UUID
    admission_number: str
    nurse_uuid: Optional[str] = None
    patient_condition: str
    instructions_given: str
    wound_care_guidance: Optional[str] = None
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdDischargeNotificationOut(BaseModel):
    id: UUID
    admission_number: str
    department: str
    message: str
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdDischargeAuditLogOut(BaseModel):
    id: UUID
    admission_number: str
    action: str
    performed_by: str
    performed_at: datetime
    details: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# --- Phase 21: IPD Billing & Payment Settlement Engine ---

class IpdBillingMasterOut(BaseModel):
    id: UUID
    admission_number: str
    patient_uhid: str
    patient_name: str
    ward_name: Optional[str] = None
    bed_code: Optional[str] = None
    total_charges: float
    total_deposits: float
    total_discount: float
    total_tax: float
    insurance_payable: float
    patient_payable: float
    total_paid: float
    outstanding_balance: float
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdBillingServiceCreate(BaseModel):
    service_category: str
    service_name: str
    quantity: int = 1
    unit_price: float
    notes: Optional[str] = None

class IpdBillingServiceOut(BaseModel):
    id: UUID
    admission_number: str
    service_category: str
    service_name: str
    service_date: datetime
    quantity: int
    unit_price: float
    total_price: float
    source_order_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdBillingDepositCreate(BaseModel):
    amount: float
    payment_mode: str
    reference_number: Optional[str] = None

class IpdBillingDepositOut(BaseModel):
    id: UUID
    admission_number: str
    patient_uhid: str
    amount: float
    payment_mode: str
    receipt_number: Optional[str] = None
    reference_number: Optional[str] = None
    collected_by: Optional[str] = None
    deposit_date: datetime
    status: str
    model_config = ConfigDict(from_attributes=True)

class IpdInsuranceClaimCreate(BaseModel):
    insurance_provider: str
    policy_number: str
    pre_auth_number: Optional[str] = None
    coverage_limit: float = 0.0
    claimed_amount: float = 0.0

class IpdInsuranceClaimApprove(BaseModel):
    approved_amount: float
    patient_share: float = 0.0
    status: str = "Approved"

class IpdInsuranceClaimOut(BaseModel):
    id: UUID
    admission_number: str
    patient_uhid: str
    insurance_provider: str
    policy_number: str
    pre_auth_number: Optional[str] = None
    coverage_limit: float
    claimed_amount: float
    approved_amount: float
    patient_share: float
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdPaymentCreate(BaseModel):
    amount: float
    payment_mode: str
    reference_number: Optional[str] = None

class IpdPaymentOut(BaseModel):
    id: UUID
    admission_number: str
    patient_uhid: str
    amount: float
    payment_mode: str
    reference_number: Optional[str] = None
    receipt_number: Optional[str] = None
    payment_type: str
    processed_by: Optional[str] = None
    payment_date: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdRefundCreate(BaseModel):
    refund_amount: float
    refund_mode: str
    refund_reason: Optional[str] = None

class IpdRefundOut(BaseModel):
    id: UUID
    admission_number: str
    patient_uhid: str
    refund_amount: float
    refund_mode: str
    refund_reason: Optional[str] = None
    approved_by: Optional[str] = None
    processed_by: Optional[str] = None
    status: str
    refund_date: datetime
    model_config = ConfigDict(from_attributes=True)


# Phase 22: Visitor Management & Medico-Legal Case (MLC) Handling

class IpdVisitorBase(BaseModel):
    admission_number: str
    patient_uhid: str
    visitor_name: str
    relationship: str
    contact_number: str
    id_proof: str

class IpdVisitorCreate(IpdVisitorBase):
    pass

class IpdVisitorOut(IpdVisitorBase):
    id: UUID
    registered_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdVisitorPassBase(BaseModel):
    visitor_id: UUID
    admission_number: str
    ward_name: str
    pass_type: str = "Standard"

class IpdVisitorPassCreate(IpdVisitorPassBase):
    generated_by: Optional[str] = None

class IpdVisitorPassOut(IpdVisitorPassBase):
    id: UUID
    pass_number: str
    visit_date: date
    status: str
    generated_by: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdVisitorLogCreate(BaseModel):
    pass_number: str
    checkpoint: str
    security_guard_id: Optional[str] = None

class IpdVisitorLogOut(BaseModel):
    id: UUID
    pass_number: str
    entry_time: datetime
    exit_time: Optional[datetime]
    checkpoint: str
    security_guard_id: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class IpdMlcCaseBase(BaseModel):
    admission_number: str
    patient_uhid: str
    case_type: str
    incident_details: Optional[str] = None
    police_station: Optional[str] = None
    fir_number: Optional[str] = None
    officer_name: Optional[str] = None
    officer_badge: Optional[str] = None

class IpdMlcCaseCreate(IpdMlcCaseBase):
    registered_by: str

class IpdMlcCaseUpdate(BaseModel):
    status: Optional[str] = None
    police_station: Optional[str] = None
    fir_number: Optional[str] = None
    officer_name: Optional[str] = None
    officer_badge: Optional[str] = None

class IpdMlcCaseOut(IpdMlcCaseBase):
    id: UUID
    registered_by: str
    status: str
    registered_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdMlcDocumentBase(BaseModel):
    mlc_id: UUID
    document_type: str
    file_url: str

class IpdMlcDocumentCreate(IpdMlcDocumentBase):
    uploaded_by: str

class IpdMlcDocumentOut(IpdMlcDocumentBase):
    id: UUID
    uploaded_by: str
    uploaded_at: datetime
    model_config = ConfigDict(from_attributes=True)

class IpdSecurityNotificationBase(BaseModel):
    admission_number: str
    notification_type: str
    message: str

class IpdSecurityNotificationCreate(IpdSecurityNotificationBase):
    pass

class IpdSecurityNotificationOut(IpdSecurityNotificationBase):
    id: UUID
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
