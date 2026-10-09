"""Combines regex detection with the Jev classifier."""

from __future__ import annotations

from jev_guard.config import Settings
from jev_guard.detectors import JevClassifier, RegexDetector
from jev_guard.models import Finding, ScanResult


def redact(text: str, findings: list[Finding]) -> str:
    out: list[str] = []
    pos = 0
    for f in sorted(findings, key=lambda f: f.start):
        if f.start < pos:  # overlapping span, already covered
            pos = max(pos, f.end)
            continue
        out.append(text[pos : f.start])
        out.append(f"<{f.entity_type}>")
        pos = f.end
    out.append(text[pos:])
    return "".join(out)


class Guard:
    def __init__(
        self,
        regex: RegexDetector | None = None,
        classifier: JevClassifier | None = None,
        threshold: float = 0.5,
    ) -> None:
        self._regex = regex or RegexDetector()
        self._classifier = classifier
        self._threshold = threshold

    @classmethod
    def from_settings(cls, s: Settings) -> Guard:
        classifier = (
            JevClassifier(
                s.jev_url,
                model=s.jev_model,
                api_key=s.jev_api_key,
                allow_insecure_http=s.allow_insecure_http,
            )
            if s.jev_url
            else None
        )
        return cls(classifier=classifier, threshold=s.threshold)

    def scan(
        self, text: str, categories: tuple[str, ...] = ("pii",), redact_text: bool = False
    ) -> ScanResult:
        """Raises ClassifierError if a configured classifier fails (fail closed)."""
        findings = self._regex.detect(text)
        verdict = self._classifier.classify(text, categories) if self._classifier else None
        flagged = bool(findings) or (
            verdict is not None and any(p >= self._threshold for p in verdict.values())
        )
        return ScanResult(
            has_pii=flagged,
            findings=findings,
            classifier=verdict,
            redacted_text=redact(text, findings) if redact_text else None,
        )

    def close(self) -> None:
        if self._classifier:
            self._classifier.close()
