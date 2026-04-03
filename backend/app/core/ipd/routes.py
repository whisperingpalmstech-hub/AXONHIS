from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from app.database import get_db
from app.dependencies import CurrentUser

from .schemas import (
    IpdAdmissionRequestCreate, IpdAdmissionRequestOut,
    IpdAdmissionRecordOut, DashboardStats,
    IpdCostEstimationCreate, IpdCostEstimationOut,
    IpdAdmissionChecklistUpdate, IpdAdmissionChecklistOut,
    IpdInsuranceDetailsCreate, IpdInsuranceDetailsOut,
    IpdProjectedBillOut, IpdDepositRecordCreate, IpdDepositRecordOut,
    IpdPatientTransportCreate, IpdPatientTransportOut,
    IpdNursingWorklistOut, IpdNursingCoversheetCreate,
    IpdNursingCoversheetOut, IpdNursingNoteCreate,
    IpdNursingNoteOut, IpdCareAssignmentCreate,
    IpdCareAssignmentOut, IpdPatientStatusMonitorOut,
    IpdVitalsRecordCreate, IpdVitalsRecordOut,
    IpdNursingAssessmentCreate, IpdNursingAssessmentOut,
    IpdRiskAssessmentCreate, IpdRiskAssessmentOut,
    IpdPainScoreCreate, IpdPainScoreOut,
    IpdNutritionAssessmentCreate, IpdNutritionAssessmentOut,
    IpdNursingObservationCreate, IpdNursingObservationOut,
    IpdDoctorWorklistOut, IpdDoctorCoversheetUpdate, IpdDoctorCoversheetOut,
    IpdDiagnosisCreate, IpdDiagnosisOut,
    IpdTreatmentPlanCreate, IpdTreatmentPlanOut,
    IpdProgressNoteCreate, IpdProgressNoteOut,
    IpdClinicalProcedureCreate, IpdClinicalProcedureOut,
    IpdConsultationRequestCreate, IpdConsultationRequestOut,
    IpdLabOrderCreate, IpdLabOrderOut,
    IpdRadiologyOrderCreate, IpdRadiologyOrderOut,
    IpdMedicationOrderCreate, IpdMedicationOrderOut,
    IpdProcedureOrderCreate, IpdProcedureOrderOut,
    IpdOrderOut, IpdOrderDetailOut,
    IpdOrderStatusUpdate, IpdOrderStatusLogOut,
    IpdTransferRequestCreate, IpdTransferRequestOut, IpdTransferApproval,
    IpdDischargePlanCreate, IpdDischargePlanOut,
    IpdDischargeChecklistUpdate, IpdDischargeChecklistOut,
    IpdDischargeSummaryCreate, IpdDischargeSummaryOut,
    IpdDischargeNoteCreate, IpdDischargeNoteOut,
    IpdBillingMasterOut, IpdBillingServiceCreate, IpdBillingServiceOut,
    IpdBillingDepositCreate, IpdBillingDepositOut,
    IpdInsuranceClaimCreate, IpdInsuranceClaimOut, IpdInsuranceClaimApprove,
    IpdPaymentCreate, IpdPaymentOut, IpdRefundCreate, IpdRefundOut,
    IpdVisitorCreate, IpdVisitorOut, IpdVisitorPassCreate, IpdVisitorPassOut,
    IpdVisitorLogCreate, IpdVisitorLogOut,
    IpdMlcCaseCreate, IpdMlcCaseOut, IpdMlcCaseUpdate,
    IpdMlcDocumentCreate, IpdMlcDocumentOut,
    IpdSecurityNotificationOut,
    PatientSearchResult,
    IpdNextOfKinCreate, IpdNextOfKinOut,
    IpdDiscountRequestCreate, IpdDiscountApproval, IpdDiscountRequestOut,
    IpdCreditNoteCreate, IpdCreditNoteOut,
    IpdIntermediateBillOut,
    IpdConsentTemplateCreate, IpdConsentTemplateOut,
    IpdCorporateAccountCreate, IpdCorporateAccountOut,
    IpdRefundProcessCreate, IpdRefundProcessOut,
    DashboardStatsExtended,
)
from .services import IPDService

router = APIRouter(prefix="/ipd", tags=["IPD Admission & Bed Management"])

# --- Dashboard ---
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    service = IPDService(db, org_id=current_user.org_id if current_user else None)
    return await service.get_dashboard_stats()

# --- Admission Requests ---
@router.post("/requests", response_model=IpdAdmissionRequestOut)
async def create_admission_request(req: IpdAdmissionRequestCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    service = IPDService(db, org_id=current_user.org_id if current_user else None)
    new_req = await service.create_admission_request(req.model_dump(), current_user.id if current_user else None)
    await db.commit()
    await db.refresh(new_req)
    return new_req

@router.get("/requests/pending", response_model=List[IpdAdmissionRequestOut])
async def list_pending_requests(db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    service = IPDService(db, org_id=current_user.org_id if current_user else None)
    return await service.get_pending_requests()

@router.put("/requests/{req_id}/status", response_model=IpdAdmissionRequestOut)
async def update_request_status(req_id: UUID, new_status: str, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    service = IPDService(db, org_id=current_user.org_id if current_user else None)
    updated_req = await service.update_request_status(req_id, new_status, current_user.id if current_user else None)
    if not updated_req:
        raise HTTPException(status_code=404, detail="Request not found")
    await db.commit()
    return updated_req

# --- Allocation ---
@router.post("/requests/{req_id}/allocate/{bed_id}", response_model=IpdAdmissionRecordOut)
async def allocate_bed(req_id: UUID, bed_id: str, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    service = IPDService(db, org_id=current_user.org_id if current_user else None)
    adm = await service.allocate_bed(req_id, bed_id, current_user.id if current_user else None)
    if not adm:
        raise HTTPException(status_code=400, detail="Cannot allocate bed. Request must be approved and bed must be available.")
    await db.commit()
    return adm

@router.get("/admissions", response_model=list[IpdAdmissionRecordOut])
async def get_active_admissions(db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    service = IPDService(db, org_id=current_user.org_id if current_user else None)
    return await service.get_active_admissions()

# --- Phase 14: Smart Admission ---
@router.post("/requests/{req_id}/estimate", response_model=IpdCostEstimationOut)
async def generate_cost_estimate(req_id: UUID, est: IpdCostEstimationCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    new_est = await service.generate_cost_estimate(req_id, est.model_dump())
    await db.commit()
    return new_est

@router.get("/admissions/{adm_no}/checklist", response_model=IpdAdmissionChecklistOut)
async def get_checklist(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    cl = await service.get_checklist(adm_no)
    if not cl:
        raise HTTPException(status_code=404, detail="Checklist not found")
    return cl

@router.put("/admissions/{adm_no}/checklist", response_model=IpdAdmissionChecklistOut)
async def update_checklist(adm_no: str, data: IpdAdmissionChecklistUpdate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    cl = await service.update_checklist(adm_no, data.model_dump(exclude_unset=True))
    if not cl:
        raise HTTPException(status_code=404, detail="Checklist not found")
    await db.commit()
    return cl

@router.post("/admissions/{adm_no}/insurance", response_model=IpdInsuranceDetailsOut)
async def save_insurance(adm_no: str, data: IpdInsuranceDetailsCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    ins = await service.save_insurance(adm_no, data.model_dump())
    await db.commit()
    return ins

@router.get("/admissions/{adm_no}/bill", response_model=IpdProjectedBillOut)
async def get_projected_bill(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    bill = await service.get_projected_bill(adm_no)
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    return bill

@router.post("/admissions/{adm_no}/deposit", response_model=IpdDepositRecordOut)
async def collect_deposit(adm_no: str, data: IpdDepositRecordCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    dep = await service.collect_deposit(adm_no, data.model_dump())
    await db.commit()
    return dep

@router.post("/admissions/{adm_no}/transport", response_model=IpdPatientTransportOut)
async def request_transport(adm_no: str, data: IpdPatientTransportCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    req = await service.request_transport(adm_no, data.model_dump())
    await db.commit()
    return req

# --- Phase 15: Nursing Coversheet & Patient Acceptance ---

@router.get("/nursing/worklist", response_model=list[IpdNursingWorklistOut])
async def get_nursing_worklist(db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_nursing_worklist()

@router.post("/nursing/coversheets", response_model=IpdNursingCoversheetOut)
async def accept_patient(data: IpdNursingCoversheetCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    service = IPDService(db)
    user_id = getattr(current_user, "id", None) if current_user else None
    user_name = getattr(current_user, "email", "Nurse User") if current_user else "Nurse User"
    
    coversheet = await service.accept_patient(data.admission_number, data.priority_status, str(user_id) if user_id else "00000000-0000-0000-0000-000000000000", user_name)
    await db.commit()
    return coversheet

@router.post("/nursing/notes", response_model=IpdNursingNoteOut)
async def add_nursing_note(admission_number: str, data: IpdNursingNoteCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    service = IPDService(db)
    user_id = getattr(current_user, "id", None) if current_user else None
    user_name = getattr(current_user, "email", "Nurse User") if current_user else "Nurse User"
    
    note = await service.add_nursing_note(
        admission_number=admission_number,
        note_type=data.note_type,
        clinical_note=data.clinical_note,
        user_id=str(user_id) if user_id else "00000000-0000-0000-0000-000000000000",
        user_name=user_name
    )
    await db.commit()
    return note

@router.post("/nursing/assignments", response_model=IpdCareAssignmentOut)
async def assign_nursing_care(admission_number: str, data: IpdCareAssignmentCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    assignment = await service.assign_nursing_care(admission_number, data.model_dump())
    await db.commit()
    return assignment

# --- Phase 16: Nursing Assessment & Vitals Monitoring ---

@router.post("/vitals/{adm_no}", response_model=IpdVitalsRecordOut)
async def record_vitals(adm_no: str, data: IpdVitalsRecordCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    vitals = await service.record_vitals(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return vitals

@router.get("/vitals/{adm_no}", response_model=list[IpdVitalsRecordOut])
async def get_vitals_history(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_vitals_history(adm_no)

@router.post("/assessments/{adm_no}", response_model=IpdNursingAssessmentOut)
async def save_nursing_assessment(adm_no: str, data: IpdNursingAssessmentCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    assessment = await service.save_nursing_assessment(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return assessment

@router.get("/assessments/{adm_no}", response_model=IpdNursingAssessmentOut)
async def get_nursing_assessment(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    assessment = await service.get_nursing_assessment(adm_no)
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment

@router.post("/risks/{adm_no}", response_model=IpdRiskAssessmentOut)
async def add_risk_assessment(adm_no: str, data: IpdRiskAssessmentCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    risk = await service.add_risk_assessment(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return risk

@router.get("/risks/{adm_no}", response_model=list[IpdRiskAssessmentOut])
async def get_risk_assessments(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_risk_assessments(adm_no)

@router.post("/pain/{adm_no}", response_model=IpdPainScoreOut)
async def add_pain_score(adm_no: str, data: IpdPainScoreCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    ps = await service.add_pain_score(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return ps

@router.post("/nutrition/{adm_no}", response_model=IpdNutritionAssessmentOut)
async def add_nutrition_assessment(adm_no: str, data: IpdNutritionAssessmentCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    na = await service.add_nutrition_assessment(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return na

@router.post("/observations/{adm_no}", response_model=IpdNursingObservationOut)
async def add_observation(adm_no: str, data: IpdNursingObservationCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    obs = await service.add_observation(adm_no, data.model_dump())
    await db.commit()
    return obs

# --- Phase 17: Doctor Coversheet & Clinical Documentation ---

@router.get("/doctor/worklist", response_model=list[IpdDoctorWorklistOut])
async def get_doctor_worklist(db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    res = await service.get_doctor_worklist()
    await db.commit()
    return res

@router.get("/doctor/coversheet/{adm_no}", response_model=IpdDoctorCoversheetOut)
async def get_doctor_coversheet(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    cs = await service.get_doctor_coversheet(adm_no)
    if not cs:
        raise HTTPException(status_code=404, detail="Coversheet not found")
    return cs

@router.put("/doctor/coversheet/{adm_no}", response_model=IpdDoctorCoversheetOut)
async def update_doctor_coversheet(adm_no: str, data: IpdDoctorCoversheetUpdate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    cs = await service.update_doctor_coversheet(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return cs

@router.get("/doctor/diagnoses/{adm_no}", response_model=list[IpdDiagnosisOut])
async def get_diagnoses(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_diagnoses(adm_no)

@router.post("/doctor/diagnoses/{adm_no}", response_model=IpdDiagnosisOut)
async def add_diagnosis(adm_no: str, data: IpdDiagnosisCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    diag = await service.add_diagnosis(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return diag

@router.get("/doctor/treatment-plans/{adm_no}", response_model=list[IpdTreatmentPlanOut])
async def get_treatment_plans(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_treatment_plans(adm_no)

@router.post("/doctor/treatment-plans/{adm_no}", response_model=IpdTreatmentPlanOut)
async def add_treatment_plan(adm_no: str, data: IpdTreatmentPlanCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    tp = await service.add_treatment_plan(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return tp

@router.get("/doctor/progress-notes/{adm_no}", response_model=list[IpdProgressNoteOut])
async def get_progress_notes(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_progress_notes(adm_no)

@router.post("/doctor/progress-notes/{adm_no}", response_model=IpdProgressNoteOut)
async def add_progress_note(adm_no: str, data: IpdProgressNoteCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    note = await service.add_progress_note(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return note

@router.get("/doctor/clinical-procedures/{adm_no}", response_model=list[IpdClinicalProcedureOut])
async def get_clinical_procedures(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_clinical_procedures(adm_no)

@router.post("/doctor/clinical-procedures/{adm_no}", response_model=IpdClinicalProcedureOut)
async def add_clinical_procedure(adm_no: str, data: IpdClinicalProcedureCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    proc = await service.add_clinical_procedure(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return proc

@router.get("/doctor/consultation-requests/{adm_no}", response_model=list[IpdConsultationRequestOut])
async def get_consultation_requests(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_consultation_requests(adm_no)

@router.post("/doctor/consultation-requests/{adm_no}", response_model=IpdConsultationRequestOut)
async def add_consultation_request(adm_no: str, data: IpdConsultationRequestCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    cr = await service.add_consultation_request(adm_no, data.model_dump(exclude_none=True))
    await db.commit()
    return cr

@router.get("/observations/{adm_no}", response_model=list[IpdNursingObservationOut])
async def get_observations(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_observations(adm_no)

# --- Phase 18: IPD Clinical Orders Management Engine ---

@router.post("/orders/lab/{adm_no}", response_model=IpdOrderOut)
async def create_lab_order(adm_no: str, data: IpdLabOrderCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.create_lab_order(adm_no, data.model_dump())
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result["order"]

@router.post("/orders/radiology/{adm_no}", response_model=IpdOrderOut)
async def create_radiology_order(adm_no: str, data: IpdRadiologyOrderCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.create_radiology_order(adm_no, data.model_dump())
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result["order"]

@router.post("/orders/medication/{adm_no}", response_model=IpdOrderOut)
async def create_medication_order(adm_no: str, data: IpdMedicationOrderCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.create_medication_order(adm_no, data.model_dump())
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result["order"]

@router.post("/orders/procedure/{adm_no}", response_model=IpdOrderOut)
async def create_procedure_order(adm_no: str, data: IpdProcedureOrderCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.create_procedure_order(adm_no, data.model_dump())
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result["order"]

@router.get("/orders/{adm_no}", response_model=list[IpdOrderOut])
async def get_patient_orders(adm_no: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_patient_orders(adm_no)

@router.get("/orders/detail/{order_id}", response_model=IpdOrderDetailOut)
async def get_order_detail(order_id: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.get_order_detail(order_id)
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    return result

@router.put("/orders/status/{order_id}", response_model=IpdOrderOut)
async def update_order_status(order_id: str, data: IpdOrderStatusUpdate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.update_order_status(order_id, data.new_status, remarks=data.remarks)
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    await db.commit()
    return result

@router.get("/orders-nursing/execution-worklist", response_model=list[IpdOrderOut])
async def get_nursing_execution_worklist(db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_nursing_execution_worklist()

# --- Phase 19: IPD Bed Transfer & Patient Movement Engine ---

@router.post("/transfers/{admission_number}", response_model=IpdTransferRequestOut)
async def create_transfer_request(admission_number: str, data: IpdTransferRequestCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.create_transfer_request(admission_number, data.model_dump())
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result

@router.get("/transfers/list", response_model=List[IpdTransferRequestOut])
async def get_transfer_requests(ward: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.get_transfer_requests(ward)

@router.get("/transfers/detail/{req_id}", response_model=dict)
async def get_transfer_detail(req_id: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.get_transfer_request_detail(req_id)
    if not result:
        raise HTTPException(status_code=404, detail="Transfer Request not found")
    return result

@router.put("/transfers/{req_id}/approve", response_model=IpdTransferRequestOut)
async def approve_transfer(req_id: str, data: IpdTransferApproval, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.approve_transfer_request(req_id, data.approved_bed, user_name="Bed Manager", remarks=data.remarks)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot approve transfer")
    await db.commit()
    return result

@router.put("/transfers/{req_id}/reject", response_model=IpdTransferRequestOut)
async def reject_transfer(req_id: str, remarks: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.reject_transfer_request(req_id, user_name="Bed Manager", remarks=remarks)
    if not result:
        raise HTTPException(status_code=400, detail="Cannot reject transfer")
    await db.commit()
    return result

# --- Phase 20: IPD Smart Discharge Planning Engine ---

@router.get("/discharge/{admission_number}")
async def get_discharge_state(admission_number: str, db: AsyncSession = Depends(get_db)):
    try:
        service = IPDService(db)
        result = await service.get_or_create_discharge_state(admission_number)
        if not result:
            raise HTTPException(status_code=404, detail="Admission not found")
        
        return {
            "plan": IpdDischargePlanOut.model_validate(result["plan"]).model_dump(mode='json'),
            "checklist": IpdDischargeChecklistOut.model_validate(result["checklist"]).model_dump(mode='json'),
            "summary": IpdDischargeSummaryOut.model_validate(result["summary"]).model_dump(mode='json')
        }
    except Exception as e:
        import traceback
        raise HTTPException(status_code=400, detail=str(traceback.format_exc()))

@router.put("/discharge/{admission_number}/plan", response_model=IpdDischargePlanOut)
async def update_discharge_plan(admission_number: str, data: IpdDischargePlanCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.update_discharge_plan(admission_number, data.model_dump(exclude_unset=True), user_name="Doctor")
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result

@router.put("/discharge/{admission_number}/checklist", response_model=IpdDischargeChecklistOut)
async def update_discharge_checklist(admission_number: str, data: IpdDischargeChecklistUpdate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.update_discharge_checklist(admission_number, data.model_dump(exclude_unset=True), user_name="Clinical Staff")
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result

@router.post("/discharge/{admission_number}/summary/generate", response_model=IpdDischargeSummaryOut)
async def generate_discharge_summary(admission_number: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.generate_discharge_summary(admission_number, user_name="System Generator")
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result

@router.put("/discharge/{admission_number}/summary", response_model=IpdDischargeSummaryOut)
async def update_discharge_summary(admission_number: str, data: IpdDischargeSummaryCreate, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    result = await service.update_discharge_summary(admission_number, data.model_dump(exclude_unset=True), user_name="Doctor")
    if not result:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return result

@router.get("/discharge/{admission_number}/pending-orders", response_model=list[IpdOrderOut])
async def check_pending_orders(admission_number: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    return await service.validate_pending_orders(admission_number)

@router.post("/discharge/{admission_number}/finalize")
async def finalize_discharge(admission_number: str, db: AsyncSession = Depends(get_db)):
    service = IPDService(db)
    try:
        await service.finalize_discharge(admission_number, user_name="Discharge Manager")
        await db.commit()
        return {"status": "success", "message": "Discharge Finalized."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Phase 21: IPD Billing Endpoints ---

@router.get("/billing/dashboard", response_model=List[IpdBillingMasterOut])
async def get_billing_dashboard(
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    return await ipd_service.get_billing_dashboard()

@router.get("/billing/{admission_number}", response_model=IpdBillingMasterOut)
async def get_billing_master(
    admission_number: str,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    billing = await ipd_service.get_or_create_billing(admission_number)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found for this admission")
    return billing

@router.post("/billing/{admission_number}/recalculate", response_model=IpdBillingMasterOut)
async def recalculate_bill(
    admission_number: str,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    billing = await ipd_service.recalculate_billing(admission_number)
    if not billing:
        raise HTTPException(status_code=404, detail="Billing record not found")
    await db.commit()
    return billing

@router.get("/billing/{admission_number}/services", response_model=List[IpdBillingServiceOut])
async def get_billing_services(
    admission_number: str,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    return await ipd_service.get_billing_services(admission_number)

@router.post("/billing/{admission_number}/services", response_model=IpdBillingServiceOut)
async def add_billing_service(
    admission_number: str,
    data: IpdBillingServiceCreate,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    svc = await ipd_service.add_billing_service(admission_number, data.model_dump(), "System Admin")
    if not svc:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return svc

@router.get("/billing/{admission_number}/deposits", response_model=List[IpdBillingDepositOut])
async def get_billing_deposits(
    admission_number: str,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    return await ipd_service.get_deposits(admission_number)

@router.post("/billing/{admission_number}/deposits", response_model=IpdBillingDepositOut)
async def add_deposit(
    admission_number: str,
    data: IpdBillingDepositCreate,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    dep = await ipd_service.add_deposit(admission_number, data.model_dump(), "System Admin")
    if not dep:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return dep

@router.get("/billing/{admission_number}/insurance", response_model=List[IpdInsuranceClaimOut])
async def get_insurance_claims(
    admission_number: str,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    return await ipd_service.get_insurance_claims(admission_number)

@router.post("/billing/{admission_number}/insurance", response_model=IpdInsuranceClaimOut)
async def add_insurance_claim(
    admission_number: str,
    data: IpdInsuranceClaimCreate,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    claim = await ipd_service.add_insurance_claim(admission_number, data.model_dump(), "System Admin")
    if not claim:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return claim

@router.post("/billing/insurance/{claim_id}/approve", response_model=IpdInsuranceClaimOut)
async def approve_insurance_claim(
    claim_id: UUID,
    data: IpdInsuranceClaimApprove,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    claim = await ipd_service.process_insurance_claim(str(claim_id), data.model_dump(), "System Admin")
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")
    await db.commit()
    return claim

@router.get("/billing/{admission_number}/payments", response_model=List[IpdPaymentOut])
async def get_payments(
    admission_number: str,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    return await ipd_service.get_payments(admission_number)

@router.post("/billing/{admission_number}/payments", response_model=IpdPaymentOut)
async def add_payment(
    admission_number: str,
    data: IpdPaymentCreate,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    pmt = await ipd_service.process_payment(admission_number, data.model_dump(), "System Admin")
    if not pmt:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return pmt

@router.get("/billing/{admission_number}/available-insurance", response_model=List[dict])
async def get_available_insurance(
    admission_number: str,
    db: AsyncSession = Depends(get_db)
):
    ipd_service = IPDService(db)
    return await ipd_service.get_patient_active_insurance(admission_number)

# ─── Phase 22: Visitor Management & MLC Handling ────────────────

@router.post("/visitors", response_model=IpdVisitorOut)
async def register_visitor(data: IpdVisitorCreate, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    visitor = await svc.register_visitor(data.model_dump())
    await db.commit()
    return visitor

@router.get("/visitors/{admission_number}", response_model=List[IpdVisitorOut])
async def get_visitors(admission_number: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_visitors(admission_number)

@router.post("/visitor-passes", response_model=IpdVisitorPassOut)
async def generate_visitor_pass(data: IpdVisitorPassCreate, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    vp = await svc.generate_visitor_pass(data.model_dump())
    await db.commit()
    return vp

@router.get("/visitor-passes/{admission_number}", response_model=List[IpdVisitorPassOut])
async def get_visitor_passes(admission_number: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_visitor_passes(admission_number)

@router.post("/visitor-logs/entry", response_model=IpdVisitorLogOut)
async def log_visitor_entry(data: IpdVisitorLogCreate, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    log = await svc.log_visitor_entry(data.model_dump())
    await db.commit()
    return log

@router.put("/visitor-logs/{log_id}/exit", response_model=IpdVisitorLogOut)
async def log_visitor_exit(log_id: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    log = await svc.log_visitor_exit(log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    await db.commit()
    return log

@router.get("/visitor-logs/{pass_number}", response_model=List[IpdVisitorLogOut])
async def get_visitor_logs(pass_number: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_visitor_logs(pass_number)

@router.post("/mlc", response_model=IpdMlcCaseOut)
async def register_mlc_case(data: IpdMlcCaseCreate, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    mlc = await svc.register_mlc_case(data.model_dump())
    await db.commit()
    return mlc

@router.get("/mlc", response_model=List[IpdMlcCaseOut])
async def get_all_mlc_cases(db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_all_mlc_cases()

@router.get("/mlc/{admission_number}", response_model=IpdMlcCaseOut)
async def get_mlc_case(admission_number: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    mlc = await svc.get_mlc_case(admission_number)
    if not mlc:
        raise HTTPException(status_code=404, detail="MLC case not found")
    return mlc

@router.put("/mlc/{admission_number}", response_model=IpdMlcCaseOut)
async def update_mlc_case(admission_number: str, data: IpdMlcCaseUpdate, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    mlc = await svc.update_mlc_case(admission_number, data.model_dump(exclude_unset=True))
    if not mlc:
        raise HTTPException(status_code=404, detail="MLC case not found")
    await db.commit()
    return mlc

@router.post("/mlc-documents", response_model=IpdMlcDocumentOut)
async def add_mlc_document(data: IpdMlcDocumentCreate, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    doc = await svc.add_mlc_document(data.model_dump())
    await db.commit()
    return doc

@router.get("/mlc-documents/{mlc_id}", response_model=List[IpdMlcDocumentOut])
async def get_mlc_documents(mlc_id: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_mlc_documents(mlc_id)

@router.get("/security-notifications", response_model=List[IpdSecurityNotificationOut])
async def get_security_notifications(read_filter: str = None, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_security_notifications(read_filter)

@router.put("/security-notifications/{notif_id}/read", response_model=IpdSecurityNotificationOut)
async def mark_notification_read(notif_id: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    notif = await svc.mark_notification_read(notif_id)
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.commit()
    return notif


# ─── Phase 23: FRD Gap Closure Routes ──────────────


# --- Patient Search ---
@router.get("/patients/search", response_model=List[PatientSearchResult])
async def search_patients(q: str, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    return await svc.search_patients(q)


# --- Next of Kin ---
@router.post("/admissions/{adm_no}/next-of-kin", response_model=IpdNextOfKinOut)
async def add_next_of_kin(adm_no: str, data: IpdNextOfKinCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    nok = await svc.add_next_of_kin(adm_no, data.model_dump())
    await db.commit()
    return nok

@router.get("/admissions/{adm_no}/next-of-kin", response_model=List[IpdNextOfKinOut])
async def get_next_of_kin(adm_no: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_next_of_kin(adm_no)


# --- Discount Request/Approval ---
@router.post("/billing/{adm_no}/discount-requests", response_model=IpdDiscountRequestOut)
async def create_discount_request(adm_no: str, data: IpdDiscountRequestCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    user_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'email', 'Staff') if current_user else 'Staff'
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    req = await svc.create_discount_request(adm_no, data.model_dump(), str(user_name))
    if not req:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return req

@router.get("/billing/{adm_no}/discount-requests", response_model=List[IpdDiscountRequestOut])
async def get_discount_requests(adm_no: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_discount_requests(adm_no)

@router.post("/billing/discount-requests/{discount_id}/action", response_model=IpdDiscountRequestOut)
async def approve_or_reject_discount(discount_id: str, data: IpdDiscountApproval, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    user_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'email', 'Finance') if current_user else 'Finance'
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    req = await svc.approve_discount(discount_id, data.model_dump(), str(user_name))
    if not req:
        raise HTTPException(status_code=404, detail="Discount request not found or not Pending")
    await db.commit()
    return req


# --- Credit Notes ---
@router.post("/billing/{adm_no}/credit-notes", response_model=IpdCreditNoteOut)
async def create_credit_note(adm_no: str, data: IpdCreditNoteCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    user_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'email', 'Staff') if current_user else 'Staff'
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    cn = await svc.create_credit_note(adm_no, data.model_dump(), str(user_name))
    if not cn:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return cn

@router.get("/billing/{adm_no}/credit-notes", response_model=List[IpdCreditNoteOut])
async def get_credit_notes(adm_no: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_credit_notes(adm_no)


# --- Refunds ---
@router.post("/billing/{adm_no}/refunds", response_model=IpdRefundProcessOut)
async def create_refund(adm_no: str, data: IpdRefundProcessCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    user_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'email', 'Staff') if current_user else 'Staff'
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    refund = await svc.create_refund(adm_no, data.model_dump(), str(user_name))
    if not refund:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return refund

@router.post("/billing/refunds/{refund_id}/approve", response_model=IpdRefundProcessOut)
async def approve_refund(refund_id: str, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    user_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'email', 'Finance') if current_user else 'Finance'
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    refund = await svc.approve_refund(refund_id, str(user_name))
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found or not Pending")
    await db.commit()
    return refund

@router.get("/billing/{adm_no}/refunds", response_model=List[IpdRefundProcessOut])
async def get_refunds(adm_no: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_refunds(adm_no)


# --- Intermediate Bills ---
@router.post("/billing/{adm_no}/intermediate-bill", response_model=IpdIntermediateBillOut)
async def generate_intermediate_bill(adm_no: str, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    user_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'email', 'Staff') if current_user else 'Staff'
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    bill = await svc.generate_intermediate_bill(adm_no, str(user_name))
    if not bill:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return bill

@router.get("/billing/{adm_no}/intermediate-bills", response_model=List[IpdIntermediateBillOut])
async def get_intermediate_bills(adm_no: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    return await svc.get_intermediate_bills(adm_no)


# --- Consent Templates ---
@router.post("/consent-templates", response_model=IpdConsentTemplateOut)
async def create_consent_template(data: IpdConsentTemplateCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    user_name = getattr(current_user, 'full_name', None) or getattr(current_user, 'email', 'Admin') if current_user else 'Admin'
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    tmpl = await svc.create_consent_template(data.model_dump(), str(user_name))
    await db.commit()
    return tmpl

@router.get("/consent-templates", response_model=List[IpdConsentTemplateOut])
async def get_consent_templates(consent_type: str = None, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    return await svc.get_consent_templates(consent_type)


# --- Corporate Accounts ---
@router.post("/billing/{adm_no}/corporate", response_model=IpdCorporateAccountOut)
async def create_corporate_account(adm_no: str, data: IpdCorporateAccountCreate, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    corp = await svc.create_corporate_account(adm_no, data.model_dump())
    if not corp:
        raise HTTPException(status_code=404, detail="Admission not found")
    await db.commit()
    return corp

@router.get("/billing/{adm_no}/corporate", response_model=IpdCorporateAccountOut)
async def get_corporate_account(adm_no: str, db: AsyncSession = Depends(get_db)):
    svc = IPDService(db)
    corp = await svc.get_corporate_account(adm_no)
    if not corp:
        raise HTTPException(status_code=404, detail="No corporate account for this admission")
    return corp


# --- Extended Dashboard ---
@router.get("/dashboard/stats-extended")
async def get_dashboard_stats_extended(db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    return await svc.get_dashboard_stats_extended()


# --- Bed Grid ---
@router.get("/bed-grid")
async def get_bed_grid(ward_type: str = None, status: str = None, db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    return await svc.get_bed_grid(ward_type, status)


# --- Discharged Patients ---
@router.get("/discharged-patients")
async def get_discharged_patients(db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    patients = await svc.get_discharged_patients()
    return [{"admission_number": a.admission_number, "patient_uhid": a.patient_uhid,
             "ward_id": a.ward_id, "bed_number": a.bed_number, "status": a.status,
             "admission_time": str(a.admission_time) if a.admission_time else None,
             "discharge_time": str(a.discharge_time) if a.discharge_time else None,
             } for a in patients]


# --- Pending Discharges ---
@router.get("/pending-discharges")
async def get_pending_discharges(db: AsyncSession = Depends(get_db), current_user: CurrentUser = None):
    svc = IPDService(db, org_id=current_user.org_id if current_user else None)
    plans = await svc.get_pending_discharges()
    return [{"admission_number": p.admission_number, "patient_uhid": p.patient_uhid,
             "planned_discharge_date": str(p.planned_discharge_date) if p.planned_discharge_date else None,
             "status": p.status,
             } for p in plans]
