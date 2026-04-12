"""
AxonHIS MD — FastAPI Routes.

Complete REST API covering all entities in the Unified Clinical Practice + Health ATM Platform:
  Organizations, Facilities, Specialty Profiles, Clinicians, Patients,
  Channels, Appointments, Encounters, Notes, Diagnoses, Service Requests,
  Medication Requests, Devices, Device Results, Observations, Documents,
  Share Grants, Payers, Coverage, Billing, Integration Events, Audit, Dashboard.
"""

import uuid
import secrets
import os
import json
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

from fastapi import APIRouter, Depends, HTTPException, Query, Form, File, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from google.cloud import speech
from google.oauth2 import service_account

from app.database import get_db
from app.core.axonhis_md.models import (
    MdOrganization, MdFacility, MdSpecialtyProfile, MdClinician,
    MdPatient, MdPatientIdentifier, MdConsentProfile, MdChannel,
    MdAppointment, MdEncounter, MdEncounterNote, MdDiagnosis,
    MdServiceRequest, MdMedicationRequest, MdDevice, MdDeviceResult,
    MdObservation, MdDocument, MdShareGrant, MdShareAccessLog,
    MdPayer, MdCoverage, MdBillingInvoice, MdBillingLineItem,
    MdIntegrationEvent, MdAuditEvent,
)
from app.core.axonhis_md.schemas import (
    OrganizationCreate, OrganizationOut,
    FacilityCreate, FacilityOut,
    SpecialtyProfileCreate, SpecialtyProfileOut,
    ClinicianCreate, ClinicianOut,
    PatientCreate, PatientOut,
    ChannelCreate, ChannelOut,
    AppointmentCreate, AppointmentOut,
    EncounterCreate, EncounterOut,
    EncounterNoteCreate, EncounterNoteOut,
    DiagnosisCreate, DiagnosisOut,
    ServiceRequestCreate, ServiceRequestOut,
    MedicationRequestCreate, MedicationRequestOut,
    DeviceCreate, DeviceOut,
    DeviceResultCreate, DeviceResultOut,
    ObservationCreate, ObservationOut,
    DocumentCreate, DocumentOut,
    ShareGrantCreate, ShareGrantOut,
    PayerCreate, PayerOut,
    CoverageCreate, CoverageOut,
    BillingInvoiceCreate, BillingInvoiceOut,
    IntegrationEventCreate, IntegrationEventOut,
    AuditEventOut,
    MdDashboardStats,
)

router = APIRouter(prefix="/md", tags=["AxonHIS MD — Unified Clinical Platform"])


# ═══════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/dashboard/stats", response_model=MdDashboardStats)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """Aggregate KPIs for the AxonHIS MD module."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)

    orgs = (await db.execute(select(func.count(MdOrganization.organization_id)))).scalar() or 0
    facs = (await db.execute(select(func.count(MdFacility.facility_id)))).scalar() or 0
    clinicians = (await db.execute(select(func.count(MdClinician.clinician_id)))).scalar() or 0
    patients = (await db.execute(select(func.count(MdPatient.patient_id)))).scalar() or 0
    appts = (await db.execute(select(func.count(MdAppointment.appointment_id)))).scalar() or 0
    appts_today = (await db.execute(
        select(func.count(MdAppointment.appointment_id)).where(
            and_(MdAppointment.slot_start >= today_start, MdAppointment.slot_start < today_end)
        )
    )).scalar() or 0
    open_enc = (await db.execute(
        select(func.count(MdEncounter.encounter_id)).where(MdEncounter.encounter_status == "OPEN")
    )).scalar() or 0
    total_enc = (await db.execute(select(func.count(MdEncounter.encounter_id)))).scalar() or 0
    pending_sr = (await db.execute(
        select(func.count(MdServiceRequest.service_request_id)).where(MdServiceRequest.status == "ORDERED")
    )).scalar() or 0
    devices = (await db.execute(select(func.count(MdDevice.device_id)))).scalar() or 0
    docs = (await db.execute(select(func.count(MdDocument.document_id)))).scalar() or 0
    shares = (await db.execute(
        select(func.count(MdShareGrant.share_grant_id)).where(MdShareGrant.revoked_at.is_(None))
    )).scalar() or 0
    invoices = (await db.execute(select(func.count(MdBillingInvoice.billing_invoice_id)))).scalar() or 0
    draft_inv = (await db.execute(
        select(func.count(MdBillingInvoice.billing_invoice_id)).where(MdBillingInvoice.status == "DRAFT")
    )).scalar() or 0
    pending_ie = (await db.execute(
        select(func.count(MdIntegrationEvent.integration_event_id)).where(MdIntegrationEvent.event_status == "PENDING")
    )).scalar() or 0
    specs = (await db.execute(select(func.count(MdSpecialtyProfile.specialty_profile_id)))).scalar() or 0

    return MdDashboardStats(
        total_organizations=orgs, total_facilities=facs, total_clinicians=clinicians,
        total_patients=patients, total_appointments=appts, appointments_today=appts_today,
        open_encounters=open_enc, total_encounters=total_enc,
        pending_service_requests=pending_sr, total_devices=devices,
        total_documents=docs, active_share_grants=shares,
        total_invoices=invoices, draft_invoices=draft_inv,
        pending_integration_events=pending_ie, total_specialties=specs,
    )


# ═══════════════════════════════════════════════════════════════════════════
# ORGANIZATIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/organizations", response_model=List[OrganizationOut])
async def list_organizations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MdOrganization).order_by(MdOrganization.name))
    return result.scalars().all()

@router.post("/organizations", response_model=OrganizationOut, status_code=201)
async def create_organization(body: OrganizationCreate, db: AsyncSession = Depends(get_db)):
    org = MdOrganization(**body.model_dump())
    db.add(org)
    await db.commit()
    await db.refresh(org)
    return org

@router.get("/organizations/{org_id}", response_model=OrganizationOut)
async def get_organization(org_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    org = await db.get(MdOrganization, org_id)
    if not org:
        raise HTTPException(404, "Organization not found")
    return org


# ═══════════════════════════════════════════════════════════════════════════
# FACILITIES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/facilities", response_model=List[FacilityOut])
async def list_facilities(org_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    q = select(MdFacility)
    if org_id:
        q = q.where(MdFacility.organization_id == org_id)
    result = await db.execute(q.order_by(MdFacility.name))
    return result.scalars().all()

@router.post("/facilities", response_model=FacilityOut, status_code=201)
async def create_facility(body: FacilityCreate, db: AsyncSession = Depends(get_db)):
    fac = MdFacility(**body.model_dump())
    db.add(fac)
    await db.commit()
    await db.refresh(fac)
    return fac


# ═══════════════════════════════════════════════════════════════════════════
# SPECIALTY PROFILES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/specialties", response_model=List[SpecialtyProfileOut])
async def list_specialties(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MdSpecialtyProfile).order_by(MdSpecialtyProfile.name))
    return result.scalars().all()

@router.post("/specialties", response_model=SpecialtyProfileOut, status_code=201)
async def create_specialty(body: SpecialtyProfileCreate, db: AsyncSession = Depends(get_db)):
    sp = MdSpecialtyProfile(**body.model_dump())
    db.add(sp)
    await db.commit()
    await db.refresh(sp)
    return sp

@router.get("/specialties/{sp_id}", response_model=SpecialtyProfileOut)
async def get_specialty(sp_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    sp = await db.get(MdSpecialtyProfile, sp_id)
    if not sp:
        raise HTTPException(404, "Specialty not found")
    return sp


# ═══════════════════════════════════════════════════════════════════════════
# CLINICIANS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/clinicians", response_model=List[ClinicianOut])
async def list_clinicians(
    org_id: Optional[uuid.UUID] = None,
    clinician_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdClinician)
    if org_id:
        q = q.where(MdClinician.organization_id == org_id)
    if clinician_type:
        q = q.where(MdClinician.clinician_type == clinician_type)
    result = await db.execute(q.order_by(MdClinician.display_name))
    return result.scalars().all()

@router.post("/clinicians", response_model=ClinicianOut, status_code=201)
async def create_clinician(body: ClinicianCreate, db: AsyncSession = Depends(get_db)):
    c = MdClinician(**body.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c

@router.get("/clinicians/{cid}", response_model=ClinicianOut)
async def get_clinician(cid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    c = await db.get(MdClinician, cid)
    if not c:
        raise HTTPException(404, "Clinician not found")
    return c


# ═══════════════════════════════════════════════════════════════════════════
# PATIENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/patients", response_model=List[PatientOut])
async def list_patients(
    search: Optional[str] = None,
    org_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdPatient)
    if org_id:
        q = q.where(MdPatient.organization_id == org_id)
    if search:
        q = q.where(
            MdPatient.display_name.ilike(f"%{search}%")
            | MdPatient.mobile_number.ilike(f"%{search}%")
            | MdPatient.mrn.ilike(f"%{search}%")
        )
    result = await db.execute(q.order_by(MdPatient.display_name).limit(200))
    return result.scalars().all()

@router.post("/patients", response_model=PatientOut, status_code=201)
async def create_patient(body: PatientCreate, db: AsyncSession = Depends(get_db)):
    epk = f"EPK-{uuid.uuid4().hex[:12].upper()}"
    mrn = body.mrn or f"MRN-{uuid.uuid4().hex[:8].upper()}"
    patient = MdPatient(
        enterprise_patient_key=epk,
        organization_id=body.organization_id,
        mrn=mrn,
        first_name=body.first_name,
        last_name=body.last_name,
        display_name=body.display_name,
        dob=body.dob,
        sex=body.sex,
        mobile_number=body.mobile_number,
        email=body.email,
        preferred_language=body.preferred_language,
    )
    db.add(patient)
    await db.flush()

    # identifiers
    for ident in body.identifiers:
        db.add(MdPatientIdentifier(
            patient_id=patient.patient_id,
            identifier_type=ident.identifier_type,
            identifier_value=ident.identifier_value,
            issuing_authority=ident.issuing_authority,
        ))

    # consent profile
    if body.consent:
        db.add(MdConsentProfile(patient_id=patient.patient_id, **body.consent.model_dump()))
    else:
        db.add(MdConsentProfile(patient_id=patient.patient_id))

    await db.commit()
    await db.refresh(patient)
    return patient

@router.get("/patients/{pid}", response_model=PatientOut)
async def get_patient(pid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    p = await db.get(MdPatient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    return p

@router.put("/patients/{pid}", response_model=PatientOut)
async def update_patient(pid: uuid.UUID, body: dict, db: AsyncSession = Depends(get_db)):
    p = await db.get(MdPatient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
    for field in ["display_name", "first_name", "last_name", "sex", "mobile_number", "email", "preferred_language"]:
        if field in body and body[field] is not None:
            setattr(p, field, body[field])
    
    if "dob" in body and body["dob"]:
        p.dob = datetime.strptime(body["dob"], "%Y-%m-%d").date()

    await db.commit()
    await db.refresh(p)
    return p

@router.delete("/patients/{pid}")
async def delete_patient(pid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    p = await db.get(MdPatient, pid)
    if not p:
        raise HTTPException(404, "Patient not found")
        
    # Cascade delete all related tables to satisfy FK constraints
    # Order matters: delete child records before parent records
    
    # First, handle appointments and their encounters
    from app.core.axonhis_md.models import MdAppointment
    appointments = (await db.execute(select(MdAppointment).where(MdAppointment.patient_id == pid))).scalars().all()
    for apt in appointments:
        # Set appointment_id to NULL on ALL encounters that reference this appointment (from any patient)
        all_encounters = (await db.execute(select(MdEncounter).where(MdEncounter.appointment_id == apt.appointment_id))).scalars().all()
        for enc in all_encounters:
            enc.appointment_id = None
        await db.flush()  # Flush changes to database before deleting appointment
        # Then delete the appointment
        await db.delete(apt)
    
    for model in [MdPatientIdentifier, MdConsentProfile, MdCoverage, MdShareGrant, MdBillingInvoice, MdDocument, MdEncounter]:
        records = (await db.execute(select(model).where(model.patient_id == pid))).scalars().all()
        for rec in records:
            await db.delete(rec)

    await db.delete(p)
    await db.commit()
    return {"status": "deleted", "patient_id": str(pid)}
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/channels", response_model=List[ChannelOut])
async def list_channels(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MdChannel).order_by(MdChannel.name))
    return result.scalars().all()

@router.post("/channels", response_model=ChannelOut, status_code=201)
async def create_channel(body: ChannelCreate, db: AsyncSession = Depends(get_db)):
    ch = MdChannel(**body.model_dump())
    db.add(ch)
    await db.commit()
    await db.refresh(ch)
    return ch


# ═══════════════════════════════════════════════════════════════════════════
# APPOINTMENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/appointments", response_model=List[AppointmentOut])
async def list_appointments(
    patient_id: Optional[uuid.UUID] = None,
    clinician_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdAppointment)
    if patient_id:
        q = q.where(MdAppointment.patient_id == patient_id)
    if clinician_id:
        q = q.where(MdAppointment.clinician_id == clinician_id)
    if status:
        q = q.where(MdAppointment.status == status)
    if date_from:
        q = q.where(MdAppointment.slot_start >= date_from)
    if date_to:
        q = q.where(MdAppointment.slot_end <= date_to)
    result = await db.execute(q.order_by(MdAppointment.slot_start.desc()).limit(500))
    rows = result.scalars().all()
    out = []
    for a in rows:
        d = AppointmentOut.model_validate(a)
        if a.patient:
            d.patient_name = a.patient.display_name
        if a.clinician:
            d.clinician_name = a.clinician.display_name
        out.append(d)
    return out

@router.post("/appointments", response_model=AppointmentOut, status_code=201)
async def create_appointment(body: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    appt = MdAppointment(**body.model_dump())
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    
    # Auto-create encounter for the appointment
    enc = MdEncounter(
        organization_id=appt.organization_id,
        facility_id=appt.facility_id,
        appointment_id=appt.appointment_id,
        patient_id=appt.patient_id,
        clinician_id=appt.clinician_id,
        encounter_mode="IN_PERSON",
        encounter_status="OPEN",
        chief_complaint=appt.reason_text
    )
    db.add(enc)
    await db.commit()
    await db.refresh(enc)
    
    d = AppointmentOut.model_validate(appt)
    if appt.patient:
        d.patient_name = appt.patient.display_name
    if appt.clinician:
        d.clinician_name = appt.clinician.display_name
    d.encounter_id = enc.encounter_id
    return d

@router.patch("/appointments/{aid}/status")
async def update_appointment_status(
    aid: uuid.UUID, status: str = Query(...), db: AsyncSession = Depends(get_db)
):
    appt = await db.get(MdAppointment, aid)
    if not appt:
        raise HTTPException(404, "Appointment not found")
    appt.status = status
    await db.commit()
    return {"status": "updated", "appointment_id": str(aid), "new_status": status}


# ═══════════════════════════════════════════════════════════════════════════
# ENCOUNTERS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/encounters", response_model=List[EncounterOut])
async def list_encounters(
    patient_id: Optional[uuid.UUID] = None,
    clinician_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdEncounter)
    if patient_id:
        q = q.where(MdEncounter.patient_id == patient_id)
    if clinician_id:
        q = q.where(MdEncounter.clinician_id == clinician_id)
    if status:
        q = q.where(MdEncounter.encounter_status == status)
    result = await db.execute(q.order_by(MdEncounter.started_at.desc()).limit(500))
    rows = result.scalars().all()
    out = []
    for e in rows:
        d = EncounterOut.model_validate(e)
        if e.patient:
            d.patient_name = e.patient.display_name
        if e.clinician:
            d.clinician_name = e.clinician.display_name
        out.append(d)
    return out

@router.post("/encounters", response_model=EncounterOut, status_code=201)
async def create_encounter(body: EncounterCreate, db: AsyncSession = Depends(get_db)):
    enc = MdEncounter(**body.model_dump())
    db.add(enc)
    await db.commit()
    await db.refresh(enc)
    d = EncounterOut.model_validate(enc)
    if enc.patient:
        d.patient_name = enc.patient.display_name
    if enc.clinician:
        d.clinician_name = enc.clinician.display_name
    return d

@router.get("/encounters/{eid}", response_model=EncounterOut)
async def get_encounter(eid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    enc = await db.get(MdEncounter, eid)
    if not enc:
        raise HTTPException(404, "Encounter not found")
    d = EncounterOut.model_validate(enc)
    if enc.patient:
        d.patient_name = enc.patient.display_name
    if enc.clinician:
        d.clinician_name = enc.clinician.display_name
    return d

@router.patch("/encounters/{eid}/close")
async def close_encounter(eid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    enc = await db.get(MdEncounter, eid)
    if not enc:
        raise HTTPException(404, "Encounter not found")
    enc.encounter_status = "CLOSED"
    enc.closed_at = datetime.utcnow()
    await db.commit()
    return {"status": "closed", "encounter_id": str(eid)}


# ═══════════════════════════════════════════════════════════════════════════
# ENCOUNTER NOTES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/encounters/{eid}/notes", response_model=List[EncounterNoteOut])
async def list_encounter_notes(eid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MdEncounterNote).where(MdEncounterNote.encounter_id == eid).order_by(MdEncounterNote.authored_at)
    )
    return result.scalars().all()

@router.post("/notes", response_model=EncounterNoteOut, status_code=201)
async def create_encounter_note(body: EncounterNoteCreate, db: AsyncSession = Depends(get_db)):
    note = MdEncounterNote(**body.model_dump())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return note


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNOSES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/encounters/{eid}/diagnoses", response_model=List[DiagnosisOut])
async def list_encounter_diagnoses(eid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MdDiagnosis).where(MdDiagnosis.encounter_id == eid).order_by(MdDiagnosis.created_at)
    )
    return result.scalars().all()

@router.post("/diagnoses", response_model=DiagnosisOut, status_code=201)
async def create_diagnosis(body: DiagnosisCreate, db: AsyncSession = Depends(get_db)):
    dx = MdDiagnosis(**body.model_dump())
    db.add(dx)
    await db.commit()
    await db.refresh(dx)
    return dx


# ═══════════════════════════════════════════════════════════════════════════
# SERVICE REQUESTS (ORDERS)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/encounters/{eid}/service-requests", response_model=List[ServiceRequestOut])
async def list_service_requests(eid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MdServiceRequest).where(MdServiceRequest.encounter_id == eid).order_by(MdServiceRequest.created_at)
    )
    return result.scalars().all()

@router.get("/service-requests", response_model=List[ServiceRequestOut])
async def list_all_service_requests(
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdServiceRequest)
    if status:
        q = q.where(MdServiceRequest.status == status)
    if request_type:
        q = q.where(MdServiceRequest.request_type == request_type)
    result = await db.execute(q.order_by(MdServiceRequest.created_at.desc()).limit(200))
    return result.scalars().all()

@router.post("/service-requests", response_model=ServiceRequestOut, status_code=201)
async def create_service_request(body: ServiceRequestCreate, db: AsyncSession = Depends(get_db)):
    sr = MdServiceRequest(**body.model_dump())
    db.add(sr)
    await db.commit()
    await db.refresh(sr)
    return sr

@router.patch("/service-requests/{srid}/status")
async def update_service_request_status(
    srid: uuid.UUID, status: str = Query(...), db: AsyncSession = Depends(get_db)
):
    sr = await db.get(MdServiceRequest, srid)
    if not sr:
        raise HTTPException(404, "Service request not found")
    sr.status = status
    await db.commit()
    return {"status": "updated"}


# ═══════════════════════════════════════════════════════════════════════════
# MEDICATION REQUESTS (PRESCRIBING)
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/encounters/{eid}/medications", response_model=List[MedicationRequestOut])
async def list_medications(eid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MdMedicationRequest).where(MdMedicationRequest.encounter_id == eid).order_by(MdMedicationRequest.created_at)
    )
    return result.scalars().all()

@router.post("/medications", response_model=MedicationRequestOut, status_code=201)
async def create_medication(body: MedicationRequestCreate, db: AsyncSession = Depends(get_db)):
    med = MdMedicationRequest(**body.model_dump())
    db.add(med)
    await db.commit()
    await db.refresh(med)
    return med


# ═══════════════════════════════════════════════════════════════════════════
# DEVICES
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/devices", response_model=List[DeviceOut])
async def list_devices(org_id: Optional[uuid.UUID] = None, db: AsyncSession = Depends(get_db)):
    q = select(MdDevice)
    if org_id:
        q = q.where(MdDevice.organization_id == org_id)
    result = await db.execute(q.order_by(MdDevice.device_name))
    return result.scalars().all()

@router.post("/devices", response_model=DeviceOut, status_code=201)
async def create_device(body: DeviceCreate, db: AsyncSession = Depends(get_db)):
    dev = MdDevice(**body.model_dump())
    db.add(dev)
    await db.commit()
    await db.refresh(dev)
    return dev


# ═══════════════════════════════════════════════════════════════════════════
# DEVICE RESULTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/encounters/{eid}/device-results", response_model=List[DeviceResultOut])
async def list_device_results(eid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MdDeviceResult).where(MdDeviceResult.encounter_id == eid).order_by(MdDeviceResult.captured_at.desc())
    )
    return result.scalars().all()

@router.post("/device-results", response_model=DeviceResultOut, status_code=201)
async def create_device_result(body: DeviceResultCreate, db: AsyncSession = Depends(get_db)):
    dr = MdDeviceResult(**body.model_dump())
    db.add(dr)
    await db.commit()
    await db.refresh(dr)
    return dr


# ═══════════════════════════════════════════════════════════════════════════
# OBSERVATIONS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/encounters/{eid}/observations", response_model=List[ObservationOut])
async def list_observations(eid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MdObservation).where(MdObservation.encounter_id == eid).order_by(MdObservation.effective_at)
    )
    return result.scalars().all()

@router.post("/observations", response_model=ObservationOut, status_code=201)
async def create_observation(body: ObservationCreate, db: AsyncSession = Depends(get_db)):
    obs = MdObservation(**body.model_dump())
    db.add(obs)
    await db.commit()
    await db.refresh(obs)
    return obs


# ═══════════════════════════════════════════════════════════════════════════
# DOCUMENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/documents", response_model=List[DocumentOut])
async def list_documents(
    patient_id: Optional[uuid.UUID] = None,
    encounter_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdDocument)
    if patient_id:
        q = q.where(MdDocument.patient_id == patient_id)
    if encounter_id:
        q = q.where(MdDocument.encounter_id == encounter_id)
    result = await db.execute(q.order_by(MdDocument.created_at.desc()).limit(200))
    return result.scalars().all()

@router.post("/documents", response_model=DocumentOut, status_code=201)
async def create_document(body: DocumentCreate, db: AsyncSession = Depends(get_db)):
    # Extract patient_id from encounter if not provided
    patient_id = body.patient_id
    if not patient_id and body.encounter_id:
        enc = await db.get(MdEncounter, body.encounter_id)
        if enc:
            patient_id = enc.patient_id
    
    if not patient_id:
        raise HTTPException(400, "patient_id is required or must be derivable from encounter_id")
    
    doc = MdDocument(
        patient_id=patient_id,
        encounter_id=body.encounter_id,
        document_type=body.document_type,
        category=body.category,
        title=body.title,
        content_text=body.content_text,
        storage_uri=body.storage_uri,
        mime_type=body.mime_type,
        status=body.status,
        sensitive_flag=body.sensitive_flag,
        share_sensitivity=body.share_sensitivity,
        created_by=body.created_by
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc

@router.delete("/documents/{doc_id}", status_code=204)
async def delete_document(doc_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    doc = await db.get(MdDocument, doc_id)
    if not doc:
        raise HTTPException(404, "Document not found")
    await db.delete(doc)
    await db.commit()

# File upload endpoint
UPLOAD_DIR = "/app/uploads"
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

@router.post("/documents/upload", status_code=201)
async def upload_file(file: UploadFile = File(...)):
    try:
        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        # Save file to disk
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        return {"filename": unique_filename, "storage_uri": f"/uploads/{unique_filename}", "original_name": file.filename}
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

# File download endpoint
@router.get("/documents/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, "File not found")
    return FileResponse(file_path, filename=filename)

# Voice transcription endpoint using Google Cloud STT
@router.post("/voice/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Validate file
        if not file or not file.filename:
            raise HTTPException(400, "No audio file provided")
        
        # Save audio file temporarily
        audio_path = os.path.join(UPLOAD_DIR, f"audio_{uuid.uuid4()}{os.path.splitext(file.filename)[1]}")
        with open(audio_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Check if file is empty
        if os.path.getsize(audio_path) == 0:
            os.remove(audio_path)
            raise HTTPException(400, "Audio file is empty")
        
        # Initialize Google Cloud Speech client
        credentials_path = os.path.join(os.path.dirname(__file__), "google_credentials.json")
        if not os.path.exists(credentials_path):
            os.remove(audio_path)
            raise HTTPException(500, "Google Cloud credentials not found")
        
        try:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = speech.SpeechClient(credentials=credentials)
        except Exception as e:
            os.remove(audio_path)
            logger.error(f"Failed to initialize Google Cloud Speech client: {str(e)}")
            raise HTTPException(500, "Failed to initialize speech recognition service")
        
        # Read the audio file
        with open(audio_path, "rb") as audio_file:
            audio_content = audio_file.read()
        
        # Configure recognition
        audio = speech.RecognitionAudio(content=audio_content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
            sample_rate_hertz=48000,
            language_code="en-US",
            enable_automatic_punctuation=True,
        )
        
        # Perform transcription
        try:
            response = client.recognize(config=config, audio=audio)
        except Exception as e:
            logger.error(f"Speech recognition failed: {str(e)}")
            os.remove(audio_path)
            raise HTTPException(500, "Speech recognition failed")
        
        # Extract transcript
        transcript = ""
        for result in response.results:
            transcript += result.alternatives[0].transcript + " "
        
        transcript = transcript.strip()
        
        if not transcript:
            transcript = "No speech detected in the audio file."
        
        # Clean up audio file
        try:
            os.remove(audio_path)
        except Exception as e:
            logger.warning(f"Failed to clean up audio file: {str(e)}")
        
        return {"transcript": transcript}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Unexpected error in transcription: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(500, f"Transcription failed: {str(e)}")

# AI question suggestions endpoint using Grok
@router.post("/ai/suggest-questions")
async def suggest_questions(
    encounter_id: uuid.UUID,
    transcript: str = "",
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get encounter and patient context
        enc = await db.get(MdEncounter, encounter_id)
        if not enc:
            raise HTTPException(404, "Encounter not found")
        
        # Use Grok API for question suggestions
        from app.core.ai.grok_client import grok_chat
        
        context = f"""
        Chief Complaint: {enc.chief_complaint or "Not specified"}
        Patient Transcript: {transcript}
        Encounter Status: {enc.encounter_status}
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are a clinical AI assistant that generates relevant follow-up questions for medical consultations. Generate 5-7 specific, relevant questions based on the patient's chief complaint and transcript. Return as a JSON array of strings."
            },
            {
                "role": "user",
                "content": f"Based on this clinical context, suggest relevant follow-up questions:\n{context}"
            }
        ]
        
        try:
            response = await grok_chat(messages, temperature=0.3, max_tokens=512)
            import json
            questions = json.loads(response["content"])
            if not isinstance(questions, list):
                questions = []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            # Fallback questions
            questions = [
                "Can you describe your symptoms in more detail?",
                "How long have you been experiencing these symptoms?",
                "Have you had these symptoms before?",
                "Are you taking any medications?",
                "Do you have any known allergies?"
            ]
            if enc.chief_complaint:
                questions.insert(0, f"Can you tell me more about your {enc.chief_complaint.lower()}?")
        except Exception as e:
            logger.error(f"Failed to generate questions: {str(e)}")
            # Fallback questions
            questions = [
                "Can you describe your symptoms in more detail?",
                "How long have you been experiencing these symptoms?",
                "Have you had these symptoms before?",
                "Are you taking any medications?",
                "Do you have any known allergies?"
            ]
            if enc.chief_complaint:
                questions.insert(0, f"Can you tell me more about your {enc.chief_complaint.lower()}?")
        
        return {"questions": questions}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error in suggest_questions: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(500, f"Failed to generate suggestions: {str(e)}")

# AI management plan suggestions endpoint using Grok
@router.post("/ai/suggest-management")
async def suggest_management(
    encounter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get encounter context
        enc = await db.get(MdEncounter, encounter_id)
        if not enc:
            raise HTTPException(404, "Encounter not found")
        
        # Get notes for context
        notes_result = await db.execute(select(MdEncounterNote).where(MdEncounterNote.encounter_id == encounter_id))
        notes = notes_result.scalars().all()
        
        # Use Grok API for management plan suggestions
        from app.core.ai.grok_client import grok_json
        
        notes_text = "\n".join([n.narrative_text or str(n.structured_json) for n in notes if n.narrative_text or n.structured_json])
        
        context = f"""
        Chief Complaint: {enc.chief_complaint or "Not specified"}
        Encounter Mode: {enc.encounter_mode}
        Clinical Notes: {notes_text}
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are a clinical AI assistant that generates management plans for medical consultations. Provide suggestions for diagnoses (with confidence scores), tests, medications, and patient advice. Return as JSON with keys: diagnoses (array with name and confidence), tests (array with name and priority), medications (array with name, dose, frequency, duration), advice (array of strings)."
            },
            {
                "role": "user",
                "content": f"Based on this clinical context, suggest a management plan:\n{context}"
            }
        ]
        
        try:
            suggestions = await grok_json(messages, temperature=0.2, max_tokens=1024)
            
            # Ensure the response has the expected structure
            if not suggestions.get("diagnoses"):
                suggestions["diagnoses"] = []
            if not suggestions.get("tests"):
                suggestions["tests"] = []
            if not suggestions.get("medications"):
                suggestions["medications"] = []
            if not suggestions.get("advice"):
                suggestions["advice"] = []
                
        except Exception as e:
            # Fallback to placeholder suggestions if Grok fails
            suggestions = {
                "diagnoses": [
                    {"name": "Tension Headache", "confidence": 0.75},
                    {"name": "Migraine", "confidence": 0.60}
                ],
                "tests": [
                    {"name": "Complete Blood Count", "priority": "ROUTINE"},
                    {"name": "CT Head (if indicated)", "priority": "AS NEEDED"}
                ],
                "medications": [
                    {"name": "Paracetamol 500mg", "dose": "1 tablet", "frequency": "QID", "duration": "3 days"},
                    {"name": "Sumatriptan 50mg", "dose": "1 tablet", "frequency": "PRN", "duration": "As needed"}
                ],
                "advice": [
                    "Rest in a quiet, dark room",
                    "Stay hydrated",
                    "Avoid triggers like stress and certain foods",
                    "Follow up if symptoms persist beyond 7 days"
                ]
            }
        
        return suggestions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to generate management plan: {str(e)}")

# AI examination findings suggestions endpoint
@router.post("/ai/suggest-exam")
async def suggest_exam(
    encounter_id: uuid.UUID,
    findings: str = "",
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get encounter context
        enc = await db.get(MdEncounter, encounter_id)
        if not enc:
            raise HTTPException(404, "Encounter not found")
        
        # Use Grok API for exam follow-up suggestions
        from app.core.ai.grok_client import grok_json
        
        context = f"""
        Chief Complaint: {enc.chief_complaint or "Not specified"}
        Encounter Mode: {enc.encounter_mode}
        Examination Findings: {findings}
        """
        
        messages = [
            {
                "role": "system",
                "content": "You are a clinical AI assistant that suggests follow-up examinations or tests based on examination findings. Return as JSON with key 'suggestions' containing an array of strings with specific follow-up recommendations."
            },
            {
                "role": "user",
                "content": f"Based on these examination findings, suggest follow-up examinations or tests:\n{context}"
            }
        ]
        
        try:
            result = await grok_json(messages, temperature=0.3, max_tokens=512)
            suggestions = result.get("suggestions", [])
            if not isinstance(suggestions, list):
                suggestions = []
        except Exception as e:
            # Fallback suggestions
            suggestions = [
                "Consider ordering relevant laboratory tests",
                "Monitor vital signs regularly",
                "Document all abnormal findings",
                "Consider specialist referral if indicated"
            ]
        
        return {"suggestions": suggestions}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to generate exam suggestions: {str(e)}")

# Prompt template configuration endpoint
@router.post("/encounter-templates")
async def save_encounter_template(
    encounter_id: uuid.UUID,
    prompt_template: str,
    db: AsyncSession = Depends(get_db)
):
    try:
        enc = await db.get(MdEncounter, encounter_id)
        if not enc:
            raise HTTPException(404, "Encounter not found")
        
        # For now, store the prompt template in the encounter's notes
        template_note = MdEncounterNote(
            encounter_id=encounter_id,
            note_type="PROMPT_TEMPLATE",
            narrative_text=prompt_template,
            authored_by="SYSTEM"
        )
        db.add(template_note)
        await db.commit()
        
        return {"message": "Prompt template saved successfully"}
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Failed to save prompt template: {str(e)}")

# AI-driven workflow automation endpoint
@router.post("/encounters/{encounter_id}/ai-workflow")
async def run_ai_workflow(
    encounter_id: uuid.UUID,
    workflow_type: str = "FULL_AUTOMATION",
    auto_execute: bool = False,
    db: AsyncSession = Depends(get_db)
):
    """
    Run AI-driven workflow automation for clinical encounters.
    
    Workflow types:
    - FULL_AUTOMATION: Complete AI-driven workflow from patient audio to documentation
    - QUESTIONING_ONLY: AI-driven questioning only
    - MANAGEMENT_ONLY: AI management plan generation only
    """
    try:
        from app.core.mcp.client import MCPClient
        from app.core.ai.grok_client import grok_json, grok_chat
        
        # Get encounter context
        enc = await db.get(MdEncounter, encounter_id)
        if not enc:
            raise HTTPException(404, "Encounter not found")
        
        mcp_client = MCPClient(db)
        workflow_results = {
            "workflow_type": workflow_type,
            "encounter_id": str(encounter_id),
            "steps": []
        }
        
        # Step 1: Get patient information
        patient_info = await mcp_client.call_tool("get_patient_info", {"patient_id": str(enc.patient_id)})
        workflow_results["steps"].append({
            "step": "get_patient_info",
            "success": patient_info.get("success"),
            "data": patient_info
        })
        
        # Step 2: Analyze encounter context
        encounter_info = await mcp_client.call_tool("get_encounter_info", {"encounter_id": str(encounter_id)})
        workflow_results["steps"].append({
            "step": "get_encounter_info",
            "success": encounter_info.get("success"),
            "data": encounter_info
        })
        
        if workflow_type == "FULL_AUTOMATION" or workflow_type == "QUESTIONING_ONLY":
            # Step 3: Generate AI questions based on context
            context = f"""
            Patient: {patient_info.get('data', {}).get('display_name', 'Unknown')}
            Chief Complaint: {enc.chief_complaint or 'Not specified'}
            Encounter Status: {enc.encounter_status}
            """
            
            messages = [
                {
                    "role": "system",
                    "content": "You are a clinical AI assistant. Generate 5-7 relevant follow-up questions based on the patient's chief complaint and context. Return as JSON array of strings."
                },
                {
                    "role": "user",
                    "content": f"Generate relevant follow-up questions:\n{context}"
                }
            ]
            
            try:
                questions_result = await grok_json(messages, temperature=0.3, max_tokens=512)
                questions = questions_result if isinstance(questions_result, list) else []
                workflow_results["steps"].append({
                    "step": "generate_questions",
                    "success": True,
                    "data": {"questions": questions}
                })
            except Exception as e:
                logger.error(f"Error generating questions: {str(e)}")
                workflow_results["steps"].append({
                    "step": "generate_questions",
                    "success": False,
                    "error": str(e)
                })
        
        if workflow_type == "FULL_AUTOMATION" or workflow_type == "MANAGEMENT_ONLY":
            # Step 4: Generate AI management plan
            notes_result = await db.execute(select(MdEncounterNote).where(MdEncounterNote.encounter_id == encounter_id))
            notes = notes_result.scalars().all()
            
            notes_text = "\n".join([n.narrative_text or str(n.structured_json) for n in notes if n.narrative_text or n.structured_json])
            
            mgmt_context = f"""
            Chief Complaint: {enc.chief_complaint or 'Not specified'}
            Encounter Status: {enc.encounter_status}
            Clinical Notes: {notes_text}
            """
            
            mgmt_messages = [
                {
                    "role": "system",
                    "content": "You are a clinical AI assistant that generates management plans. Provide suggestions for diagnoses (with confidence), tests, medications, and advice. Return as JSON with keys: diagnoses (array with name and confidence), tests (array with name and priority), medications (array with name, dose, frequency), advice (array of strings)."
                },
                {
                    "role": "user",
                    "content": f"Generate management plan:\n{mgmt_context}"
                }
            ]
            
            try:
                mgmt_result = await grok_json(mgmt_messages, temperature=0.2, max_tokens=1024)
                
                # Execute MCP tool calls if auto_execute is enabled
                if auto_execute:
                    tool_calls = []
                    
                    # Order lab tests
                    if mgmt_result.get("tests"):
                        for test in mgmt_result["tests"][:3]:  # Limit to 3 tests
                            tool_calls.append({
                                "tool_name": "order_lab_test",
                                "arguments": {
                                    "encounter_id": str(encounter_id),
                                    "test_name": test.get("name", "Unknown"),
                                    "priority": test.get("priority", "ROUTINE")
                                }
                            })
                    
                    # Prescribe medications
                    if mgmt_result.get("medications"):
                        for med in mgmt_result["medications"][:3]:  # Limit to 3 medications
                            tool_calls.append({
                                "tool_name": "prescribe_medication",
                                "arguments": {
                                    "encounter_id": str(encounter_id),
                                    "medication_name": med.get("name", "Unknown"),
                                    "dose": med.get("dose", "Unknown"),
                                    "frequency": med.get("frequency", "Unknown"),
                                    "route": med.get("route", "ORAL")
                                }
                            })
                    
                    # Execute tool chain
                    if tool_calls:
                        execution_results = await mcp_client.execute_tool_chain(tool_calls)
                        workflow_results["tool_executions"] = execution_results
                
                workflow_results["steps"].append({
                    "step": "generate_management_plan",
                    "success": True,
                    "data": mgmt_result
                })
            except Exception as e:
                logger.error(f"Error generating management plan: {str(e)}")
                workflow_results["steps"].append({
                    "step": "generate_management_plan",
                    "success": False,
                    "error": str(e)
                })
        
        if workflow_type == "FULL_AUTOMATION":
            # Step 5: Generate clinical note
            try:
                note_result = await mcp_client.call_tool("generate_clinical_note", {
                    "encounter_id": str(encounter_id),
                    "note_type": "SUMMARY"
                })
                workflow_results["steps"].append({
                    "step": "generate_clinical_note",
                    "success": note_result.get("success"),
                    "data": note_result
                })
            except Exception as e:
                logger.error(f"Error generating clinical note: {str(e)}")
                workflow_results["steps"].append({
                    "step": "generate_clinical_note",
                    "success": False,
                    "error": str(e)
                })
        
        workflow_results["success"] = all(step.get("success", False) for step in workflow_results["steps"])
        
        return workflow_results
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"Error in AI workflow: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(500, f"AI workflow failed: {str(e)}")

# Document generation endpoint
@router.post("/encounters/{encounter_id}/generate-document")
async def generate_document(
    encounter_id: uuid.UUID,
    title: str = "Clinical Summary",
    db: AsyncSession = Depends(get_db)
):
    try:
        enc = await db.get(MdEncounter, encounter_id)
        if not enc:
            raise HTTPException(404, "Encounter not found")
        
        # Get encounter details
        notes_result = await db.execute(select(MdEncounterNote).where(MdEncounterNote.encounter_id == encounter_id))
        notes = notes_result.scalars().all()
        
        diag_result = await db.execute(select(MdDiagnosis).where(MdDiagnosis.encounter_id == encounter_id))
        diagnoses = diag_result.scalars().all()
        
        meds_result = await db.execute(select(MdMedicationRequest).where(MdMedicationRequest.encounter_id == encounter_id))
        medications = meds_result.scalars().all()
        
        # Use Grok to generate document
        from app.core.ai.grok_client import grok_chat
        
        notes_text = "\n".join([n.narrative_text or str(n.structured_json) for n in notes if n.narrative_text or n.structured_json])
        diag_text = "\n".join([d.diagnosis_display for d in diagnoses])
        meds_text = "\n".join([f"{m.medication_name} - {m.dose} {m.frequency}" for m in medications if m.medication_name])
        
        # Get patient name from relationship
        patient_name = "Unknown"
        if enc.patient:
            patient_name = enc.patient.display_name or f"{enc.patient.first_name or ''} {enc.patient.last_name or ''}".strip() or "Unknown"
        
        context = f"""
        Document Type: {title}
        Patient: {patient_name}
        Chief Complaint: {enc.chief_complaint or "Not specified"}
        Encounter Status: {enc.encounter_status}
        
        Clinical Notes:
        {notes_text}
        
        Diagnoses:
        {diag_text}
        
        Medications:
        {meds_text}
        """
        
        messages = [
            {
                "role": "system",
                "content": f"You are a clinical documentation assistant. Generate a professional {title} based on the provided encounter information. Format it clearly with appropriate sections."
            },
            {
                "role": "user",
                "content": f"Generate a {title}:\n{context}"
            }
        ]
        
        result = await grok_chat(messages, temperature=0.3, max_tokens=2048)
        
        return {"content": result["content"]}
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Failed to generate document: {str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"ERROR in generate-document: {error_detail}")
        raise HTTPException(500, error_detail)

# Encounter completion endpoint
@router.post("/encounters/{encounter_id}/complete")
async def complete_encounter(
    encounter_id: uuid.UUID,
    share_with_email: str = "",
    db: AsyncSession = Depends(get_db)
):
    try:
        enc = await db.get(MdEncounter, encounter_id)
        if not enc:
            raise HTTPException(404, "Encounter not found")
        
        # Update encounter status
        enc.encounter_status = "COMPLETED"
        enc.ended_at = datetime.utcnow()
        
        await db.commit()
        
        # TODO: Implement actual email sharing functionality
        # For now, just log the share request
        if share_with_email:
            logger.info(f"Encounter {encounter_id} summary should be shared with: {share_with_email}")
        
        return {"message": "Encounter completed successfully", "shared_with": share_with_email}
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, f"Failed to complete encounter: {str(e)}")


# ═══════════════════════════════════════════════════════════════════════════
# SHARE GRANTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/share-grants", response_model=List[ShareGrantOut])
async def list_share_grants(
    patient_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdShareGrant)
    if patient_id:
        q = q.where(MdShareGrant.patient_id == patient_id)
    result = await db.execute(q.order_by(MdShareGrant.created_at.desc()))
    return result.scalars().all()

@router.post("/share-grants", response_model=ShareGrantOut, status_code=201)
async def create_share_grant(body: ShareGrantCreate, db: AsyncSession = Depends(get_db)):
    sg = MdShareGrant(**body.model_dump())
    if body.grant_method == "QR_CODE":
        sg.qr_token = secrets.token_urlsafe(32)
    if body.grant_method in ("SECURE_LINK", "QR_CODE"):
        sg.secure_link_token = secrets.token_urlsafe(48)
    db.add(sg)
    await db.commit()
    await db.refresh(sg)
    return sg

@router.patch("/share-grants/{sgid}/revoke")
async def revoke_share_grant(sgid: uuid.UUID, db: AsyncSession = Depends(get_db)):
    sg = await db.get(MdShareGrant, sgid)
    if not sg:
        raise HTTPException(404, "Share grant not found")
    sg.revoked_at = datetime.utcnow()
    await db.commit()
    return {"status": "revoked"}

@router.get("/share/view/{token}")
async def view_shared_record(token: str, db: AsyncSession = Depends(get_db)):
    """Public endpoint for accessing shared patient records via secure link."""
    result = await db.execute(
        select(MdShareGrant).where(MdShareGrant.secure_link_token == token)
    )
    sg = result.scalars().first()
    if not sg:
        raise HTTPException(404, "Share link not found or expired")
    if sg.revoked_at is not None:
        raise HTTPException(403, "Share access has been revoked")
    if sg.expires_at and sg.expires_at < datetime.utcnow():
        raise HTTPException(403, "Share link has expired")

    # Log access
    log = MdShareAccessLog(
        share_grant_id=sg.share_grant_id,
        access_channel="SECURE_LINK",
        access_result="GRANTED",
    )
    db.add(log)
    await db.commit()

    # Return patient info based on scope
    patient = await db.get(MdPatient, sg.patient_id)
    if not patient:
        raise HTTPException(404, "Patient not found")

    return {
        "patient_name": patient.display_name,
        "scope_type": sg.scope_type,
        "grant_method": sg.grant_method,
        "patient_id": str(patient.patient_id),
    }


# ═══════════════════════════════════════════════════════════════════════════
# PAYERS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/payers", response_model=List[PayerOut])
async def list_payers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MdPayer).order_by(MdPayer.payer_name))
    return result.scalars().all()

@router.post("/payers", response_model=PayerOut, status_code=201)
async def create_payer(body: PayerCreate, db: AsyncSession = Depends(get_db)):
    p = MdPayer(**body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


# ═══════════════════════════════════════════════════════════════════════════
# COVERAGE
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/coverage", response_model=List[CoverageOut])
async def list_coverage(
    patient_id: Optional[uuid.UUID] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdCoverage)
    if patient_id:
        q = q.where(MdCoverage.patient_id == patient_id)
    result = await db.execute(q.order_by(MdCoverage.created_at.desc()))
    return result.scalars().all()

@router.post("/coverage", response_model=CoverageOut, status_code=201)
async def create_coverage(body: CoverageCreate, db: AsyncSession = Depends(get_db)):
    cov = MdCoverage(**body.model_dump())
    db.add(cov)
    await db.commit()
    await db.refresh(cov)
    return cov


# ═══════════════════════════════════════════════════════════════════════════
# BILLING
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/billing/invoices", response_model=List[BillingInvoiceOut])
async def list_invoices(
    patient_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdBillingInvoice)
    if patient_id:
        q = q.where(MdBillingInvoice.patient_id == patient_id)
    if status:
        q = q.where(MdBillingInvoice.status == status)
    result = await db.execute(q.order_by(MdBillingInvoice.created_at.desc()).limit(200))
    rows = result.scalars().all()
    out = []
    for inv in rows:
        d = BillingInvoiceOut.model_validate(inv)
        if inv.patient:
            d.patient_name = inv.patient.display_name
        out.append(d)
    return out

@router.post("/billing/invoices", response_model=BillingInvoiceOut, status_code=201)
async def create_invoice(body: BillingInvoiceCreate, db: AsyncSession = Depends(get_db)):
    inv_num = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    total = sum(li.line_amount for li in body.line_items)
    
    # Get organization_id from patient if not provided
    org_id = body.organization_id
    if not org_id:
        patient = await db.get(MdPatient, body.patient_id)
        if patient:
            org_id = patient.organization_id
    
    inv = MdBillingInvoice(
        organization_id=org_id,
        patient_id=body.patient_id,
        encounter_id=body.encounter_id,
        coverage_id=body.coverage_id,
        invoice_number=inv_num,
        currency_code=body.currency_code,
        total_amount=total,
        due_date=body.due_date,
    )
    db.add(inv)
    await db.flush()
    for li in body.line_items:
        db.add(MdBillingLineItem(
            billing_invoice_id=inv.billing_invoice_id,
            **li.model_dump(),
        ))
    await db.commit()
    await db.refresh(inv)
    d = BillingInvoiceOut.model_validate(inv)
    if inv.patient:
        d.patient_name = inv.patient.display_name
    return d

@router.patch("/billing/invoices/{iid}/status")
async def update_invoice_status(
    iid: uuid.UUID, status: str = Query(...), db: AsyncSession = Depends(get_db)
):
    inv = await db.get(MdBillingInvoice, iid)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    inv.status = status
    await db.commit()
    return {"status": "updated"}


# ═══════════════════════════════════════════════════════════════════════════
# INTEGRATION EVENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/integration/events", response_model=List[IntegrationEventOut])
async def list_integration_events(
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdIntegrationEvent)
    if status:
        q = q.where(MdIntegrationEvent.event_status == status)
    result = await db.execute(q.order_by(MdIntegrationEvent.created_at.desc()).limit(200))
    return result.scalars().all()

@router.post("/integration/events", response_model=IntegrationEventOut, status_code=201)
async def create_integration_event(body: IntegrationEventCreate, db: AsyncSession = Depends(get_db)):
    ie = MdIntegrationEvent(**body.model_dump())
    db.add(ie)
    await db.commit()
    await db.refresh(ie)
    return ie


# ═══════════════════════════════════════════════════════════════════════════
# AUDIT EVENTS
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/audit/events", response_model=List[AuditEventOut])
async def list_audit_events(
    patient_id: Optional[uuid.UUID] = None,
    action_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    q = select(MdAuditEvent)
    if patient_id:
        q = q.where(MdAuditEvent.patient_id == patient_id)
    if action_type:
        q = q.where(MdAuditEvent.action_type == action_type)
    result = await db.execute(q.order_by(MdAuditEvent.event_time.desc()).limit(500))
    return result.scalars().all()

@router.get("/medications", response_model=List[MedicationRequestOut])
async def list_all_medications(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MdMedicationRequest).order_by(MdMedicationRequest.created_at.desc()).limit(200))
    return result.scalars().all()

@router.get("/documents", response_model=List[DocumentOut])
async def list_all_documents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MdDocument).order_by(MdDocument.created_at.desc()).limit(200))
    return result.scalars().all()
