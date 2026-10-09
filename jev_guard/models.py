"""Result types. Findings never carry the matched text, only offsets."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Finding(BaseModel):
    entity_type: str
    start: int
    end: int
    score: float = Field(ge=0, le=1)
    source: Literal["regex"]


class ScanResult(BaseModel):
    has_pii: bool
    findings: list[Finding] = Field(default_factory=list)
    # Classifier probability per category, e.g. {"pii": 0.93}; None if no classifier ran.
    classifier: dict[str, float] | None = None
    redacted_text: str | None = None
