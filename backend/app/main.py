"""
AXONHIS Backend – Application Entry Point (Phase 1).

All configuration, middleware, and routers are registered here.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine

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

    # ── Health Check ──────────────────────────────────────────────────────
    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "axonhis-backend", "version": "0.1.0"}

    return app


app = create_app()
