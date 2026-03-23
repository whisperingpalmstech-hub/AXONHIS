"""
AXONHIS Backend – Application Entry Point (Phase 1).

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

# Phase 1 routers
from app.core.auth.router import router as auth_router
from app.core.audit.router import router as audit_router
from app.core.files.router import router as files_router
from app.core.notifications.router import router as notifications_router
from app.core.config.router import router as config_router

# Phase 2+ routers (included for forward-compatibility)
from app.core.patients.router import router as patients_router
from app.core.encounters.router import router as encounters_router
from app.core.orders.router import router as orders_router
from app.core.tasks.router import router as tasks_router
from app.core.lab.router import router as lab_router
from app.core.pharmacy.router import router as pharmacy_router
from app.core.billing.router import router as billing_router
from app.core.ai.router import router as ai_router
from app.core.analytics.router import router as analytics_router

# Phase 11 - Production
from app.core.system.health_checks.routes import router as system_health_router
from app.core.system.logging.routes import router as system_logging_router
from app.core.system.monitoring.routes import router as system_monitoring_router
from app.core.cdss.engine.routes import router as cdss_router

# Phase 13 - Blood Bank
from app.core.blood_bank.router import router as blood_bank_router

# Phase 10 - Ward & Bed Management
from app.core.wards.router import router as wards_router

# Phase 11 - Radiology & Imaging Management
from app.core.radiology.router import router as radiology_router

# Phase 14 - Operating Theatre Management
from app.core.ot.router import router as ot_router

# Phase 15 - Hospital Communication Platform
from app.core.communication.routes import communication_router

# Phase 16 - Patient Portal & Telemedicine
from app.core.patient_portal.router import portal_router

# Enterprise Scheduling
from app.core.scheduling.routes import router as scheduling_router

# OPD Visit Intelligence Engine
from app.core.opd_visits.routes import router as opd_visits_router

# OPD Smart Queue & Flow Orchestration Engine
from app.core.smart_queue.routes import router as smart_queue_router

# OPD Nursing Clinical Triage Engine
from app.core.nursing_triage.routes import router as nursing_triage_router

# AI Doctor Desk & Intelligent EMR Engine
from app.core.doctor_desk.routes import router as doctor_desk_router

# Enterprise OPD Billing & Revenue Cycle Engine
from app.core.rcm_billing.routes import router as rcm_billing_router

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Security Headers Phase 11 ─────────────────────────────────────────
    app.add_middleware(SecurityHeadersMiddleware)

    # ── Exception Handler Phase 11 ────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        # We need an ad-hoc session since this is an exception
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
        return response

    # ── API Routers ───────────────────────────────────────────────────────
    api = "/api/v1"

    # Phase 1 – Core Platform
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
    app.include_router(communication_router, prefix=api)

    # Phase 11 - Deployments & Systems
    app.include_router(system_health_router, prefix=api)     # exposes /api/v1/system/*
    app.include_router(system_logging_router, prefix=api)    # exposes /api/v1/system/logs
    app.include_router(system_monitoring_router, prefix=api) # exposes /api/v1/system/monitoring/*

    # Phase 12 - CDSS
    app.include_router(cdss_router, prefix="/api/v1/cdss", tags=["Clinical Decision Support"])

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

    # Hospital Intelligence & Analytics Engine
    from app.core.hospital_intelligence.routes import router as bi_router
    app.include_router(bi_router, prefix="/api/v1")

    # ── Health Check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "axonhis-backend", "version": "0.1.0"}

    return app


app = create_app()
