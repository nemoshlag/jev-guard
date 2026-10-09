"""Pattern-based detection using Microsoft Presidio's predefined recognizers.

Only the pattern recognizers are used (no spaCy model), so this stays fast,
deterministic and fully offline.
"""

from __future__ import annotations

from presidio_analyzer.predefined_recognizers import (
    CreditCardRecognizer,
    EmailRecognizer,
    IbanRecognizer,
    IpRecognizer,
    PhoneRecognizer,
    UsSsnRecognizer,
)

from jev_guard.models import Finding


class RegexDetector:
    def __init__(self, min_score: float = 0.3) -> None:
        self._min_score = min_score
        self._recognizers = [
            EmailRecognizer(),
            CreditCardRecognizer(),
            UsSsnRecognizer(),
            PhoneRecognizer(),
            IpRecognizer(),
            IbanRecognizer(),
        ]

    def detect(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        for recognizer in self._recognizers:
            for r in recognizer.analyze(text, recognizer.supported_entities, None):
                if r.score >= self._min_score:
                    findings.append(
                        Finding(
                            entity_type=r.entity_type,
                            start=r.start,
                            end=r.end,
                            score=r.score,
                            source="regex",
                        )
                    )
        return sorted(findings, key=lambda f: (f.start, -f.score))
