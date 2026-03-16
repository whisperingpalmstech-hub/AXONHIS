# AXONHIS – AI-First Hospital Information System

> Production-grade, clinician-first HIS designed for OPD, IPD, ER, Lab, Pharmacy, Billing, and Analytics.

## Quick Start

```bash
# 1. Clone and copy environment config
cp .env.example .env
# Edit .env with your secrets

# 2. Start all services
make dev

# 3. Run migrations
make migrate

# 4. Visit the app
#    Frontend:  http://localhost:3000
#    API Docs:  http://localhost:8000/docs
```

## Architecture

- **Backend**: FastAPI (Python) — modular monolith under `backend/app/core/`
- **Database**: PostgreSQL 16 via SQLAlchemy (async)
- **Cache/Queue**: Redis 7 + Celery workers
- **Frontend**: Next.js 14 (TypeScript + TailwindCSS)
- **Containerization**: Docker Compose

## Module Sequence

| Phase | Module | Status |
|-------|--------|--------|
| 1 | Core Platform (auth, events, audit) | 🔲 |
| 2 | Patient Registration | 🔲 |
| 3 | Encounter System | 🔲 |
| 4 | Order Engine | 🔲 |
| 5 | Task Engine | 🔲 |
| 6 | Doctor Consultation UI | 🔲 |
| 7 | Nursing Workflows | 🔲 |
| 8 | Laboratory System | 🔲 |
| 9 | Pharmacy System | 🔲 |
| 10 | Billing Engine | 🔲 |
| 11 | Patient Summary AI | 🔲 |
| 12 | Voice Command Processing | 🔲 |

## Developer Commands

```bash
make dev            # Start all services
make test           # Run backend tests
make lint           # Ruff + mypy
make migrate        # Apply DB migrations
make makemigration msg="description"  # Create new migration
make backend-shell  # Shell into backend container
make db-shell       # psql into database
```

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Production-ready, protected |
| `develop` | Integration branch |
| `feature/phase-1-core` | Phase 1 feature work |
| `feature/phase-N-*` | Per-phase feature branches |

PRs must pass CI (lint + test) before merging to `develop`.

## Testing

```bash
make test                    # All tests
make test-unit               # Unit tests only
make test-integration        # Integration tests only
```

## License
Private — Whispering Palms Tech Hub
