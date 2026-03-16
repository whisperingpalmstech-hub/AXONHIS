"""Unit tests for auth module."""
import pytest
from app.core.auth.services import hash_password, verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "testpassword123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed) is True

    def test_wrong_password(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False
