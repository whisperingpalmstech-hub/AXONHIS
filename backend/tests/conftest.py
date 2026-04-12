"""
Shared pytest fixtures for the AXONHIS test suite (Phase 1 enhanced).
"""
import asyncio
import uuid
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.auth.models import User, UserStatus
from app.core.auth.services import hash_password, AuthService
from app.core.patients.patients.models import Patient
from app.core.encounters.encounters.models import Encounter
from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = str(settings.database_url)
if TEST_DATABASE_URL.endswith("/axonhis"):
    TEST_DATABASE_URL = TEST_DATABASE_URL[:-8] + "/axonhis_test"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncIterator[AsyncSession]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def _override_db() -> AsyncIterator[AsyncSession]:
        yield db

    app.dependency_overrides[get_db] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def doctor_user(db: AsyncSession) -> User:
    user = User(
        email="doctor@test.com",
        first_name="Dr.",
        last_name="Test",
        password_hash=hash_password("password123"),
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def nurse_user(db: AsyncSession) -> User:
    user = User(
        email="nurse@test.com",
        first_name="Nurse",
        last_name="Test",
        password_hash=hash_password("password123"),
        status=UserStatus.ACTIVE,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers(doctor_user: User, db: AsyncSession) -> dict[str, str]:
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    stmt = select(User).options(selectinload(User.user_roles)).where(User.id == doctor_user.id)
    loaded_user = (await db.execute(stmt)).scalar_one()
    service = AuthService(db)
    token = service.create_access_token(loaded_user)
    return {"Authorization": f"Bearer {token}"}

@pytest_asyncio.fixture
async def test_patient(db: AsyncSession) -> Patient:
    from datetime import date
    patient = Patient(
        patient_uuid=str(uuid.uuid4())[:8],
        first_name="Jane",
        last_name="Doe",
        date_of_birth=date(1980, 1, 1),
        gender="F",
    )
    db.add(patient)
    await db.flush()
    return patient

@pytest_asyncio.fixture
async def test_encounter(db: AsyncSession, test_patient: Patient, doctor_user: User) -> Encounter:
    import uuid
    encounter = Encounter(
        encounter_uuid=str(uuid.uuid4())[:8],
        patient_id=test_patient.id,
        encounter_type="IPD",
        doctor_id=doctor_user.id,
        department="General Medicine",
        status="scheduled"
    )
    db.add(encounter)
    await db.flush()
    return encounter
