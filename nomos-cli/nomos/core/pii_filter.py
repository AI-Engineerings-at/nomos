"""NomOS PII Filter Engine — regex-based PII detection and masking.

Detects and redacts personally identifiable information (PII) in text
using regex patterns. Supports email, phone (AT/DE/CH), IBAN, address,
and tax ID patterns.

NER (spaCy) is an optional future enhancement for high-risk agents.
The regex engine is the production baseline that ships now.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class PIIMatch:
    """A single PII detection in text."""

    pii_type: str
    original: str
    start: int
    end: int


@dataclass
class PIIFilterResult:
    """Result of PII filtering: redacted text + list of matches."""

    filtered_text: str
    matches: list[PIIMatch] = field(default_factory=list)

    @property
    def pii_count(self) -> int:
        return len(self.matches)


# Phone regex is intentionally tight to avoid matching version numbers (v2.1.0)
# and dates (25.03.2026). Requires international prefix (+XX) followed by
# digit groups separated by spaces or hyphens.
_PATTERNS: list[tuple[str, re.Pattern, str]] = [
    ("email", re.compile(r"[\w.+-]+@[\w.-]+\.\w{2,}"), "[EMAIL_REDACTED]"),
    ("iban", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7,}[A-Z0-9]{0,16}\b"), "[IBAN_REDACTED]"),
    (
        "phone",
        re.compile(r"\+\d{1,3}\s\d{1,4}[\s-]\d{2,4}[\s-]?\d{2,8}"),
        "[PHONE_REDACTED]",
    ),
    (
        "address",
        re.compile(
            r"\b[A-ZÄÖÜ][a-zäöüß]+(?:strasse|gasse|weg|platz)\s+\d+[a-z]?,\s*\d{4,5}\s+[A-ZÄÖÜ][a-zäöüß]+\b"
        ),
        "[ADDRESS_REDACTED]",
    ),
    ("tax_id", re.compile(r"\b\d{2,3}/\d{3,4}/\d{4,5}\b"), "[TAX_ID_REDACTED]"),
]


class PIIFilter:
    """Regex-based PII filter for text content.

    Args:
        use_ner: Reserved for future spaCy NER integration. Currently
                 only regex patterns are used regardless of this flag.
    """

    def __init__(self, use_ner: bool = False) -> None:
        self._use_ner = use_ner

    def filter(self, text: str) -> PIIFilterResult:
        """Scan text for PII and return redacted version with match details."""
        matches: list[PIIMatch] = []
        result = text

        for pii_type, pattern, replacement in _PATTERNS:
            for match in pattern.finditer(result):
                matches.append(
                    PIIMatch(
                        pii_type=pii_type,
                        original=match.group(),
                        start=match.start(),
                        end=match.end(),
                    )
                )
            result = pattern.sub(replacement, result)

        return PIIFilterResult(filtered_text=result, matches=matches)
