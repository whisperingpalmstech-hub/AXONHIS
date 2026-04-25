"""
AXONHIS Backend – Enterprise Application Entry Point.

All configuration, middleware, and routers are registered here.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

from app.config import settings
from app.database import engine, get_db
from app.core.system.monitoring.services import MonitoringService
from app.core.system.security.middleware import SecurityHeadersMiddleware

# Core System & Auth Engine
from app.core.auth.router import router as auth_router
from app.core.audit.router import router as audit_router
from app.core.files.router import router as files_router
from app.core.notifications.router import router as notifications_router
from app.core.config.router import router as config_router

# Clinical Entities & Medical Records
from app.core.patients.router import router as patients_router
from app.core.encounters.router import router as encounters_router
from app.core.orders.router import router as orders_router
from app.core.tasks.router import router as tasks_router
from app.core.lab.router import router as lab_router
from app.core.pharmacy.router import router as pharmacy_router
from app.core.billing.router import router as billing_router
from app.core.ai.router import router as ai_router
from app.core.analytics.router import router as analytics_router

# Core Infrastructure Observability
from app.core.system.health_checks.routes import router as system_health_router, public_router as public_health_router
from app.core.system.logging.routes import router as system_logging_router
from app.core.system.monitoring.routes import router as system_monitoring_router
from app.core.cdss.engine.routes import router as cdss_router

# Hospital Departments
from app.core.blood_bank.router import router as blood_bank_router
from app.core.wards.router import router as wards_router
from app.core.radiology.router import router as radiology_router
from app.core.ot.router import router as ot_router
from app.core.communication.routes import communication_router
from app.core.patient_portal.router import portal_router

from app.core.diagnostics.routes import router as diagnostics_router
from app.core.advanced_lab.routes import router as new_advanced_lab_router
from app.core.procurement.routes import router as procurement_router
from app.core.kiosk.routes import router as kiosk_router

# Diagnostic Procedures Engine
from app.core.diagnostics.routes import router as diagnostics_router

# Enterprise Scheduling
from app.core.scheduling.routes import router as scheduling_router

# OPD Visit Intelligence Engine
from app.core.opd_visits.routes import router as opd_visits_router

# OPD Smart Queue & Flow Orchestration Engine
from app.core.smart_queue.routes import router as smart_queue_router

# OPD Nursing Clinical Triage Engine
from app.core.nursing_triage.routes import router as nursing_triage_router
from app.core.nursing.routes import router as nursing_router

# AI Doctor Desk & Intelligent EMR Engine
from app.core.doctor_desk.routes import router as doctor_desk_router

# Enterprise OPD Billing & Revenue Cycle Engine
from app.core.rcm_billing.routes import router as rcm_billing_router

# Multi-Tenancy & Masters Engine
from app.core.administration.tenants.routes import router as multitenancy_router

# Accounting & ERP Subsystem
from app.core.accounting.routes import router as accounting_router

# Clinical Workflow Engine (5 AI modules)
from app.core.clinical_workflow.routes import router as clinical_workflow_router

# Force load all models for SQLAlchemy registry
from app.core.patients.patients.models import Patient
from app.core.patient_portal.patient_accounts.models import PatientAccount
from app.core.scheduling.models import SlotBooking
from app.core.lab.models import LabOrder, LabResult
from app.core.pharmacy.prescriptions.models import Prescription
from app.core.auth.models import User
from app.core.encounters.encounters.models import Encounter
from app.core.encounters.diagnoses.models import EncounterDiagnosis
from app.core.tasks.models import Task
from app.core.encounters.clinical_flags.models import ClinicalFlag
from app.core.billing.invoices.models import Invoice
from app.core.diagnostics.models import (
    DiagnosticTemplate,
    DiagnosticProcedureOrder,
    DiagnosticWorkbenchRecord,
    DiagnosticResultEntry,
    DiagnosticValidation,
    DiagnosticReport,
    DiagnosticReportHandover,
    DiagnosticAmendmentLog
)
from app.core.advanced_lab.models import HistoSpecimen
from app.core.accounting.models import ChartOfAccounts, JournalEntry, JournalEntryLine

# CSSD Models
from app.core.cssd.models import (
    InstrumentSet, SterilizationCycle, CycleSetLink, CSSDDispatch
)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:

    """Startup / shutdown lifecycle."""
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="AXONHIS API",
        description="AI-First Hospital Information System — Enterprise Backend",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────
    allowed_origins = settings.backend_cors_origins
    if isinstance(allowed_origins, str):
        allowed_origins = [i.strip() for i in allowed_origins.split(",") if i.strip()]
    
    # Add local developer origins for safety
    for dev_origin in ["http://localhost:3000", "http://localhost:9501", "http://localhost:9502", "http://localhost:9503", "http://127.0.0.1:9502", "http://127.0.0.1:9503"]:
        if dev_origin not in allowed_origins:
            allowed_origins.append(dev_origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Security Headers Phase 11 ─────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)
    
    # ── Structured Logging with Correlation IDs ─────────────────────────
    from app.core.structured_logging.middleware import StructuredLoggingMiddleware
    app.add_middleware(StructuredLoggingMiddleware)
    
    # ── Rate Limiting (HIPAA Point 7) ────────────────────────────────────
    from app.core.system.security.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=10000)

    # ── Exception Handler Phase 11 & i18n ────────────────────────────────────────
    from fastapi.exceptions import RequestValidationError
    from app.core.i18n import get_locale_from_header, t

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        locale = request.headers.get("X-Locale") or get_locale_from_header(request.headers.get("Accept-Language"))
        errors = []
        for error in exc.errors():
            msg = error.get("msg", "invalid")
            # Basic map for generic pydantic errors
            if "required" in msg:
                msg = t("validation.required", locale=locale)
            elif "not a valid email" in msg:
                msg = t("validation.invalid_email", locale=locale)
            elif "not a valid number" in msg:
                msg = t("validation.positive_number", locale=locale)
            errors.append({"loc": error.get("loc"), "msg": msg, "type": error.get("type")})
        return JSONResponse(status_code=422, content={"detail": errors})

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        print(f"DEBUG GLOBAL EXCEPTION: {exc}")
        import traceback
        traceback.print_exc()
        try:
            async for db in get_db():
                monitoring = MonitoringService(db)
                req_payload = None
                try:
                    req_payload = await request.json()
                except Exception:
                    pass
                
                await monitoring.log_error(
                    error_type="api",
                    message=str(exc),
                    exc=exc,
                    user_context=getattr(request, "user", None), # Basic contextual tracking
                    request_payload=req_payload
                )
                break # Just run once
        except Exception:
            pass # Failsafe if DB logging fails
            
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    # ── Performance Monitoring Phase 11 ───────────────────────────────────
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        # Add ngrok skip browser warning header
        response.headers["ngrok-skip-browser-warning"] = "69420"
        return response

    # ── API Routers ───────────────────────────────────────────────────────
    api = "/api/v1"

    # Phase 1 – Core Platform
    from app.core.abdm.router import router as abdm_router
    app.include_router(abdm_router, prefix=api)
    
    app.include_router(auth_router, prefix=api)
    app.include_router(audit_router, prefix=api)
    app.include_router(files_router, prefix=api)
    app.include_router(notifications_router, prefix=api)
    app.include_router(config_router, prefix=api)

    # Phase 2+ – Clinical modules
    app.include_router(patients_router, prefix=api)
    app.include_router(encounters_router, prefix=api)
    app.include_router(orders_router, prefix=api)
    app.include_router(tasks_router, prefix=api)
    app.include_router(lab_router, prefix=api)
    app.include_router(pharmacy_router, prefix=api)
    app.include_router(billing_router, prefix=api)
    app.include_router(ai_router, prefix=api)
    app.include_router(analytics_router, prefix=api)
    app.include_router(nursing_triage_router, prefix=api)
    app.include_router(nursing_router, prefix=api)
    app.include_router(communication_router, prefix=api)

    # Phase 11 - Deployments & Systems
    app.include_router(public_health_router)                 # exposes /health (no auth required for monitoring)
    app.include_router(system_health_router, prefix=api)     # exposes /api/v1/system/*
    app.include_router(system_logging_router, prefix=api)    # exposes /api/v1/system/logs
    app.include_router(system_monitoring_router, prefix=api) # exposes /api/v1/system/monitoring/*

    # Phase 12 - CDSS
    app.include_router(cdss_router, prefix="/api/v1/cdss/engine", tags=["Clinical Decision Support"])

    # Phase 13 - Blood Bank
    app.include_router(blood_bank_router, prefix="/api/v1")

    # Phase 10 - Ward & Bed Management
    app.include_router(wards_router, prefix="/api/v1")

    # Phase 11 - Radiology & Imaging Management
    app.include_router(radiology_router, prefix="/api/v1")

    # Phase 14 - Operating Theatre Management
    app.include_router(ot_router, prefix="/api/v1")

    # Phase 16 - Patient Portal
    app.include_router(portal_router, prefix="/api/v1")
    app.include_router(diagnostics_router)

    # Enterprise Scheduling
    app.include_router(scheduling_router, prefix="/api/v1")

    # OPD Visit Intelligence Engine
    app.include_router(opd_visits_router, prefix="/api/v1")

    # OPD Smart Queue & Flow Orchestration Engine
    app.include_router(smart_queue_router, prefix="/api/v1")

    # OPD Nursing Clinical Triage Engine
    app.include_router(nursing_triage_router, prefix="/api/v1")

    # AI Doctor Desk & Intelligent EMR Engine
    app.include_router(doctor_desk_router, prefix="/api/v1")

    # Enterprise OPD Billing & Revenue Cycle Engine
    app.include_router(rcm_billing_router, prefix="/api/v1")
    app.include_router(multitenancy_router, prefix="/api/v1/administration")

    # Complete OPD Module — Unified Orchestrator
    from app.core.opd.routes import router as opd_complete_router
    app.include_router(opd_complete_router, prefix="/api/v1")

    # Accounting & ERP Subsystem
    app.include_router(accounting_router, prefix="/api/v1")

    # Clinical Workflow Engine (Navigator, Scribe, Guardian, Handover, Translator)
    app.include_router(clinical_workflow_router)

    # Sprint 1: Billing Masters & Configuration Engine (FRD Gaps 5-15)
    from app.core.billing_masters.routes import router as billing_masters_router
    app.include_router(billing_masters_router, prefix="/api/v1")

    # Package Management Module
    from app.core.billing.package.router import router as package_router
    app.include_router(package_router, prefix="/api/v1/billing/packages", tags=["Billing Packages"])

    # Multi-stage Billing Module
    from app.core.billing.stages.router import router as billing_stages_router
    app.include_router(billing_stages_router, prefix="/api/v1/billing/stages", tags=["Billing Stages"])

    # Variable Pricing Engine Module
    from app.core.billing.pricing.router import router as pricing_router
    app.include_router(pricing_router, prefix="/api/v1/billing/pricing", tags=["Billing Pricing"])

    # Contract Management Module
    from app.core.billing.contracts.router import router as contracts_router
    app.include_router(contracts_router, prefix="/api/v1/billing/contracts", tags=["Billing Contracts"])

    # Deposit Management Module
    from app.core.billing.deposits.router import router as deposits_router
    app.include_router(deposits_router, prefix="/api/v1/billing/deposits", tags=["Billing Deposits"])

    # Taxation Module
    from app.core.billing.tax.router import router as tax_router
    app.include_router(tax_router, prefix="/api/v1/billing/tax", tags=["Billing Tax"])

    # Credit Patient Billing Module
    from app.core.billing.credit.router import router as credit_router
    app.include_router(credit_router, prefix="/api/v1/billing/credit", tags=["Billing Credit"])

    # Sprint 2: Emergency Room (ER) Module (FRD Gap 1)
    from app.core.er.routes import router as er_router
    app.include_router(er_router, prefix="/api/v1")

    # Sprint 3: IPD Enhancements (FRD Gaps 2-4)
    from app.core.ipd.ipd_enhancements.routes import router as ipd_enhanced_router
    app.include_router(ipd_enhanced_router, prefix="/api/v1")

    # Sprint 4: Cross-Module Integration Bridge
    from app.core.integration.routes import router as integration_router
    app.include_router(integration_router, prefix="/api/v1")

    # Sprint 5: Operating Theatre (OT) Module — Enhanced
    from app.core.ot.routes import router as ot_enhanced_router
    app.include_router(ot_enhanced_router, prefix="/api/v1")

    # Hospital Intelligence & Analytics Engine
    from app.core.hospital_intelligence.routes import router as bi_router
    app.include_router(bi_router, prefix="/api/v1")

    # LIS Test Order Management Engine
    from app.core.lab.test_order_engine.routes import router as lis_order_router
    app.include_router(lis_order_router, prefix="/api/v1")

    # LIS Phlebotomy & Sample Collection Engine
    from app.core.lab.phlebotomy_engine.routes import router as phlebotomy_router
    app.include_router(phlebotomy_router, prefix="/api/v1")

    # LIS Central Receiving & Specimen Tracking Engine
    from app.core.lab.central_receiving.routes import router as cr_router
    app.include_router(cr_router, prefix="/api/v1")

    # LIS Laboratory Processing & Result Entry Engine
    from app.core.lab.processing_engine.routes import router as proc_router
    app.include_router(proc_router, prefix="/api/v1")

    # LIS Analyzer & Device Integration Engine
    from app.core.lab.analyzer_engine.routes import router as analyzer_router
    app.include_router(analyzer_router, prefix="/api/v1")

    # LIS Result Validation & Approval Engine
    from app.core.lab.result_validation_engine.routes import router as validation_router
    app.include_router(validation_router, prefix="/api/v1")

    # LIS Smart Reporting & Report Release Engine
    from app.core.lab.reporting_engine.routes import router as reporting_router
    app.include_router(reporting_router, prefix="/api/v1")

    # LIS Advanced Diagnostic Modules
    # from app.core.lab.advanced_diagnostics.routes import router as advanced_lab_router
    # app.include_router(advanced_lab_router, prefix="/api/v1")

    # LIS Extended Services & Quality Management
    from app.core.lab.extended_services.routes import router as extended_lab_router
    app.include_router(extended_lab_router, prefix="/api/v1")

    # IPD Admission & Bed Management Engine
    from app.core.ipd.routes import router as ipd_router
    app.include_router(ipd_router, prefix="/api/v1")

    # Phase 23 - Role-Based Patient Interaction Workspace
    from app.core.rpiw.routes import router as rpiw_router
    app.include_router(rpiw_router)

    # Clinical Encounter Flow - AI-Powered Interactive Consultation
    from app.core.clinical_encounter_flow.routes import router as clinical_encounter_flow_router
    app.include_router(clinical_encounter_flow_router, prefix="/api/v1")

    # Phase 24 - RPIW Patient Summary Engine
    from app.core.rpiw_summary.routes import router as rpiw_summary_router
    app.include_router(rpiw_summary_router)

    # Phase 25 - RPIW Clinical Action Engine
    from app.core.rpiw_actions.routes import router as rpiw_actions_router
    app.include_router(rpiw_actions_router)

    # Phase 26 - RPIW Role-Based AI Assistant Engine
    from app.core.rpiw_ai_assistant.routes import router as rpiw_ai_router
    app.include_router(rpiw_ai_router)

    from app.core.pharmacy.sales.routes import router as pharmacy_sales_router
    app.include_router(pharmacy_sales_router, prefix="/api/v1")

    # Virtual Avatar Interaction Layer
    from app.core.avatar.routes import router as avatar_router
    app.include_router(avatar_router, prefix="/api/v1")

    from app.core.linen.router import router as linen_router
    app.include_router(linen_router, prefix="/api/v1/linen", tags=["Linen & Laundry"])

    from app.core.cssd.router import router as cssd_router
    app.include_router(cssd_router, prefix="/api/v1/cssd", tags=["CSSD"])

    # Phase 27 - Hospital Inventory and Store Management Module
    from app.core.inventory.router import router as inventory_router
    app.include_router(inventory_router, prefix="/api/v1/inventory", tags=["Inventory & Stores"])

    # Stock Movement Analytics Module
    from app.core.inventory.movement.router import router as movement_router
    app.include_router(movement_router, prefix="/api/v1/inventory/movement", tags=["Stock Movement"])

    # Expiry Management Module
    from app.core.inventory.expiry.router import router as expiry_router
    app.include_router(expiry_router, prefix="/api/v1/inventory/expiry", tags=["Expiry Management"])

    # Stock Valuation Module
    from app.core.inventory.valuation.router import router as valuation_router
    app.include_router(valuation_router, prefix="/api/v1/inventory/valuation", tags=["Stock Valuation"])

    # Physical Stock Verification Module
    from app.core.inventory.verification.router import router as verification_router
    app.include_router(verification_router, prefix="/api/v1/inventory/verification", tags=["Stock Verification"])
    app.include_router(diagnostics_router, prefix="/api/v1/diagnostics", tags=["Diagnostic Procedures"])
    app.include_router(new_advanced_lab_router, prefix="/api/v1/advanced", tags=["Advanced Diagnostics"])
    app.include_router(procurement_router, prefix="/api/v1", tags=["Procurement & Supply Chain"])
    app.include_router(kiosk_router, prefix="/api/v1", tags=["Self-Service Kiosk"])

    # AxonHIS MD — Unified Clinical Practice + Health ATM Platform
    from app.core.axonhis_md.routes import router as axonhis_md_router
    app.include_router(axonhis_md_router, prefix="/api/v1", tags=["AxonHIS MD"])

    # MCP Integration for AI Tool Usage
    from app.core.mcp.routes import router as mcp_router
    app.include_router(mcp_router, prefix="/api/v1")

    # Health Platform Development Pack - Missing Features
    from app.core.longitudinal.routes import router as longitudinal_router
    app.include_router(longitudinal_router, prefix="/api/v1")
    
    from app.core.event_bus.routes import router as event_bus_router
    app.include_router(event_bus_router, prefix="/api/v1")
    
    from app.core.clinical_rules.routes import router as clinical_rules_router
    app.include_router(clinical_rules_router, prefix="/api/v1")
    
    from app.core.suggestion_tracker.routes import router as suggestion_tracker_router
    app.include_router(suggestion_tracker_router, prefix="/api/v1")
    
    from app.core.structured_logging.routes import router as structured_logging_router
    app.include_router(structured_logging_router, prefix="/api/v1")
    
    from app.core.device_adapter.routes import router as device_adapter_router
    app.include_router(device_adapter_router, prefix="/api/v1")
    
    from app.core.webhook_publisher.routes import router as webhook_publisher_router
    app.include_router(webhook_publisher_router, prefix="/api/v1")
    
    from app.core.config_service.routes import router as config_service_router
    app.include_router(config_service_router, prefix="/api/v1")
    
    from app.core.approval_gates.routes import router as approval_gates_router
    app.include_router(approval_gates_router, prefix="/api/v1")
    
    from app.core.prompt_mappings.routes import router as prompt_mappings_router
    app.include_router(prompt_mappings_router, prefix="/api/v1")
    
    from app.core.document_template_mappings.routes import router as document_template_mappings_router
    app.include_router(document_template_mappings_router, prefix="/api/v1")
    
    from app.core.doctor_preferences.routes import router as doctor_preferences_router
    app.include_router(doctor_preferences_router, prefix="/api/v1")

    # QA Module - Quality Assurance and Testing
    from app.core.qa.router import router as qa_router
    app.include_router(qa_router, prefix="/api/v1/qa", tags=["QA Module"])

    # Force-load AxonHIS MD models for SQLAlchemy registry
    from app.core.axonhis_md.models import (
        MdOrganization, MdFacility, MdSpecialtyProfile, MdClinician,
        MdPatient, MdPatientIdentifier, MdConsentProfile, MdChannel,
        MdAppointment, MdEncounter, MdEncounterNote, MdDiagnosis,
        MdServiceRequest, MdMedicationRequest, MdDevice, MdDeviceResult,
        MdObservation, MdDocument, MdShareGrant, MdShareAccessLog,
        MdPayer, MdCoverage, MdBillingInvoice, MdBillingLineItem,
        MdIntegrationEvent, MdAuditEvent,
    )

    # Force-load new feature models for SQLAlchemy registry
    from app.core.longitudinal.models import (
        MdLongitudinalRecordIndex, MdPatientTimeline, MdRecordSearchCache
    )
    
    from app.core.event_bus.models import (
        MdEvent, MdEventSubscription, MdEventDelivery, MdEventDeadLetter
    )
    
    from app.core.clinical_rules.models import (
        MdClinicalRule, MdRuleExecution, MdRuleAlert, MdRuleVariable
    )
    
    from app.core.suggestion_tracker.models import (
        MdSuggestion, MdSuggestionFeedback, MdSuggestionAnalytics, MdSuggestionPattern
    )
    
    
    from app.core.prompt_mappings.models import (
        MdPromptMapping, MdPromptVariable, MdPromptExecution
    )
    
    from app.core.document_template_mappings.models import (
        MdDocumentTemplateMapping
    )
    
    from app.core.doctor_preferences.models import (
        MdDoctorPreference
    )
    from app.core.device_adapter.models import (
        MdDeviceAdapter, MdDeviceData, MdAdapterCommand, MdAdapterLog
    )
    from app.core.config_service.models import (
        MdConfigItem, MdConfigHistory, MdConfigGroup, MdConfigGroupMapping
    )
    from app.core.approval_gates.models import (
        MdApprovalGate, MdApprovalRequest, MdApprovalAction
    )
    
    from app.core.webhook_publisher.models import (
        MdWebhookSubscription, MdWebhookDelivery, MdWebhookLog
    )

    # ── Health Check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "axonhis-backend", "version": "0.1.0"}

    # ── Root Route ────────────────────────────────────────────────────────────
    @app.get("/", tags=["root"])
    async def root() -> dict[str, str]:
        return {
            "message": "AXONHIS API",
            "docs": "/docs",
            "health": "/health",
            "version": "0.1.0"
        }

    return app


app = create_app()
