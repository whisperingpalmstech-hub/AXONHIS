"""
Shared pytest fixtures for the AXONHIS test suite.

Provides:
- Async test DB session (uses test database)
- FastAPI test client
- Authenticated user fixtures per role
"""
import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.core.auth.models import User, UserRole
from app.core.auth.services import AuthService, _hash_password
from app.database import Base, get_db
from app.main import app


# Use a separate test database
TEST_DATABASE_URL = str(settings.database_url).replace("/axonhis", "/axonhis_test")

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Provide a single event loop for all tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db() -> AsyncIterator[AsyncSession]:
    """Provide a fresh DB session per test."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    """Provide a test HTTP client with DB override."""

    async def _override_db() -> AsyncIterator[AsyncSession]:
        yield db

    app.dependency_overrides[get_db] = _override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def doctor_user(db: AsyncSession) -> User:
    """Create a test doctor user."""
    user = User(
        email="doctor@test.com",
        full_name="Dr. Test",
        hashed_password=_hash_password("password123"),
        role=UserRole.DOCTOR,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def nurse_user(db: AsyncSession) -> User:
    """Create a test nurse user."""
    user = User(
        email="nurse@test.com",
        full_name="Nurse Test",
        hashed_password=_hash_password("password123"),
        role=UserRole.NURSE,
    )
    db.add(user)
    await db.flush()
    return user


@pytest_asyncio.fixture
async def auth_headers(doctor_user: User) -> dict[str, str]:
    """Return Authorization header for the doctor user."""
    service_stub = type("FakeDB", (), {})()
    token = AuthService(service_stub).create_access_token(doctor_user)
    return {"Authorization": f"Bearer {token}"}
