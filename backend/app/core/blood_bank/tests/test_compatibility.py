"""Unit tests for blood compatibility matrix logic."""
import pytest

from app.core.blood_bank.compatibility_tests.services import CompatibilityTestService


class TestCompatibilityRules:
    """Validate the ABO/Rh compatibility matrix."""

    @pytest.mark.parametrize(
        "unit_bg, unit_rh, patient_bg, patient_rh, expected",
        [
            # O- is universal donor
            ("O", "-", "O", "-", True),
            ("O", "-", "O", "+", True),
            ("O", "-", "A", "-", True),
            ("O", "-", "A", "+", True),
            ("O", "-", "B", "-", True),
            ("O", "-", "B", "+", True),
            ("O", "-", "AB", "-", True),
            ("O", "-", "AB", "+", True),
            # O+ can donate to O+, A+, B+, AB+
            ("O", "+", "O", "+", True),
            ("O", "+", "A", "+", True),
            ("O", "+", "B", "+", True),
            ("O", "+", "AB", "+", True),
            ("O", "+", "O", "-", False),
            ("O", "+", "A", "-", False),
            # A- can donate to A-, A+, AB-, AB+
            ("A", "-", "A", "-", True),
            ("A", "-", "A", "+", True),
            ("A", "-", "AB", "-", True),
            ("A", "-", "AB", "+", True),
            ("A", "-", "O", "-", False),
            ("A", "-", "B", "+", False),
            # A+ can donate to A+, AB+
            ("A", "+", "A", "+", True),
            ("A", "+", "AB", "+", True),
            ("A", "+", "A", "-", False),
            ("A", "+", "O", "+", False),
            # B- can donate to B-, B+, AB-, AB+
            ("B", "-", "B", "-", True),
            ("B", "-", "B", "+", True),
            ("B", "-", "AB", "-", True),
            ("B", "-", "AB", "+", True),
            ("B", "-", "A", "+", False),
            # B+ can donate to B+, AB+
            ("B", "+", "B", "+", True),
            ("B", "+", "AB", "+", True),
            ("B", "+", "B", "-", False),
            # AB- can donate to AB-, AB+
            ("AB", "-", "AB", "-", True),
            ("AB", "-", "AB", "+", True),
            ("AB", "-", "A", "+", False),
            # AB+ can only donate to AB+
            ("AB", "+", "AB", "+", True),
            ("AB", "+", "AB", "-", False),
            ("AB", "+", "O", "+", False),
        ],
    )
    def test_compatibility_matrix(self, unit_bg, unit_rh, patient_bg, patient_rh, expected):
        result = CompatibilityTestService.is_compatible(unit_bg, unit_rh, patient_bg, patient_rh)
        assert result == expected, (
            f"Expected {expected} for unit {unit_bg}{unit_rh} → patient {patient_bg}{patient_rh}, got {result}"
        )

    def test_universal_donor(self):
        """O- can donate to every blood group."""
        all_recipients = [
            ("O", "-"), ("O", "+"),
            ("A", "-"), ("A", "+"),
            ("B", "-"), ("B", "+"),
            ("AB", "-"), ("AB", "+"),
        ]
        for bg, rh in all_recipients:
            assert CompatibilityTestService.is_compatible("O", "-", bg, rh) is True

    def test_universal_recipient(self):
        """AB+ can receive from every blood group."""
        all_donors = [
            ("O", "-"), ("O", "+"),
            ("A", "-"), ("A", "+"),
            ("B", "-"), ("B", "+"),
            ("AB", "-"), ("AB", "+"),
        ]
        for bg, rh in all_donors:
            assert CompatibilityTestService.is_compatible(bg, rh, "AB", "+") is True

    def test_incompatible_match_blocked(self):
        """B+ cannot donate to A-."""
        assert CompatibilityTestService.is_compatible("B", "+", "A", "-") is False
