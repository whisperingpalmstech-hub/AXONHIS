"""Unit tests for auth module."""
import pytest
from app.core.auth.services import _hash_password, _verify_password


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "testpassword123"
        hashed = _hash_password(password)
        assert hashed != password
        assert _verify_password(password, hashed) is True

    def test_wrong_password(self):
        hashed = _hash_password("correct_password")
        assert _verify_password("wrong_password", hashed) is False
