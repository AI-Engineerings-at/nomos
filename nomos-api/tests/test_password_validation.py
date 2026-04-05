"""Tests for validate_password_strength — imported from nomos_api.schemas."""

import pytest

from nomos_api.schemas import validate_password_strength


class TestPasswordValidation:
    def test_valid_password(self) -> None:
        assert validate_password_strength("SecureP@ssw0rd12!") is None

    def test_too_short(self) -> None:
        with pytest.raises(ValueError, match="12"):
            validate_password_strength("Short1!aA")

    def test_no_uppercase(self) -> None:
        with pytest.raises(ValueError, match="[Uu]ppercase"):
            validate_password_strength("alllowercase1!xx")

    def test_no_lowercase(self) -> None:
        with pytest.raises(ValueError, match="[Ll]owercase"):
            validate_password_strength("ALLUPPERCASE1!XX")

    def test_no_digit(self) -> None:
        with pytest.raises(ValueError, match="[Dd]igit"):
            validate_password_strength("NoDigitsHere!Xx")

    def test_no_special(self) -> None:
        with pytest.raises(ValueError, match="[Ss]pecial"):
            validate_password_strength("NoSpecialChar1Xx")

    def test_exactly_12_chars_valid(self) -> None:
        assert validate_password_strength("Abcdefgh1!23") is None
