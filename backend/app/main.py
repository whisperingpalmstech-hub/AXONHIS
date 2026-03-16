"""
AXONHIS Backend – Application Entry Point.

All configuration, middleware, and routers are registered here.
"""
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine
from app.core.auth.router import router as auth_router
from app.core.patients.router import router as patients_router
from app.core.encounters.router import router as encounters_router
from app.core.orders.router import router as orders_router
from app.core.tasks.router import router as tasks_router
from app.core.lab.router import router as lab_router
from app.core.pharmacy.router import router as pharmacy_router
from app.core.billing.router import router as billing_router
from app.core.ai.router import router as ai_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle."""
    # Startup
    yield
    # Shutdown
    await engine.dispose()


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title="AXONHIS API",
        description="AI-First Hospital Information System",
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

    # ── Routers ───────────────────────────────────────────────────────────
    api_prefix = "/api/v1"
    app.include_router(auth_router, prefix=api_prefix)
    app.include_router(patients_router, prefix=api_prefix)
    app.include_router(encounters_router, prefix=api_prefix)
    app.include_router(orders_router, prefix=api_prefix)
    app.include_router(tasks_router, prefix=api_prefix)
    app.include_router(lab_router, prefix=api_prefix)
    app.include_router(pharmacy_router, prefix=api_prefix)
    app.include_router(billing_router, prefix=api_prefix)
    app.include_router(ai_router, prefix=api_prefix)

    @app.get("/health", tags=["health"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "axonhis-backend"}

    return app


app = create_app()
