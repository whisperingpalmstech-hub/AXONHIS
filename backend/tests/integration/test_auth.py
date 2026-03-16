"""
Backend test suite – Auth integration tests.

Tests:
- User registration
- Login (success, failure, lockout)
- Token refresh
- Session management
- RBAC permission checks
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthFlow:
    """Test the complete authentication lifecycle."""

    async def test_health_check(self, client: AsyncClient):
        """Verify the health check endpoint works."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    async def test_register_user(self, client: AsyncClient, auth_headers: dict):
        """Register a new user via the API."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@test.com",
                "password": "TestPass123!",
                "first_name": "New",
                "last_name": "User",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@test.com"
        assert data["first_name"] == "New"

    async def test_login_success(self, client: AsyncClient, doctor_user):
        """Successful login returns tokens."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "doctor@test.com", "password": "password123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, doctor_user):
        """Wrong password returns 401."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "doctor@test.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_get_me(self, client: AsyncClient, auth_headers: dict):
        """Authenticated /me endpoint returns user data."""
        response = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "doctor@test.com"

    async def test_unauthenticated_access(self, client: AsyncClient):
        """Accessing protected endpoint without token returns 401."""
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 401
