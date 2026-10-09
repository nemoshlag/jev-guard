"""Environment-based configuration. Secrets are never given defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes"}


@dataclass(frozen=True)
class Settings:
    # Classifier endpoint. Empty = regex-only. Local: http://127.0.0.1:8009; remote: https://api.typesafe.ai
    jev_url: str = ""
    jev_model: str = "jev-latest"
    jev_api_key: str | None = None
    allow_insecure_http: bool = False
    threshold: float = 0.5
    # Key clients must send as a Bearer token to the guard API. Empty = no auth (loopback only!).
    api_key: str | None = None
    max_chars: int = 100_000

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            jev_url=os.environ.get("JEV_GUARD_JEV_URL", ""),
            jev_model=os.environ.get("JEV_GUARD_JEV_MODEL", "jev-latest"),
            jev_api_key=os.environ.get("JEV_GUARD_JEV_API_KEY") or None,
            allow_insecure_http=_bool("JEV_GUARD_ALLOW_INSECURE_HTTP"),
            threshold=float(os.environ.get("JEV_GUARD_THRESHOLD", "0.5")),
            api_key=os.environ.get("JEV_GUARD_API_KEY") or None,
            max_chars=int(os.environ.get("JEV_GUARD_MAX_CHARS", "100000")),
        )
