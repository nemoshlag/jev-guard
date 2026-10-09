import httpx
import pytest

from jev_guard.api import create_app
from jev_guard.config import Settings
from jev_guard.detectors import ClassifierError, JevClassifier
from jev_guard.guard import Guard

TEXT = "Contact jane.doe@example.com, card 4111 1111 1111 1111."


def _classifier(handler, **kw) -> JevClassifier:
    c = JevClassifier("http://127.0.0.1:8009", **kw)
    c._client = httpx.Client(
        base_url="http://127.0.0.1:8009", transport=httpx.MockTransport(handler)
    )
    return c


def _answer(p: float):
    return lambda request: httpx.Response(
        200, json={"answers": {"pii": {"type": "noul", "noul": p}}}
    )


def test_regex_finds_and_redacts():
    r = Guard().scan(TEXT, redact_text=True)
    assert r.has_pii
    assert {f.entity_type for f in r.findings} >= {"EMAIL_ADDRESS", "CREDIT_CARD"}
    assert "example.com" not in r.redacted_text and "4111" not in r.redacted_text
    assert "jane.doe" not in r.model_dump_json().replace("redacted_text", "")


def test_clean_text():
    r = Guard().scan("The weather is nice today.")
    assert not r.has_pii and r.classifier is None


def test_classifier_flags_text_regex_misses():
    g = Guard(classifier=_classifier(_answer(0.93)))
    r = g.scan("My neighbour Alice Smith lives at the red house.")
    assert r.has_pii and not r.findings and r.classifier == {"pii": 0.93}


def test_classifier_below_threshold():
    g = Guard(classifier=_classifier(_answer(0.1)))
    assert not g.scan("Nothing here.").has_pii


def test_classifier_failure_fails_closed():
    g = Guard(classifier=_classifier(lambda request: httpx.Response(500)))
    with pytest.raises(ClassifierError):
        g.scan("hello")


def test_plaintext_remote_rejected():
    with pytest.raises(ValueError):
        JevClassifier("http://example.com")
    JevClassifier("https://api.typesafe.ai")
    JevClassifier("http://jev:8009", allow_insecure_http=True)


def test_unknown_category_rejected():
    with pytest.raises(ValueError):
        _classifier(_answer(0.5)).classify("x", ("phi",))


def test_api_auth_and_scan():
    from fastapi.testclient import TestClient

    with TestClient(create_app(Settings(api_key="s3cret", max_chars=100))) as c:
        body = {"text": TEXT, "redact": True}
        assert c.post("/v1/scan", json=body).status_code == 401
        assert (
            c.post("/v1/scan", json=body, headers={"Authorization": "Bearer nope"}).status_code
            == 401
        )
        ok = c.post("/v1/scan", json=body, headers={"Authorization": "Bearer s3cret"})
        assert ok.status_code == 200 and ok.json()["has_pii"]
        big = {"text": "a" * 101}
        assert (
            c.post("/v1/scan", json=big, headers={"Authorization": "Bearer s3cret"}).status_code
            == 413
        )
        assert c.get("/healthz").status_code == 200
