"""Tests for NomOS PII Filter Engine — regex-based PII detection and masking."""

from __future__ import annotations

from nomos.core.pii_filter import PIIFilter, PIIMatch, PIIFilterResult


class TestPIIFilterEmail:
    def test_detect_email(self) -> None:
        f = PIIFilter()
        result = f.filter("Kontakt: max@example.com bitte")
        assert "[EMAIL_REDACTED]" in result.filtered_text
        assert any(m.pii_type == "email" for m in result.matches)

    def test_preserves_non_pii_content(self) -> None:
        f = PIIFilter()
        text = "Projekt NomOS v2 hat 105 Tests. Email: test@firma.at"
        result = f.filter(text)
        assert "Projekt NomOS v2 hat 105 Tests" in result.filtered_text
        assert "test@firma.at" not in result.filtered_text


class TestPIIFilterPhone:
    def test_detect_phone_austrian(self) -> None:
        f = PIIFilter()
        result = f.filter("Ruf an: +43 1 234 5678")
        assert "[PHONE_REDACTED]" in result.filtered_text

    def test_detect_phone_mobile(self) -> None:
        f = PIIFilter()
        result = f.filter("Mobil: +43 664 1234567")
        assert "[PHONE_REDACTED]" in result.filtered_text

    def test_no_false_positive_on_version_numbers(self) -> None:
        f = PIIFilter()
        result = f.filter("NomOS v2.1.0 released on 2026-03-25")
        assert result.pii_count == 0
        assert result.filtered_text == "NomOS v2.1.0 released on 2026-03-25"

    def test_no_false_positive_on_dates(self) -> None:
        f = PIIFilter()
        result = f.filter("Deadline: 25.03.2026")
        assert result.pii_count == 0


class TestPIIFilterIBAN:
    def test_detect_iban(self) -> None:
        f = PIIFilter()
        result = f.filter("IBAN: AT611904300234573201")
        assert "[IBAN_REDACTED]" in result.filtered_text


class TestPIIFilterAddress:
    def test_german_address_pattern(self) -> None:
        f = PIIFilter()
        result = f.filter("Wohnt in Musterstrasse 42, 1010 Wien")
        assert "[ADDRESS_REDACTED]" in result.filtered_text


class TestPIIFilterMultiple:
    def test_detect_multiple_pii(self) -> None:
        f = PIIFilter()
        result = f.filter("max@test.com anrufen unter +43 664 1234567")
        assert result.pii_count == 2
        assert "[EMAIL_REDACTED]" in result.filtered_text
        assert "[PHONE_REDACTED]" in result.filtered_text


class TestPIIFilterClean:
    def test_no_pii(self) -> None:
        f = PIIFilter()
        result = f.filter("Keine persoenlichen Daten hier.")
        assert result.pii_count == 0
        assert result.filtered_text == "Keine persoenlichen Daten hier."


class TestPIIFilterResult:
    def test_pii_count_property(self) -> None:
        result = PIIFilterResult(
            filtered_text="redacted",
            matches=[
                PIIMatch(pii_type="email", original="a@b.com", start=0, end=7),
            ],
        )
        assert result.pii_count == 1

    def test_empty_matches(self) -> None:
        result = PIIFilterResult(filtered_text="clean text")
        assert result.pii_count == 0
