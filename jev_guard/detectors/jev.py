"""Client for the System One API (hosted Jev, or a local Jev-compatible server such as Kev)."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

import httpx

# Add "pci" / "phi" here later; the rest of the pipeline is category-agnostic.
CATEGORY_QUESTIONS: dict[str, str] = {
    "pii": (
        "Does the text contain personally identifiable information, such as a "
        "person's name, address, contact details, government ID, or any data that "
        "could identify a specific individual?"
    ),
}


class ClassifierError(RuntimeError):
    pass


def _is_local(host: str) -> bool:
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


class JevClassifier:
    def __init__(
        self,
        base_url: str,
        model: str = "jev-latest",
        api_key: str | None = None,
        timeout: float = 15.0,
        allow_insecure_http: bool = False,
    ) -> None:
        parsed = urlparse(base_url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            raise ValueError("base_url must be an http(s) URL")
        # Text is sent to this endpoint, so plaintext is only allowed to loopback
        # or when explicitly opted in (e.g. a private docker network).
        if parsed.scheme == "http" and not (_is_local(parsed.hostname) or allow_insecure_http):
            raise ValueError(
                "Refusing plaintext http to a non-local host; use https or set "
                "JEV_GUARD_ALLOW_INSECURE_HTTP=true for trusted private networks."
            )
        self._model = model
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            timeout=timeout,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
            follow_redirects=False,
        )

    def classify(self, text: str, categories: tuple[str, ...] = ("pii",)) -> dict[str, float]:
        unknown = [c for c in categories if c not in CATEGORY_QUESTIONS]
        if unknown:
            raise ValueError(f"Unsupported categories: {unknown}")
        payload = {
            "state": text,
            "model": self._model,
            "questions": {
                c: {"type": "noul", "instructions": CATEGORY_QUESTIONS[c]} for c in categories
            },
        }
        try:
            resp = self._client.post("/v1/systemone", json=payload)
            resp.raise_for_status()
            answers = resp.json()["answers"]
            return {c: float(answers[c]["noul"]) for c in categories}
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            # Don't chain the response: errors must not leak request content.
            raise ClassifierError(f"Classifier request failed ({type(exc).__name__})") from None

    def close(self) -> None:
        self._client.close()
